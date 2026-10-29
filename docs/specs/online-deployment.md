# Online deployment with accounts and spending limits

| Field | Value |
|---|---|
| Status | `draft` |
| Created | 2026-10-29 |
| Last updated | 2026-10-29 |
| Depends on | [0001](0001-mvp.md) |
| Supersedes | – |

## 1. Problem and context

SpeakUp only runs on the computer where it was installed. To practise, another learner (e.g. a cousin) has to clone the repo, install uv and use their own OpenAI key. Running it on the internet as it is would be unsafe: there is no login, every visitor sees and edits every profile, and anyone with the link would spend the owner's OpenAI money without a limit.

## 2. Goal

The owner sends a link and a password to a learner. The learner practises from any browser, including a phone, sees only their own profile, and cannot spend more than the limit the owner set.

## 3. Scope

**In scope:**
- Profiles, accounts and usage stored in a hosted Postgres database (Neon) instead of `profiles/*.json`.
- One account per profile: the learner logs in with the profile id and a password. Accounts are created only by the owner from the terminal.
- Per-person and total monthly spending limits, checked before every paid call.
- Admin commands run from the owner's terminal against the same database: add an account, reset a password, set a limit, show usage, import existing profile files.
- Local development and tests on Postgres in Docker (`compose.yaml`).
- Hosting on Google Cloud Run (one instance), with secrets in Secret Manager, and deployment steps in the README.

**Out of scope:**
- Admin panel in the browser (stays in the backlog).
- Self sign-up, password reset by e-mail, OAuth / "Sign in with Google".
- Saving conversations or session history (backlog: "Session history and progress"); only usage numbers are stored.
- Keeping a conversation alive across a server restart.
- CI/CD; deployment is a command run by the owner.

## 4. User scenarios

1. **Owner sets up an account.** In the terminal: `uv run python -m tutor.accounts add kasia --name Kasia --limit 3`. The command prints a generated password. The owner sends the link and the password to Kasia.
2. **Learner logs in.** Kasia opens the link and sees "Zaloguj się" with the fields id and password. She logs in, and the start screen shows only her profile ("Cześć, Kasia"), her topics, "edytuj profil" and "w tym miesiącu: 0,37 z 3 USD". The rest works as in the MVP.
3. **Wrong password.** "Nieprawidłowy login lub hasło." After 5 failures in a row for one id: "Za dużo prób. Spróbuj za 15 minut." (429), even with the right password.
4. **Limit reached.** Kasia's monthly cost reaches her limit, or the total reaches the total limit. Every paid call returns 429: "Limit wydatków został osiągnięty. Skontaktuj się z administratorem." This covers starting a session, sending a turn and the end-of-session summary. The current reply is never cut in the middle. Leaving with "nowa rozmowa" still works, because it costs nothing and records the usage.
5. **Session expired.** A cookie expires after 30 days, or the owner resets the password. The next call returns 401 and the app goes back to the login screen with "Zaloguj się ponownie."
6. **Server restarted.** Cloud Run stops an idle instance after a few minutes, or the owner deploys. The conversation in progress is lost, and the existing "Sesja wygasła…" message is shown. The usage of every turn so far is already in the database, so no cost is lost.
7. **Owner checks spending.** `uv run python -m tutor.accounts usage` prints the cost this month per person and in total, the limits and the number of sessions.
8. **Someone tries another learner's data.** A request for another profile or another learner's session returns 404, the same as a missing one, so ids cannot be probed.

## 5. Solution design

### Architecture and flow

```
learner (browser) ──HTTPS──► Cloud Run: FastAPI app (1 instance) ──┬──► OpenAI
                                                                   └──► Neon Postgres
owner (terminal: tutor.accounts) ──────────────────────────────────────► Neon Postgres
```

- `tutor/db.py` – new: `connect()` from `DATABASE_URL`, the schema (created with `CREATE TABLE IF NOT EXISTS` at startup) and small query functions. Connection per operation (a few per turn); a pool only if measured latency needs it.
- `tutor/profiles.py` – the same functions (`list/load/save_profile`) backed by the `profiles` table instead of files.
- `tutor/accounts.py` – new: password hashing (`hashlib.scrypt`, random salt), login attempts, signed cookie values (`hmac` + `SECRET_KEY`), limit checks, and the admin commands (`python -m tutor.accounts …`).
- `tutor/session.py` – the session usage is written to `session_usage` after every paid call (upsert by session id).
- `api/auth.py` – new: `/api/login`, `/api/logout`, `/api/me`, and a `current_profile` dependency used by every other router.
- `api/profiles.py`, `api/sessions.py` – every endpoint takes `current_profile`; a profile or session that is not the caller's gives 404.
- `app.py` – maps the new errors: `NotLoggedIn` 401, `TooManyAttempts` and `LimitReached` 429.
- `static/` – login screen; the start screen shows the logged-in profile only (no profile picker, no "utwórz profil"), the month cost, and "wyloguj".
- `Dockerfile`, `.dockerignore` – new: image with uv, `uv sync --frozen --no-dev`, `uvicorn app:app --host 0.0.0.0 --port $PORT`.

