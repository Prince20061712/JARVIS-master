import { motion, AnimatePresence } from "motion/react";
import { useEffect, useState } from "react";
import { RobotState } from "./Robot";

interface RobotFaceProps {
    state: RobotState;
    emotion?: "neutral" | "shy";
    mouseOffset?: { x: number; y: number };
}

/* ──────────────── Palette ──────────────── */
const PALETTE: Record<string, { primary: string; dim: string }> = {
    idle: { primary: "rgba(140,210,255,0.7)", dim: "rgba(140,210,255,0.15)" },
    speaking: { primary: "rgba(100,255,200,0.75)", dim: "rgba(100,255,200,0.12)" },
    processing: { primary: "rgba(180,140,255,0.7)", dim: "rgba(180,140,255,0.12)" },
    listening: { primary: "rgba(220,200,120,0.75)", dim: "rgba(220,200,120,0.12)" },
    error: { primary: "rgba(255,90,90,0.8)", dim: "rgba(255,90,90,0.15)" },
    scanning: { primary: "rgba(140,210,255,0.7)", dim: "rgba(140,210,255,0.12)" },
    loading: { primary: "rgba(180,140,255,0.7)", dim: "rgba(180,140,255,0.12)" },
    analyzing: { primary: "rgba(180,140,255,0.7)", dim: "rgba(180,140,255,0.12)" },
    rebooting: { primary: "rgba(255,160,80,0.75)", dim: "rgba(255,160,80,0.12)" },
    dancing: { primary: "rgba(220,130,255,0.75)", dim: "rgba(220,130,255,0.12)" },
};

/* ──────────────── Aperture Eye ──────────────── 
   Looks like a camera iris / visor slit — thin horizontal bar that
   opens/closes rather than a chunky cartoon rectangle.           */
function ApertureEye({
    cx, primary, dim, state,
}: {
    cx: number; primary: string; dim: string; state: RobotState;
}) {
    const [blink, setBlink] = useState(false);

    useEffect(() => {
        if (state !== "idle" && state !== "scanning") return;
        const schedule = (): ReturnType<typeof setTimeout> => {
            const delay = 3000 + Math.random() * 4000;
            return setTimeout(() => {
                setBlink(true);
                setTimeout(() => { setBlink(false); schedule(); }, 90);
            }, delay);
        };
        const t = schedule();
        return () => clearTimeout(t);
    }, [state]);

    const openH = state === "error" ? 3 : 10;
    const height = blink ? 0.5 : openH;

    return (
        <g>
            {/* dim fill — the "iris" background */}
            <motion.rect
                x={cx - 18} y={22} width={36} height={12}
                rx={6}
                fill={dim}
                animate={{ opacity: state === "processing" ? [0.5, 1, 0.5] : 0.8 }}
                transition={{ duration: 1, repeat: Infinity, repeatType: "mirror" }}
            />
            {/* bright slit */}
            <motion.rect
                x={cx - 16}
                width={32}
                rx={3}
                fill={primary}
                animate={{
                    height,
                    y: 22 + (12 - height) / 2,
                    opacity: state === "processing" ? [0.6, 1, 0.6] : state === "error" ? [1, 0.3, 1] : 0.95,
                }}
                transition={{
                    duration: blink ? 0.06 : state === "processing" ? 0.7 : 0.15,
                    repeat: state === "processing" || state === "error" ? Infinity : 0,
                    repeatType: "mirror",
                }}
                style={{ filter: `drop-shadow(0 0 4px ${primary})` }}
            />
            {/* subtle corner ticks — gives a HUD / targeting feel */}
            {[cx - 18, cx + 18 - 4].map((x, i) => (
                <rect key={i} x={x} y={20} width={4} height={1.5} rx={0.5}
                    fill={primary} opacity={0.5} />
            ))}
        </g>
    );
}

/* ──────────────── Frequency Display (mouth) ──────────────── 
   Thin vertical columns like an EQ analyser — refined, not cartoony */
