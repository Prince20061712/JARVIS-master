/**
 * JARVIS Text-to-Speech
 * Uses the browser's built-in Web Speech API — no backend, zero latency.
 */

interface SpeakOptions {
    rate?: number;   // 0.1 – 10  (default 0.95 — slightly slower, more dignified)
    pitch?: number;  // 0 – 2     (default 0.85 — lower, more authoritative)
    volume?: number; // 0 – 1
    voiceHint?: "male" | "female" | "any";
}

let selectedVoice: SpeechSynthesisVoice | null = null;

/** 
 * Pick the best available voice — prefer a deep English male voice 
 * that sounds closest to JARVIS (en-GB or en-US, male).
 */
function pickVoice(hint: "male" | "female" | "any" = "male"): SpeechSynthesisVoice | null {
    if (!("speechSynthesis" in window)) return null;

    const voices = speechSynthesis.getVoices();
    if (!voices.length) return null;

    const enVoices = voices.filter(v => v.lang.startsWith("en"));

    // Prefer British English (closest to Jarvis)
    const gbMale = enVoices.find(v =>
        v.lang.includes("GB") && /daniel|male|guy|man/i.test(v.name)
    );
    if (gbMale && hint !== "female") return gbMale;

    // Fallback: any GB English
    const gb = enVoices.find(v => v.lang.includes("GB"));
    if (gb) return gb;

    // Then: named male US voices
    const usMale = enVoices.find(v => /alex|daniel|fred|thomas|bruce|male/i.test(v.name));
    if (usMale && hint !== "female") return usMale;

    // Default: first English voice
    return enVoices[0] ?? voices[0] ?? null;
}

/** 
 * Speak text aloud via the browser's speech synthesis engine.
 * Cancels any ongoing speech first so JARVIS never talks over itself.
 */
export function speak(text: string, options: SpeakOptions = {}): void {
    if (!("speechSynthesis" in window)) {
        console.warn("[JARVIS TTS] speechSynthesis not supported in this browser.");
        return;
    }

    // Stop anything already playing
    speechSynthesis.cancel();

    const utter = new SpeechSynthesisUtterance(text);

    // Strip markdown-ish artifacts before speaking
    utter.text = text
        .replace(/\*\*(.*?)\*\*/g, "$1")  // bold
        .replace(/\*(.*?)\*/g, "$1")       // italic / stage directions
        .replace(/🎭|😊|💭/g, "")          // emoji
        .replace(/\s+/g, " ")
        .trim();

    utter.rate = options.rate ?? 0.92;
    utter.pitch = options.pitch ?? 0.82;
    utter.volume = options.volume ?? 1.0;

    // Re-use cached voice or pick a new one
    if (!selectedVoice) {
        selectedVoice = pickVoice(options.voiceHint);
    }
    if (selectedVoice) utter.voice = selectedVoice;

    speechSynthesis.speak(utter);
}

/** 
 * Preload voices as soon as this module is imported.
 * Browsers may need a voiceschanged event before voices are available.
 */
if (typeof window !== "undefined" && "speechSynthesis" in window) {
    if (speechSynthesis.getVoices().length === 0) {
        speechSynthesis.addEventListener("voiceschanged", () => {
            selectedVoice = pickVoice();
        }, { once: true });
    } else {
        selectedVoice = pickVoice();
    }
}