### Data and formats

Tables:

```sql
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,                -- same pattern as today: ^[a-z0-9-]{1,32}$
  data JSONB NOT NULL,                -- the Profile model as JSON (name, level, interests, ...)
  password_hash TEXT,                 -- "scrypt$<n>$<r>$<p>$<salt_b64>$<hash_b64>"; NULL = cannot log in
  monthly_limit_usd NUMERIC,          -- NULL = PERSON_MONTHLY_LIMIT_USD from config
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS session_usage (
  session_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES profiles(id),
  started_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  usage JSONB NOT NULL,               -- the Usage counters from 0001
  cost_usd NUMERIC NOT NULL
);
```

The profile JSON in `data` is the existing `Profile` format from 0001, unchanged:

```json
{"id": "kasia", "name": "Kasia", "level": "A2", "interests": ["Travel", "Food"], "goals": "", "avoid_topics": [], "correction_style": "gentle"}
```

`session_usage.usage` example:

```json
{"chat_input_tokens": 3182, "chat_output_tokens": 1077, "stt_input_tokens": 70, "stt_output_tokens": 21, "tts_characters": 144}
```

The month is the calendar month in UTC (`date_trunc('month', updated_at)`).

Cookie `speakup_login`: `<profile_id>.<expires_unix>.<hmac_sha256_b64>`, `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/`, 30 days. Changing a password changes a per-account value included in the signature, so old cookies stop working.

New config (`config.py` reading `.env`, names in `env.example`):

| Name | Example | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql://speakup:speakup@localhost:5432/speakup` locally, `postgresql://…neon.tech/speakup` on Cloud Run | Database used by the app. |
| `TEST_DATABASE_URL` | `postgresql://speakup:speakup@localhost:5432/speakup_test` | Database used by the tests (local Docker only). |
| `ADMIN_DATABASE_URL` | `postgresql://…neon.tech/speakup` | Database used by `tutor.accounts`; defaults to `DATABASE_URL`. Locally the app uses the Docker database while admin commands go to production Neon. |
| `SECRET_KEY` | 32+ random bytes, base64 | Signs login cookies. Startup fails without it. |
| `TOTAL_MONTHLY_LIMIT_USD` | `10` | Limit for all learners together. |
| `PERSON_MONTHLY_LIMIT_USD` | `3` | Default limit per person. |

### Endpoints

| Method | Path | Input → output |
|---|---|---|
| `POST` | `/api/login` | `{profile_id, password}` → 204 + cookie; 401 wrong id or password (same message for both); 429 too many attempts |
| `POST` | `/api/logout` | → 204, cookie cleared |
| `GET` | `/api/me` | → `{id, name, level, month_cost_usd, month_limit_usd}`; 401 when not logged in |
| `GET` | `/api/profiles` | removed: the start screen uses `/api/me` |
| `GET`/`PUT` | `/api/profiles/{id}` | as in 0001, only for the caller's own id (otherwise 404); `PUT` cannot create a profile |
| `POST` | `/api/session`, `/api/text`, `/api/turn` | as in 0001; `profile_id` in `/api/session` must be the caller's; 429 when a limit is reached |
| `POST` | `/api/session/{id}/end` | as in 0001, only the caller's sessions; 429 over the limit, except with `summary=false` (no paid call) |

Without a valid cookie, every `/api/*` endpoint except `/api/login` returns 401. Static files stay public (the page itself contains no data).

Admin commands (`uv run python -m tutor.accounts <command>`):

| Command | Does |
|---|---|
| `add <id> --name <name> [--level B1] [--limit 3]` | Create a profile with an account and print a generated password. |
| `password <id>` | Generate and print a new password; old logins stop working. |
| `limit <id> <usd>` / `limit <id> default` | Set or clear the person's monthly limit. |
| `usage [--month 2026-10]` | Table: person, cost this month, limit, sessions; total and total limit. |
| `import` | Copy `profiles/*.json` into the database (accounts without a password until `password <id>`). |

### Interface