function FrequencyBar({
    primary, dim, state,
}: {
    primary: string; dim: string; state: RobotState;
}) {
    const NUM = 11;
    const BAR_W = 4;
    const GAP = 4;
    const TOTAL = NUM * (BAR_W + GAP) - GAP;    // 74px
    const startX = (104 - TOTAL) / 2;
    const maxH = 10;
    const baseH = [3, 5, 4, 7, 6, 8, 5, 7, 4, 5, 3];

    if (state === "idle" || state === "rebooting" || state === "loading") {
        /* Flat single line */
        return (
            <motion.line
                x1={startX} y1={54} x2={startX + TOTAL} y2={54}
                stroke={primary} strokeWidth={1} strokeLinecap="round" opacity={0.45}
                animate={{ opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 3, repeat: Infinity }}
            />
        );
    }

    if (state === "processing" || state === "analyzing" || state === "scanning") {
        /* Dashed sliding line */
        return (
            <motion.line
                x1={startX} y1={54} x2={startX + TOTAL} y2={54}
                stroke={primary} strokeWidth={1.5} strokeLinecap="round"
                strokeDasharray="6 4"
                animate={{ strokeDashoffset: [0, -20] }}
                transition={{ duration: 0.5, repeat: Infinity, ease: "linear" }}
                style={{ filter: `drop-shadow(0 0 3px ${primary})` }}
            />
        );
    }

    if (state === "error") {
        return (
            <motion.path
                d={`M${startX} 56 Q${startX + TOTAL / 2} 50 ${startX + TOTAL} 56`}
                fill="none" stroke={primary} strokeWidth={1.5} strokeLinecap="round"
                animate={{ opacity: [0.9, 0.3, 0.9] }}
                transition={{ duration: 0.45, repeat: Infinity }}
                style={{ filter: `drop-shadow(0 0 4px ${primary})` }}
            />
        );
    }

    /* speaking / listening — animated columns */
    return (
        <g>
            {baseH.map((h, i) => (
                <motion.rect
                    key={i}
                    x={startX + i * (BAR_W + GAP)}
                    width={BAR_W}
                    rx={1.5}
                    fill={primary}
                    opacity={0.8}
                    animate={{
                        height: [h * 0.3, h, h * 0.5, maxH, h * 0.6, h * 0.3],
                        y: [54 - h * 0.3, 54 - h, 54 - h * 0.5, 54 - maxH, 54 - h * 0.6, 54 - h * 0.3]
                    }}
                    transition={{
                        duration: 0.35 + i * 0.04,
                        repeat: Infinity,
                        repeatType: "mirror",
                        delay: i * 0.03,
                        ease: "easeInOut",
                    }}
                    style={{ filter: `drop-shadow(0 0 3px ${primary})` }}
                />
            ))}
            {/* dim column bg */}
            {baseH.map((_, i) => (
                <rect key={`bg-${i}`}
                    x={startX + i * (BAR_W + GAP)} y={44} width={BAR_W} height={12}
                    rx={1.5} fill={dim} opacity={0.5} />
            ))}
        </g>
    );
}

/* ──────────────── HUD Frame ──────────────── */
function HUDFrame({ primary }: { primary: string }) {
    const C = 8;
    const corners: [number, number, string][] = [
        [2, 2, `M2,${2 + C} L2,2 L${2 + C},2`],
        [102, 2, `M${102 - C},2 L102,2 L102,${2 + C}`],
        [2, 74, `M2,${74 - C} L2,74 L${2 + C},74`],
        [102, 74, `M${102 - C},74 L102,74 L102,${74 - C}`],
    ];
    return (
        <g opacity={0.5}>
            {corners.map(([, , d], i) => (
                <path key={i} d={d} fill="none"
                    stroke={primary} strokeWidth={1.2} strokeLinecap="round" />
            ))}
        </g>
    );
}

/* ──────────────── Shy Face ──────────────── 
   A dedicated, expressive face for when JARVIS receives a compliment.
   Crescent squinting eyes + warm blush circles + gentle smile + sparkle. */
