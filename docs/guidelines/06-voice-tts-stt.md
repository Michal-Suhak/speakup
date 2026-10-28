# 06. Voice: TTS and STT

Voice is the agent's perception system (ears and mouth). It doesn't make the agent smarter, but for practising speaking it is essential.

## Minimum glossary

- **STT / ASR**: speech → text. **TTS**: text → speech.
- **VAD** (Voice Activity Detection): when the learner stopped speaking. A bad VAD makes the bot interrupt or stay silent too long.
- **Sample rate**: 16 kHz is enough for speech (STT models convert to it anyway). For playback, e.g. MP3 44.1 kHz/128 kbps is enough.
- **Streaming**: audio arrives in chunks, so playback starts before the whole utterance is ready.
- **Prosody**: intonation, tempo, stress, mood. Timbre is something else.

## Providers

- Put the voice layer behind **one interface** (`speak(text, voice) -> bytes`, `transcribe(audio) -> str`), so providers can be swapped without touching the agent.
- Options: **OpenAI** TTS/STT (one provider and one key) or **ElevenLabs** (TTS + STT, thousands of voices, emotion tags). Choose by listening tests on your own sentences.
- For learning English pick a **native voice with a clear accent** (US/UK) and let the learner change it. The accent is part of the goal (e.g. "Business English US").
- Keep `voice_id` and `model_id` in config or the learner profile, not in code.

## Latency

Every stage (STT → LLM → TTS) adds delay. 2 seconds of silence is awkward, 5 seconds means hanging up.

- For conversation pick a low-latency TTS model (e.g. "flash/turbo" variants), and a higher-quality model for reference recordings.
- Stream TTS and start speaking from the first sentence of the reply.
- Process audio in memory (`b"".join(stream)`), don't write a file to disk on every turn. Add saving only where needed (e.g. learner recordings for pronunciation feedback).
- Quality and correct logic first, millisecond optimisation second.

## Voice control

- **Parameters** (ElevenLabs `voice_settings`): high `stability` (0.8–1.0) gives a clean, newsreader, boring voice; low (0.3–0.5) emotional and risky. `style` amplifies expression. Start from presets (`narrator`, `conversational`, `emotional`) and tune per voice.
- **Directing through text** (v3 models): tags in the text, e.g. `[laughs]`, `[whispers]`, `[sighs]`, `[excited]`. Tags always in English. Easiest when the LLM generates them itself, so add a schema field or an instruction in the template.
- **Punctuation**: `...` gives a pause, CAPITALS give emphasis.
- **Two fields in the schema**: `ai_answer` (for display, no tags) and `speech_text` (with tags and pauses, for TTS). The learner shouldn't read `[sighs]` in the chat.

## Tutor specifics

- **Pace**: for lower levels (A2–B1) slower speech and shorter sentences. Control it through the learner profile in the template.
- **Transcript as teaching data**: STT text is the input to mistake analysis. STT may "fix" the learner's grammar errors, so test whether the transcript keeps what was actually said.
- **Real-life listening**: in conversation practice the agent speaks naturally ("gonna", "How's it going?"), and slows down or repeats when the learner asks.
- **Ethics**: clone a specific person's voice only with their consent.