- Login screen: "Zaloguj się", fields "Twój login" and "Hasło", button "Wejdź". Error texts from scenarios 3 and 5. All texts in the `TEXT` object or `index.html`.
- Start screen: "Cześć, <name>", the topics, "edytuj profil", "w tym miesiącu: 0,37 z 3 USD", "wyloguj".
- Summary screen: the line from 0001 plus "w tym miesiącu: … z … USD".
- Limit reached: the message from scenario 4. The mic, the text field and "zakończ sesję" are disabled until the next month; "nowa rozmowa" and "wyloguj" still work.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|
| Hosting | Google Cloud Run, `--max-instances=1`, scale to zero, region `europe-central2` | Cloudflare quick tunnel from the owner's computer; small VPS (a few EUR per month); Render free tier; Hugging Face Spaces; Vercel | Free at this traffic, works when the owner's computer is off (a quick tunnel gives an HTTPS link only while the app runs locally, with a new address each time), HTTPS included, wakes in seconds. Downsides: Google needs a billing account with a card even within the free tier, and the free tier can change. Render sleeps after 15 min and wakes in about a minute. HF Spaces has no persistent disk and its free terms need checking. On Vercel every request can run in a different serverless instance, so the in-memory sessions and their lock would break; sessions would first have to move to the database. A VPS needs no code change but costs money and needs updates. One instance, because sessions live in memory. |
| Database | Neon Postgres, region close to `europe-central2` | Supabase (pauses after a week idle); Turso/libSQL (unclear inactivity rules); SQLite on the server (lost on Cloud Run restarts) | Free tier that scales to zero and wakes in milliseconds; works from Cloud Run and from the owner's terminal. Free projects idle for 90 days may be deleted: acceptable with regular use. |
| Where accounts live | In the `profiles` table, one account per profile | Shared login and password in `.env` (HTTP Basic) | Each learner sees only their own data and has their own limit; passwords change without a redeploy. |
| Passwords | `hashlib.scrypt` with a random salt, compared with `hmac.compare_digest` | bcrypt/argon2 packages | Standard library, no new dependency, a memory-hard hash. |
| Login state | Signed cookie (`hmac` + `SECRET_KEY`), 30 days | Server-side login table; Starlette `SessionMiddleware` (needs `itsdangerous`) | No extra table or dependency; `SameSite=Strict` blocks cross-site requests. |
| Brute force | 5 failures per id → 15 min lock, in memory | Lock stored in the database | One instance; a restart resets the counter, which is acceptable for two users. |
| Usage storage | Upsert per session after every paid call | Write only at the end of the session | Limits apply during a session, and no cost is lost on restarts or abandoned sessions. |
| Limit check | Before every paid call, including the end-of-session summary; the call that crosses the limit finishes | Stop in the middle; estimate the next call's cost; allow the summary over the limit | A reply is never cut; the overshoot is at most one turn (about 0.002 USD). The limit is a hard stop for everything that costs money. |
| Postgres driver | `psycopg[binary]` (approved) | `asyncpg`; an ORM (SQLAlchemy) | Synchronous like the rest of the code, plain SQL for two tables, no ORM to learn. |
| Local development and tests | Postgres 17 in Docker (`compose.yaml` with one `db` service). The app uses the `speakup` database and tests use `speakup_test`, which is recreated by a fixture. No file mode is kept | Neon test branch (needs internet); keeping `profiles/*.json` for local runs | One storage backend in all places; tests run offline and never touch production. Local runs need Docker, which the README explains. |
| Admin tools | Terminal commands against the database | Admin panel in the browser | Nothing admin-related exposed on the internet; panel stays in the backlog. |
| Deployment | `gcloud run deploy --source .` from the owner's computer | GitHub Actions | One command for one owner; CI only when there are more people. |

## 7. Cost, latency, privacy

- **OpenAI:** no new calls; limits cap the monthly cost.
- **Hosting:** Cloud Run and Neon free tiers cover two learners. Google needs a billing account with a card; a budget alert (e.g. 1 USD) is part of the setup. Builds use Cloud Build's free minutes.
- **Latency:**
  - first request after idle: a cold start of a few seconds, plus Neon waking up (milliseconds);
  - each turn: one or two database writes, tens of milliseconds each (connection per operation).
- **Stored data:**
  - In Neon (EU region): profiles (name, level, interests, goals, topics to avoid), password hashes, per-session usage counts and cost, kept until the owner deletes them.
  - Conversations and recordings are still not stored.
  - The data now leaves the owner's computer: the owner tells learners what is stored.
- **Logs** (Cloud Run Logging): the existing step timings and `Session <id> ended` lines, plus `Login failed for <id>` and `Limit reached for <id>`. Never passwords, cookies, `DATABASE_URL`, profile field values or transcripts.
- **Error responses:** our own short messages (scenarios above); database errors become 503 "Database unavailable (OperationalError). Try again in a moment." without the driver's message.

