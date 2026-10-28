# SpeakUp

Lokalny tutor do ćwiczenia mówienia po angielsku. Rozmawiasz z nim głosowo, a on odpowiada, prowadzi rozmowę i poprawia ważne błędy. Wszystkie modele działają przez OpenAI API.

> Projekt jest w budowie. Aktualny etap i plan: [docs/specs/0001-mvp.md](docs/specs/0001-mvp.md).

## Wymagania

- macOS, Linux lub Windows
- [uv](https://docs.astral.sh/uv/) (sam zainstaluje odpowiednią wersję Pythona)
- klucz API OpenAI ([platform.openai.com](https://platform.openai.com/api-keys)); API jest płatne osobno od ChatGPT, warto ustawić limit wydatków na koncie

## Instalacja

1. Zainstaluj uv (macOS / Linux):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Na macOS możesz też użyć `brew install uv`.

2. W folderze projektu zainstaluj zależności:

   ```bash
   uv sync
   ```

3. Skopiuj plik z ustawieniami i wpisz swój klucz w `OPENAI_API_KEY`:

   ```bash
   cp .env.example .env
   ```

   Plik `.env` zostaje tylko u Ciebie i nie trafia do repozytorium.

## Sprawdzenie klucza

```bash
uv run python config.py
```

Jeśli wszystko działa, zobaczysz `OK: key works`. W przeciwnym razie pojawi się komunikat, co poprawić (brak klucza, zły klucz albo brak internetu).

## Uruchomienie

Aplikacja pojawi się w kolejnych etapach. Komenda startowa będzie wyglądać tak:

```bash
uv run uvicorn app:app --reload
```
