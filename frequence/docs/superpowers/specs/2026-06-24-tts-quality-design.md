# TTS quality: smarter native voice + Gemini toggle

## Problem

On macOS Chrome the pronunciation feature sounds terrible. The Web Speech
(`speechSynthesis`) voice list there is led by Chrome's robotic network
"Google <language>" voices (and compact system voices), while Safari gets the
good system voices. The app currently prefers *any* native voice over the
high-quality Gemini "Kore" voice, so macOS Chrome lands on the worst path.

The high-quality Gemini path already exists (`geminiTTS`, WAV wrapping,
per-word cache) — it is just deprioritised behind the native voice.

## Goals

1. Improve the native voice that gets picked (free, instant, every browser).
2. Let the user opt into the high-quality Gemini voice when they want it.

Non-goals: changing the build, data, Gemini request shape, or caching.

## Design

### 1. Smarter native voice selection — `voiceFor(bcp)`

Replace "first match wins" with a score over the language-matching voices.
Higher score wins; ties keep current list order.

- `localService === true` (on-device voice) → strong bonus. Network voices
  (`localService === false`, e.g. "Google français") → penalty.
- Name contains "enhanced" / "premium" (downloadable HQ macOS voices) → bonus.
- Name starts with "Google" → penalty (Chrome network voices).
- Exact `lang` match (`fr-FR`) → bonus over base-language match (`fr`).

Matching set is unchanged (exact `bcp47`, else `startsWith(base)`); only the
choice *within* that set changes. Returns `undefined` when nothing matches
(callers already handle that).

### 2. Voice-mode toggle — Language modal

A "Voice" row inside `openLanguageMenu()`, below the language list, near the
Reset button. Two states:

- **Auto** (default): current routing with the improved native picker.
- **High quality**: always Gemini "Kore"; falls back to native if no key.

Persisted as `localStorage["freq-tts-mode"]` (`"auto"` | `"hq"`), read by
`speak()`. Default when unset: `"auto"`.

### 3. Routing — `speak(text, btn)`

```
mode = ttsMode()
if mode === "hq" and getKey():        geminiTTS(text)      // high quality
else if TTS and voiceFor(bcp):        speakNative(text)    // improved native
else:                                  geminiTTS(text)      // no native -> Gemini (or its native fallback)
```

`geminiTTS` already falls back to `speakNative` when there is no key or the API
fails, so the no-key "hq" case degrades gracefully.

## Testing

Manual, in macOS Chrome (the failing environment):

1. Auto mode: tapping 🔊 uses an on-device voice, not "Google <lang>".
2. Switch to High quality (key set): 🔊 plays the Gemini voice; second tap on
   the same word is instant (cache).
3. High quality with no key: falls back to native, no error.
4. Mode persists across reload.
5. `make game` passes the JS syntax check.

## Scope

~25 lines in `game.template.html`. No new dependencies, no build/data changes.