function ShyFace() {
    const PINK = "rgba(255,140,185,0.85)";
    const PINK_DIM = "rgba(255,140,185,0.18)";
    const PINK_GLOW = "rgba(255,100,160,0.35)";

    return (
        <g>
            {/* Warm pink visor wash */}
            <motion.rect
                x={2} y={2} width={100} height={72} rx={12}
                fill={PINK_GLOW}
                animate={{ opacity: [0.12, 0.22, 0.12] }}
                transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Corner ticks — pink */}
            {[
                "M2,10 L2,2 L10,2",
                "M94,2 L102,2 L102,10",
                "M2,66 L2,74 L10,74",
                "M94,74 L102,74 L102,66",
            ].map((d, i) => (
                <path key={i} d={d} fill="none"
                    stroke={PINK} strokeWidth={1.2} strokeLinecap="round" opacity={0.5} />
            ))}

            {/* ── Left eye: crescent / happy squint ── */}
            <g transform="translate(30,28)">
                {/* iris bg */}
                <ellipse cx={0} cy={0} rx={13} ry={7} fill={PINK_DIM} />
                {/* bright crescent — clip bottom half of circle */}
                <motion.path
                    d="M-11,2 Q0,-10 11,2"
                    fill="none" stroke={PINK} strokeWidth={2.5} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 4px ${PINK})` }}
                    animate={{ d: ["M-11,2 Q0,-10 11,2", "M-11,1 Q0,-11 11,1", "M-11,2 Q0,-10 11,2"] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                />
            </g>

            {/* ── Right eye: crescent / happy squint ── */}
            <g transform="translate(74,28)">
                <ellipse cx={0} cy={0} rx={13} ry={7} fill={PINK_DIM} />
                <motion.path
                    d="M-11,2 Q0,-10 11,2"
                    fill="none" stroke={PINK} strokeWidth={2.5} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 4px ${PINK})` }}
                    animate={{ d: ["M-11,2 Q0,-10 11,2", "M-11,1 Q0,-11 11,1", "M-11,2 Q0,-10 11,2"] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
                />
            </g>

            {/* ── Blush circles — left ── */}
            <motion.ellipse cx={16} cy={46} rx={11} ry={6}
                fill="rgba(255,100,150,0.10)"
                animate={{ rx: [11, 13, 11], opacity: [0.8, 1, 0.8] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.ellipse cx={16} cy={46} rx={7} ry={4}
                fill="rgba(255,100,150,0.25)"
                style={{ filter: "blur(1px)" }}
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* ── Blush circles — right ── */}
            <motion.ellipse cx={88} cy={46} rx={11} ry={6}
                fill="rgba(255,100,150,0.10)"
                animate={{ rx: [11, 13, 11], opacity: [0.8, 1, 0.8] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
            />
            <motion.ellipse cx={88} cy={46} rx={7} ry={4}
                fill="rgba(255,100,150,0.25)"
                style={{ filter: "blur(1px)" }}
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
            />

            {/* ── Gentle smile ── */}
            <motion.path
                d="M32,57 Q52,66 72,57"
                fill="none" stroke={PINK} strokeWidth={2} strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 4px ${PINK})` }}
                animate={{ d: ["M32,57 Q52,66 72,57", "M32,56 Q52,67 72,56", "M32,57 Q52,66 72,57"] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* ── Pulsing heart sparkle ── */}
            <motion.g
                transform="translate(52,12)"
                animate={{ scale: [0.8, 1.15, 0.8], opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
            >
                {/* Simple heart path centred at 0,0 */}
                <path
                    d="M0,-4 C-1,-6 -5,-6 -5,-3 C-5,0 0,4 0,4 C0,4 5,0 5,-3 C5,-6 1,-6 0,-4 Z"
                    fill={PINK}
                    style={{ filter: `drop-shadow(0 0 5px ${PINK})` }}
                />
            </motion.g>
        </g>
    );
}

/* ──────────────── Main Export ──────────────── */
export function RobotFace({
    state,
    emotion = "neutral",
    mouseOffset = { x: 0, y: 0 },
}: RobotFaceProps) {
    const pal = PALETTE[state] ?? PALETTE.idle;
    const primary = pal.primary;
    const dim = pal.dim;
    const isShy = emotion === "shy";

    return (
        <motion.div
            className="absolute pointer-events-none select-none"
            animate={{ x: mouseOffset.x, y: mouseOffset.y }}
            transition={{ type: "spring", stiffness: 180, damping: 22, mass: 0.5 }}
            style={{
                top: "16%",
                left: "50%",
                marginLeft: "-52px",
                width: "104px",
                height: "76px",
                zIndex: 20,
            }}
        >
            <svg viewBox="0 0 104 76" width="104" height="76" xmlns="http://www.w3.org/2000/svg">
                <AnimatePresence mode="wait">
                    {isShy ? (
                        <motion.g key="shy"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ duration: 0.35 }}
                        >
                            <ShyFace />
                        </motion.g>
                    ) : (
                        <motion.g key="normal"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.25 }}
                        >
                            {/* Faint visor glow */}
                            <motion.rect
                                x={2} y={2} width={100} height={72} rx={12}
                                fill={primary}
                                animate={{ opacity: state === "error" ? [0.03, 0.08, 0.03] : 0.04 }}
                                transition={{ duration: 1, repeat: Infinity, repeatType: "mirror" }}
                            />
                            <HUDFrame primary={primary} />
                            <ApertureEye cx={30} primary={primary} dim={dim} state={state} />
                            <ApertureEye cx={74} primary={primary} dim={dim} state={state} />
                            <FrequencyBar primary={primary} dim={dim} state={state} />
                        </motion.g>
                    )}
                </AnimatePresence>
            </svg>
        </motion.div>
    );
}