## 8. Risks and open questions

- [x] New dependency `psycopg[binary]`: approved.
- [x] Database for tests: local Postgres in Docker.
- [x] Local runs without a database: not kept; local runs use Postgres in Docker.
- [x] Google billing account with a card: accepted, recorded as a downside of Cloud Run.
- [x] Summary over the limit: not allowed; only "nowa rozmowa" (no paid call) works.
- [x] Limit message: "Limit wydatków został osiągnięty. Skontaktuj się z administratorem."
- [x] Free plan terms: re-checked on the providers' pages as the first step of stage 4.

Remaining risks:
- Free tiers of Neon and Cloud Run can change; the budget alert and the in-app limits cap the damage.
- Neon may delete a free project idle for 90 days; an export with `pg_dump` before long breaks avoids losing profiles.

## 9. Implementation plan

One PR per stage; each leaves `main` working.

**Stage 1 – Database**
- [ ] `compose.yaml` with Postgres 17 (`speakup` and `speakup_test` databases), `psycopg` dependency, `DATABASE_URL`, `tutor/db.py` with the schema
- [ ] Test fixture that recreates the schema in `speakup_test`; existing profile tests run on it
- [ ] `tutor/profiles.py` on the `profiles` table, same functions and errors
- [ ] `tutor.accounts import` for existing `profiles/*.json`
- [ ] README: installing Docker, `docker compose up -d`, then the usual `uv run` steps

**Stage 2 – Accounts and login**
- [ ] Password hashing, `add` and `password` commands
- [ ] `/api/login`, `/api/logout`, `/api/me`, `current_profile` on every router, 404 for other learners' data, login attempt lock
- [ ] Login screen, start screen for the logged-in profile, "wyloguj", 401 → login screen

**Stage 3 – Usage and limits**
- [ ] `session_usage` upsert after every paid call
- [ ] Limit checks (per person and total) with 429, `limit` and `usage` commands
- [ ] "w tym miesiącu" on the start and summary screens, the limit message

**Stage 4 – Hosting**
- [ ] Re-check the Neon and Cloud Run free plan terms on the providers' pages; update this spec if they changed
- [ ] Neon project for production, README: creating it and setting `DATABASE_URL` / `ADMIN_DATABASE_URL`
- [ ] `Dockerfile`, `.dockerignore`, `SECRET_KEY` check at startup
- [ ] Cloud Run deployment with Secret Manager, one instance, budget alert
- [ ] README: "Deployment" section, sharing the link, checking usage

## 10. Acceptance criteria

- [ ] A learner logs in with an id and password created by `tutor.accounts add` and practises on the Cloud Run URL from a computer and a phone.
- [ ] Without logging in, every `/api/*` endpoint except `/api/login` returns 401.
- [ ] A logged-in learner gets 404 for another learner's profile and session.
- [ ] After 5 wrong passwords, the right one is refused for 15 minutes.
- [ ] After `tutor.accounts password <id>`, the old cookie returns 401.
- [ ] When the person's or the total monthly limit is reached, starting a session, sending a turn and ending with a summary return 429 with the limit message; leaving with "nowa rozmowa" (`summary=false`) still works.
- [ ] `tutor.accounts usage` run on the owner's computer shows the same costs as the summaries on the hosted app.
- [ ] After a server restart, the usage of turns before the restart is still in `usage`.
- [ ] No log line or error response contains a password, cookie, `DATABASE_URL`, profile field value or transcript.
- [ ] Profiles survive a redeploy.

## 11. Tests and evaluation

- Unit tests with `TestClient`:
  - login, logout, wrong password, the lock;
  - cookie signature, expiry and password change;
  - 401 and 404 on every endpoint;
  - limit checks around the boundary;
  - usage upserts;
  - the admin commands with fixed inputs.
- Tests run against `speakup_test` in the local Docker Postgres (`TEST_DATABASE_URL`), recreated for each run; they never touch production.
- Manual: deploy, log in as two learners on two devices, check isolation, reach a low test limit (e.g. 0.01 USD), restart the service and run `usage`.
- No tutor prompts change, so `tutor-eval` is not needed.

## Changelog

| Date | Change |
|---|---|
| 2026-10-29 | Document created. |
| 2026-10-29 | Open questions resolved: `psycopg` approved, Postgres in Docker for local runs and tests (no file mode), card for Google accepted as a downside, no summary over the limit, limit message wording, free plan terms re-checked in stage 4. |
| 2026-10-29 | Parked as an unnumbered draft; it gets the next number when accepted. |
