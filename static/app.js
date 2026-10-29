const $ = (id) => document.getElementById(id);

const TEXT = {
  invalidFields: (fields) => `Nieprawidłowe dane w polach: ${fields}.`,
  tutorBusy: "Tutor jeszcze odpowiada, poczekaj chwilę.",
  sessionExpired: "Sesja wygasła (serwer był restartowany). Kliknij „nowa rozmowa”.",
  httpError: (status, detail) => `Błąd (${status}): ${detail}`,
  noConnection: "Brak połączenia z serwerem. Czy aplikacja jest uruchomiona?",
  noFreeId: "Nie udało się nadać id profilu, wpisz inne imię.",
  tutorName: "Tutor",
  corrections: (count) => `poprawki: ${count}`,
  micIdle: "przytrzymaj i mów",
  micRecording: "nagrywam… puść, aby wysłać",
  tooShort: "Nagranie było za krótkie. Przytrzymaj przycisk przez cały czas, kiedy mówisz.",
  noSpeech: "Nie usłyszałem, spróbuj jeszcze raz.",
  recordingTooLong: "Nagranie jest za długie, mów krótszymi fragmentami.",
  micDenied: "Brak dostępu do mikrofonu. Zezwól na niego w ustawieniach przeglądarki albo pisz w polu poniżej.",
  noMic: "Nie znaleziono mikrofonu. Możesz pisać w polu poniżej.",
  noRecorder: "Ta przeglądarka nie nagrywa dźwięku. Możesz pisać w polu poniżej.",
  thinking: "tutor zastanawia się…",
  speaking: "tutor mówi…",
  playFailed: "Nie udało się odtworzyć głosu tutora. Kliknij „powtórz”.",
};
const MIN_RECORDING_MS = 500;
const MAX_RECORDING_MS = 60_000;
const views = ["start-view", "profile-view", "chat-view"];
const player = new Audio();

let profiles = [];
let current = null;
let sessionId = null;
let busy = false;
let speaking = false;
let stream = null;
let recorder = null;
let wantRecording = false;

