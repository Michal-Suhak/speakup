const $ = (id) => document.getElementById(id);
const views = ["start-view", "profile-view", "chat-view"];

let profiles = [];
let current = null;
let sessionId = null;

function show(view) {
  views.forEach((id) => ($(id).hidden = id !== view));
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

function errorMessage(status, detail) {
  if (status === 422 && Array.isArray(detail)) {
    const fields = detail.map((e) => e.loc.slice(1).join(".")).join(", ");
    return `Nieprawidłowe dane w polach: ${fields}.`;
  }
  if (status === 409) return "Tutor jeszcze odpowiada, poczekaj chwilę.";
  return `Błąd (${status}): ${detail}`;
}

async function api(method, path, body) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Brak połączenia z serwerem. Czy aplikacja jest uruchomiona?");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorMessage(response.status, data.detail ?? response.statusText));
  return data;
}

function slugify(name) {
  const slug = name
    .toLowerCase()
    .replace(/ł/g, "l")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 28);
  return slug || "profil";
}

function uniqueId(name) {
  const base = slugify(name);
  const taken = new Set(profiles.map((p) => p.id));
  let id = base;
  for (let n = 2; taken.has(id); n++) id = `${base}-${n}`;
  return id;
}

async function loadProfiles(selectId) {
  profiles = await api("GET", "/api/profiles");
  const select = $("profile-select");
  select.replaceChildren(
    ...profiles.map((p) => new Option(`${p.name} (${p.level})`, p.id)),
  );
  $("profile-picker").hidden = profiles.length === 0;
  if (selectId) select.value = selectId;
  await selectProfile();
}

async function selectProfile() {
  const id = $("profile-select").value;
  current = id ? await api("GET", `/api/profiles/${id}`) : null;
  $("topic-box").hidden = !current;
  if (!current) return;
  $("topics").replaceChildren(
    ...current.interests.map((topic) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = topic;
      button.onclick = () => startSession(topic);
      return button;
    }),
  );
}

function splitList(text) {
  return text.split(",").map((s) => s.trim()).filter(Boolean);
}

function openEditor() {
  const form = $("profile-form");
  form.name.value = current.name;
  form.level.value = current.level;
  form.interests.value = current.interests.join(", ");
  form.goals.value = current.goals;
  form.avoid_topics.value = current.avoid_topics.join(", ");
  form.correction_style.value = current.correction_style;
  show("profile-view");
}

async function saveProfile(event) {
  event.preventDefault();
  const form = event.target;
  const profile = {
    id: current.id,
    name: form.name.value,
    level: form.level.value,
    interests: splitList(form.interests.value),
    goals: form.goals.value,
    avoid_topics: splitList(form.avoid_topics.value),
    correction_style: form.correction_style.value,
  };
  await api("PUT", `/api/profiles/${profile.id}`, profile);
  await loadProfiles(profile.id);
  show("start-view");
}

async function createProfile(event) {
  event.preventDefault();
  const name = $("new-name").value.trim();
  const id = uniqueId(name);
  await api("PUT", `/api/profiles/${id}`, { id, name });
  $("new-name").value = "";
  await loadProfiles(id);
  openEditor();
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  $("transcript").append(div);
  div.scrollIntoView({ block: "end" });
  return div;
}

function addCorrections(message, corrections) {
  if (corrections.length === 0) return;
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = `Poprawki (${corrections.length})`;
  details.append(summary);
  for (const c of corrections) {
    const p = document.createElement("p");
    p.className = "correction";
    const wrong = document.createElement("s");
    wrong.textContent = c.you_said;
    const better = document.createElement("strong");
    better.textContent = c.better;
    const explanation = document.createElement("div");
    explanation.className = "explanation";
    explanation.textContent = c.explanation_pl;
    p.append(wrong, " → ", better, explanation);
    details.append(p);
  }
  message.append(details);
}

function setBusy(busy) {
  $("status").hidden = !busy;
  $("text-form").querySelectorAll("input, button").forEach((el) => (el.disabled = busy));
  document.querySelectorAll("#start-view button").forEach((el) => (el.disabled = busy));
}

async function startSession(topic) {
  setBusy(true);
  try {
    const data = await api("POST", "/api/session", { profile_id: current.id, topic });
    sessionId = data.session_id;
    $("chat-topic").textContent = topic;
    $("transcript").replaceChildren();
    show("chat-view");
    addMessage("tutor", data.reply);
  } finally {
    setBusy(false);
    $("text").focus();
  }
}

async function sendText(event) {
  event.preventDefault();
  const text = $("text").value.trim();
  if (!text) return;
  const message = addMessage("learner", text);
  $("text").value = "";
  setBusy(true);
  try {
    const data = await api("POST", "/api/text", { session_id: sessionId, text });
    addCorrections(message, data.corrections);
    addMessage("tutor", data.reply);
  } catch (error) {
    message.remove();
    $("text").value = text;
    throw error;
  } finally {
    setBusy(false);
    $("text").focus();
  }
}

function guarded(handler) {
  return async (event) => {
    showError("");
    try {
      await handler(event);
    } catch (error) {
      showError(error.message);
    }
  };
}

$("profile-select").onchange = guarded(selectProfile);
$("edit-profile").onclick = guarded(openEditor);
$("new-profile").onsubmit = guarded(createProfile);
$("profile-form").onsubmit = guarded(saveProfile);
$("cancel-profile").onclick = () => show("start-view");
$("start-form").onsubmit = guarded((event) => {
  event.preventDefault();
  return startSession($("topic").value.trim());
});
$("text-form").onsubmit = guarded(sendText);
$("new-session").onclick = () => {
  sessionId = null;
  show("start-view");
};

guarded(loadProfiles)();
