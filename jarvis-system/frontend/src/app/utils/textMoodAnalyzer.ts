/**
 * Text Style Mood Analyzer
 *
 * Reads typing patterns to infer the user's current mood/energy level.
 * No NLP required — pure heuristics on character + punctuation patterns.
 */

export type DetectedMood =
    | "neutral"
    | "excited"
    | "angry"
    | "confused"
    | "sad"
    | "tired"
    | "playful"
    | "shy";

export interface MoodResult {
    mood: DetectedMood;
    intensity: number;       // 0.0 – 1.0
    label: string;           // Human-readable label
    tip: string;             // JARVIS response hint
    robotEmotion: "neutral" | "shy";
}

const NEUTRAL: MoodResult = {
    mood: "neutral",
    intensity: 0.3,
    label: "Focused",
    tip: "Ready to help!",
    robotEmotion: "neutral",
};

export function analyzeTextMood(text: string): MoodResult {
    if (!text || text.trim().length === 0) return NEUTRAL;

    const t = text.trim();
    const lower = t.toLowerCase();

    // ── Signals ──────────────────────────────────
    const wordCount = t.split(/\s+/).length;
    const charCount = t.length;

    // Repeated letters: "helllooo", "yesss", "nooo"
    const repeatedChars = (t.match(/(.)\1{2,}/g) ?? []).length;

    // ALL CAPS ratio
    const upperLetters = (t.match(/[A-Z]/g) ?? []).length;
    const totalLetters = (t.match(/[a-zA-Z]/g) ?? []).length;
    const capsRatio = totalLetters > 3 ? upperLetters / totalLetters : 0;
    const isAllCaps = capsRatio > 0.7 && totalLetters > 3;

    // Exclamation marks
    const exclamCount = (t.match(/!/g) ?? []).length;

    // Question marks
    const questionCount = (t.match(/\?/g) ?? []).length;

    // Ellipsis / trailing dots
    const hasEllipsis = /\.{2,}|…/.test(t);

    // Emoji detection
    const emojiCount = (t.match(/[\p{Emoji_Presentation}]/gu) ?? []).length;

    // Keyboard smash (random/nonsense): "asdfjkl", "qwerty"
    const smashPattern = /[qwrtypsdfghjklzxcvbnm]{5,}/i;
    const isSmash = smashPattern.test(t.replace(/\s/g, ""));

    // Very short reply
    const isVeryShort = wordCount === 1 && charCount <= 3;

    // Sad keywords
    const sadKeywords = ["sad", "tired", "exhausted", "bored", "depressed", "upset", "unhappy", "disappointed"];
    const hasSadWord = sadKeywords.some(w => lower.includes(w));

    // Angry keywords
    const angryKeywords = ["angry", "frustrated", "annoyed", "hate", "stupid", "useless", "terrible", "awful"];
    const hasAngryWord = angryKeywords.some(w => lower.includes(w));

    // Praise / gratitude
    const praiseKeywords = ["good job", "great", "nice", "thank", "awesome", "amazing", "brilliant", "perfect", "well done", "good jab"];
    const hasPraise = praiseKeywords.some(w => lower.includes(w));

    // ── Decision Tree ───────────────────────────

    // 1. Angry — all caps + harsh word or exclamation
    if (isAllCaps && (hasAngryWord || exclamCount >= 2)) {
        return {
            mood: "angry",
            intensity: Math.min(0.95, 0.6 + exclamCount * 0.1),
            label: "Frustrated",
            tip: "Stay calm and break it down step by step.",
            robotEmotion: "neutral",
        };
    }

    // 2. Excited — many exclamation marks OR repeated chars
    if (exclamCount >= 2 || (repeatedChars >= 1 && exclamCount >= 1)) {
        return {
            mood: "excited",
            intensity: Math.min(0.95, 0.5 + repeatedChars * 0.1 + exclamCount * 0.1),
            label: "Enthusiastic",
            tip: "Channelling that energy into learning!",
            robotEmotion: "neutral",
        };
    }

    // 3. Repeated letters alone → playful / casual
    if (repeatedChars >= 2) {
        return {
            mood: "playful",
            intensity: 0.55,
            label: "Playful",
            tip: "Fun mode activated! What do you need?",
            robotEmotion: "shy",
        };
    }

    // 4. Confused — multiple question marks
    if (questionCount >= 2) {
        return {
            mood: "confused",
            intensity: Math.min(0.9, 0.5 + questionCount * 0.1),
            label: "Confused",
            tip: "Let me simplify this step by step for you.",
            robotEmotion: "neutral",
        };
    }

    // 5. Thoughtful / uncertain — ellipsis
    if (hasEllipsis && !exclamCount) {
        return {
            mood: "tired",
            intensity: 0.45,
            label: "Contemplative",
            tip: "Take your time. I'm here whenever you're ready.",
            robotEmotion: "neutral",
        };
    }

    // 6. Praise / very happy
    if (hasPraise) {
        return {
            mood: "shy",
            intensity: 0.65,
            label: "Kind",
            tip: "Glad I could help! Thank you! 😊",
            robotEmotion: "shy",
        };
    }

    // 7. Sad / tired keywords
    if (hasSadWord) {
        return {
            mood: "sad",
            intensity: 0.6,
            label: "Low Energy",
            tip: "I'm here. Let's take it slow — one step at a time.",
            robotEmotion: "neutral",
        };
    }

    // 8. Angry keywords without caps
    if (hasAngryWord) {
        return {
            mood: "angry",
            intensity: 0.55,
            label: "Frustrated",
            tip: "Let's identify what's causing trouble and fix it.",
            robotEmotion: "neutral",
        };
    }

    // 9. Keyboard smash = confused/stressed
    if (isSmash) {
        return {
            mood: "confused",
            intensity: 0.7,
            label: "Overwhelmed",
            tip: "It's okay — let's start with the basics.",
            robotEmotion: "neutral",
        };
    }

    // 10. Emojis = positive energy
    if (emojiCount >= 2) {
        return {
            mood: "excited",
            intensity: 0.5,
            label: "Expressive",
            tip: "Great energy! Let's dive in.",
            robotEmotion: "neutral",
        };
    }

    // 11. Very short dry replies
    if (isVeryShort) {
        return {
            mood: "tired",
            intensity: 0.4,
            label: "Brief",
            tip: "Quick question — I've got a quick answer.",
            robotEmotion: "neutral",
        };
    }

    // 12. All caps without angry word = urgent
    if (isAllCaps) {
        return {
            mood: "excited",
            intensity: 0.7,
            label: "Urgent",
            tip: "On it — let's tackle this right away.",
            robotEmotion: "neutral",
        };
    }

    return NEUTRAL;
}
