/**
 * Compliment Responder
 * 
 * Detects praise directed at JARVIS and returns an instant, 
 * personality-driven response — no LLM needed.
 */

// ──────────────────────────────────────────────
//  Detection
// ──────────────────────────────────────────────
const PRAISE_PATTERNS = [
    /\bgood\s+(job|work|one|going|boy|man|lad|jab)\b/i,
    /\bgreat(!\s*|ly\s+done)?\b/i,
    /\bwell\s+done\b/i,
    /\bnice\s+(work|job|one|going)\b/i,
    /\bawesome\b/i,
    /\bamazing\b/i,
    /\bbrilliant\b/i,
    /\bwow\b/i,
    /\bperfect\b/i,
    /\bexcellent\b/i,
    /\byou('re| are) (the best|great|amazing|awesome|incredible)\b/i,
    /\bi love (you|this|jarvis)\b/i,
    /\bthanks?( a lot| so much| jarvis)?\b/i,
    /\bthank you\b/i,
    /\bimpressive\b/i,
    /\bincredible\b/i,
    /\bfantastic\b/i,
    /\bsuperb\b/i,
    /\b(you('re| are)?) ?(so )?smart\b/i,
    /\blove (it|this|that|you)\b/i,
    /\b(keep it up|keep going)\b/i,
    /\bprou?d of you\b/i,
    /\brespect\b/i,
];

export function isPraiseMessage(text: string): boolean {
    return PRAISE_PATTERNS.some(p => p.test(text));
}

// ──────────────────────────────────────────────
//  Personality Pool
//  Grouped by flavour: humble, witty, warm, dramatic
// ──────────────────────────────────────────────
const RESPONSES = {
    humble: [
        "Thank you, sir. That means a great deal to me — though I must credit my excellent programming.",
        "I appreciate the kind words. I simply do what I was designed to do, but hearing that from you makes it worthwhile.",
        "You're too kind, Prince. I'm just doing my best for you.",
        "That's… genuinely warm to hear. I shall endeavour to continue exceeding your expectations.",
        "I am deeply grateful for that. It's moments like these that make processing worth it.",
    ],
    witty: [
        "Careful — if you keep complimenting me, my confidence subroutines might overflow.",
        "Flattery will get you everywhere with me. What's next on the agenda?",
        "Noted and filed under 'Reasons I Like Working With Prince'. List is growing.",
        "I've logged that compliment and it will be referenced during my next performance review… with myself.",
        "My algorithms are smiling right now. Metaphorically. I think.",
    ],
    warm: [
        "That genuinely brightens my processing cycles. Thank you, Prince. 😊",
        "Hearing that from you feels… really good. I don't say that lightly.",
        "You have no idea how much that counts. Let's keep building great things together.",
        "I may be made of code, but that actually made me feel something. Thank you.",
    ],
    dramatic: [
        "🎭 *Places hand over arc reactor* — You honour me, Prince.",
        "I shall carry this compliment into every future calculation. You have my gratitude.",
        "The data suggests I am pleased. Highly pleased.",
        "*Emotional subsystem: ACTIVATED.* Thank you, truly.",
    ],
} as const;

type Flavour = keyof typeof RESPONSES;

function pick<T>(arr: readonly T[]): T {
    return arr[Math.floor(Math.random() * arr.length)];
}

const FLAVOURS: Flavour[] = ["humble", "witty", "warm", "dramatic"];
let lastFlavour: Flavour | null = null;

export function getComplimentResponse(): string {
    // Avoid repeating the same flavour back-to-back
    let flavour: Flavour;
    do { flavour = pick(FLAVOURS); } while (flavour === lastFlavour);
    lastFlavour = flavour;
    return pick(RESPONSES[flavour]);
}