function show(view) {
  views.forEach((id) => ($(id).hidden = id !== view));
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

function errorMessage(path, status, detail) {
  if (status === 422 && Array.isArray(detail)) {
    const fields = detail.map((e) => e.loc.slice(1).join(".")).join(", ");
    return TEXT.invalidFields(fields);
  }
  if (status === 409) return TEXT.tutorBusy;
  if (status === 404 && (path === "/api/text" || path === "/api/turn")) return TEXT.sessionExpired;
  if (status === 400 && path === "/api/turn") return TEXT.noSpeech;
  if (status === 413) return TEXT.recordingTooLong;
  return TEXT.httpError(status, detail);
}

async function api(method, path, body) {
  let response;
  try {
    const json = body && !(body instanceof FormData);
    response = await fetch(path, {
      method,
      headers: json ? { "Content-Type": "application/json" } : {},
      body: json ? JSON.stringify(body) : body,
    });
  } catch {
    throw new Error(TEXT.noConnection);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(errorMessage(path, response.status, data.detail ?? response.statusText));
    error.status = response.status;
    throw error;
  }
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

async function freeId(name) {
  const base = slugify(name);
  for (let n = 1; n <= 100; n++) {
    const id = n === 1 ? base : `${base}-${n}`;
    try {
      await api("GET", `/api/profiles/${id}`);
    } catch (error) {
      // 400 means a broken file with this id: keep it and pick another id
      if (error.status === 404) return id;
      if (error.status !== 400) throw error;
    }
  }
  throw new Error(TEXT.noFreeId);
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
  const id = await freeId(name);
  await api("PUT", `/api/profiles/${id}`, { id, name });
  $("new-name").value = "";
  await loadProfiles(id);
  openEditor();
}

function addMessage(role, text) {
  const line = document.createElement("div");
  line.className = `line ${role}`;
  const who = document.createElement("span");
  who.className = "who";
  who.textContent = role === "tutor" ? TEXT.tutorName : current.name;
  const said = document.createElement("div");
  said.className = "said";
  said.textContent = text;
  line.append(who, said);
  $("transcript").append(line);
  line.scrollIntoView({ block: "end" });
  return said;
}

function addCorrections(message, corrections) {
  if (corrections.length === 0) return;
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = TEXT.corrections(corrections.length);
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

function setBusy(value) {
  busy = value;
  $("status").hidden = !busy && !speaking;
  $("status").textContent = busy ? TEXT.thinking : TEXT.speaking;
  $("mic").disabled = busy || speaking;
  $("repeat").disabled = busy || speaking;
  $("text-form").querySelectorAll("input, button").forEach((el) => (el.disabled = busy));
  document.querySelectorAll("#start-view button").forEach((el) => (el.disabled = busy));
}

function setSpeaking(value) {
  speaking = value;
  setBusy(busy);
}

async function playReply() {
  player.currentTime = 0;
  setSpeaking(true);
  try {
    await player.play();
  } catch (error) {
    // a newer reply or "nowa rozmowa" interrupted this one and owns the state now
    if (error.name === "AbortError") return;
    setSpeaking(false);
    showError(TEXT.playFailed);
  }
}

function speak(audio) {
  if ($("chat-view").hidden) return;
  stopSpeaking();
  if (audio) player.src = `data:audio/mpeg;base64,${audio}`;
  else player.removeAttribute("src");
  $("repeat").hidden = !audio;
  if (audio) playReply();
}

function stopSpeaking() {
  player.pause();
  setSpeaking(false);
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
    speak(data.audio);
  } finally {
    setBusy(false);
    $("mic").focus();
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
    speak(data.audio);
  } catch (error) {
    message.parentElement.remove();
    $("text").value = text;
    throw error;
  } finally {
    setBusy(false);
    $("text").focus();
  }
}

function setRecording(recording) {
  $("mic").classList.toggle("recording", recording);
  $("mic-label").textContent = recording ? TEXT.micRecording : TEXT.micIdle;
}

async function startRecording() {
  if (recorder || busy || speaking || wantRecording) return;
  wantRecording = true;
  if (!window.MediaRecorder) throw new Error(TEXT.noRecorder);
  try {
    stream ??= await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    wantRecording = false;
    throw new Error(error.name === "NotFoundError" ? TEXT.noMic : TEXT.micDenied);
  }
  // the button may be released while the browser asks for microphone permission
  if (!wantRecording) return;
  const type = ["audio/webm", "audio/mp4"].find((t) => MediaRecorder.isTypeSupported(t));
  const chunks = [];
  const started = Date.now();
  recorder = new MediaRecorder(stream, type ? { mimeType: type } : undefined);
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onstop = guarded(() => sendRecording(chunks, recorder.mimeType, Date.now() - started));
  recorder.start();
  recorder.timer = setTimeout(stopRecording, MAX_RECORDING_MS);
  setRecording(true);
}

function stopRecording() {
  wantRecording = false;
  if (!recorder) return;
  clearTimeout(recorder.timer);
  recorder.stop();
  setRecording(false);
}

async function sendRecording(chunks, mimeType, duration) {
  recorder = null;
  if (duration < MIN_RECORDING_MS) throw new Error(TEXT.tooShort);
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("audio", new Blob(chunks, { type: mimeType }), `turn.${mimeType.includes("mp4") ? "mp4" : "webm"}`);
  setBusy(true);
  try {
    const data = await api("POST", "/api/turn", form);
    addCorrections(addMessage("learner", data.user_text), data.corrections);
    addMessage("tutor", data.reply);
    speak(data.audio);
  } finally {
    setBusy(false);
  }
}

function releaseMicrophone() {
  if (recorder) recorder.onstop = () => (recorder = null);
  stopRecording();
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
}

function isTyping(event) {
  return event.target.matches("input, textarea, select");
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
  releaseMicrophone();
  stopSpeaking();
  sessionId = null;
  show("start-view");
};
$("repeat").onclick = guarded(playReply);
player.onended = () => setSpeaking(false);
player.onerror = () => setSpeaking(false);
$("mic").onpointerdown = guarded(startRecording);
["pointerup", "pointerleave", "pointercancel"].forEach((name) => $("mic").addEventListener(name, stopRecording));
document.addEventListener("keydown", (event) => {
  if (event.code !== "Space" || $("chat-view").hidden || isTyping(event)) return;
  event.preventDefault();
  if (!event.repeat) guarded(startRecording)();
});
document.addEventListener("keyup", (event) => {
  if (event.code !== "Space" || isTyping(event)) return;
  event.preventDefault();
  stopRecording();
});
window.addEventListener("blur", stopRecording);
setRecording(false);

guarded(loadProfiles)();
