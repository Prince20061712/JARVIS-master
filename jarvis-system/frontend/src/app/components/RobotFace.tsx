import { motion, AnimatePresence } from "motion/react";
import { useEffect, useState, useMemo } from "react";
import { RobotState } from "./Robot";

interface RobotFaceProps {
    state: RobotState;
    emotion?: "neutral" | "shy" | "curious" | "excited" | "confused";
    mouseOffset?: { x: number; y: number };
    intensity?: number; // 0-1 scale for expression intensity
}

/* ──────────────── Enhanced Palette with Gradients ──────────────── */
interface ColorPalette {
    primary: string;
    secondary: string;
    dim: string;
    glow: string;
    accent: string;
    gradient: {
        start: string;
        end: string;
    };
}

const PALETTE: Record<string, ColorPalette> = {
    idle: {
        primary: "rgba(140,210,255,0.9)",
        secondary: "rgba(100,180,255,0.6)",
        dim: "rgba(140,210,255,0.15)",
        glow: "rgba(140,210,255,0.3)",
        accent: "rgba(200,230,255,0.8)",
        gradient: { start: "#8cd2ff", end: "#4aa8ff" }
    },
    speaking: {
        primary: "rgba(100,255,200,0.9)",
        secondary: "rgba(64,224,208,0.6)",
        dim: "rgba(100,255,200,0.12)",
        glow: "rgba(100,255,200,0.35)",
        accent: "rgba(200,255,230,0.8)",
        gradient: { start: "#64ffc8", end: "#3cb9a0" }
    },
    processing: {
        primary: "rgba(180,140,255,0.9)",
        secondary: "rgba(147,112,219,0.6)",
        dim: "rgba(180,140,255,0.12)",
        glow: "rgba(180,140,255,0.3)",
        accent: "rgba(220,200,255,0.8)",
        gradient: { start: "#b48cff", end: "#8a6ae8" }
    },
    listening: {
        primary: "rgba(255,215,120,0.9)",
        secondary: "rgba(255,185,80,0.6)",
        dim: "rgba(255,215,120,0.12)",
        glow: "rgba(255,215,120,0.3)",
        accent: "rgba(255,235,200,0.8)",
        gradient: { start: "#ffd778", end: "#ffb350" }
    },
    error: {
        primary: "rgba(255,90,90,0.95)",
        secondary: "rgba(255,60,60,0.7)",
        dim: "rgba(255,90,90,0.15)",
        glow: "rgba(255,90,90,0.4)",
        accent: "rgba(255,150,150,0.8)",
        gradient: { start: "#ff5a5a", end: "#ff3838" }
    },
    scanning: {
        primary: "rgba(80,200,255,0.9)",
        secondary: "rgba(60,180,255,0.6)",
        dim: "rgba(80,200,255,0.12)",
        glow: "rgba(80,200,255,0.35)",
        accent: "rgba(180,230,255,0.8)",
        gradient: { start: "#50c8ff", end: "#3a9eff" }
    },
    loading: {
        primary: "rgba(200,160,255,0.9)",
        secondary: "rgba(170,130,255,0.6)",
        dim: "rgba(200,160,255,0.12)",
        glow: "rgba(200,160,255,0.3)",
        accent: "rgba(230,210,255,0.8)",
        gradient: { start: "#c8a0ff", end: "#aa82ff" }
    },
    analyzing: {
        primary: "rgba(160,180,255,0.9)",
        secondary: "rgba(140,160,255,0.6)",
        dim: "rgba(160,180,255,0.12)",
        glow: "rgba(160,180,255,0.3)",
        accent: "rgba(210,220,255,0.8)",
        gradient: { start: "#a0b4ff", end: "#7a8cff" }
    },
    rebooting: {
        primary: "rgba(255,170,100,0.9)",
        secondary: "rgba(255,140,70,0.6)",
        dim: "rgba(255,170,100,0.12)",
        glow: "rgba(255,170,100,0.3)",
        accent: "rgba(255,210,170,0.8)",
        gradient: { start: "#ffaa64", end: "#ff8c46" }
    },
    dancing: {
        primary: "rgba(255,130,255,0.9)",
        secondary: "rgba(230,100,230,0.6)",
        dim: "rgba(255,130,255,0.12)",
        glow: "rgba(255,130,255,0.35)",
        accent: "rgba(255,200,255,0.8)",
        gradient: { start: "#ff82ff", end: "#e06ae0" }
    },
};

/* ──────────────── Advanced Aperture Eye with Iris Animation ──────────────── */
function AdvancedApertureEye({
    cx, palette, state, intensity = 1,
}: {
    cx: number; palette: ColorPalette; state: RobotState; intensity?: number;
}) {
    const [blink, setBlink] = useState(false);
    const [irisRotation, setIrisRotation] = useState(0);

    // Sophisticated blink system
    useEffect(() => {
        if (state !== "idle" && state !== "scanning" && state !== "analyzing") return;

        const schedule = () => {
            const delay = 2000 + Math.random() * 5000;
            return setTimeout(() => {
                setBlink(true);
                setTimeout(() => {
                    setBlink(false);
                    schedule();
                }, 120);
            }, delay);
        };

        const timer = schedule();
        return () => clearTimeout(timer);
    }, [state]);

    // Iris rotation for processing/analyzing states
    useEffect(() => {
        if (state === "processing" || state === "analyzing") {
            const interval = setInterval(() => {
                setIrisRotation(prev => (prev + 15) % 360);
            }, 50);
            return () => clearInterval(interval);
        }
    }, [state]);

    const getEyeHeight = () => {
        if (blink) return 1;
        switch (state) {
            case "error": return 4 * intensity;
            case "processing": return 8 + Math.sin(Date.now() * 0.01) * 2;
            case "dancing": return 12 + Math.sin(Date.now() * 0.02) * 4;
            default: return 10;
        }
    };

    const getIrisEffect = () => {
        if (state === "processing" || state === "analyzing") {
            return (
                <motion.circle
                    cx={cx}
                    cy={28}
                    r={6}
                    fill="none"
                    stroke={palette.primary}
                    strokeWidth={1.5}
                    strokeDasharray="2 4"
                    style={{ rotate: irisRotation }}
                    animate={{ opacity: [0.3, 0.8, 0.3] }}
                    transition={{ duration: 1, repeat: Infinity }}
                />
            );
        }
        return null;
    };

    return (
        <g>
            {/* Outer ring with glow */}
            <motion.circle
                cx={cx}
                cy={28}
                r={16}
                fill="none"
                stroke={palette.dim}
                strokeWidth={1.5}
                animate={{
                    r: [16, 17, 16],
                    opacity: [0.3, 0.6, 0.3],
                }}
                transition={{ duration: 3, repeat: Infinity }}
            />

            {/* Main iris background with subtle pulse */}
            <motion.ellipse
                cx={cx}
                cy={28}
                rx={14}
                ry={10}
                fill={palette.dim}
                animate={{
                    opacity: state === "processing" ? [0.5, 0.8, 0.5] : 0.6,
                    scaleX: state === "dancing" ? [1, 1.1, 1] : 1,
                    scaleY: state === "dancing" ? [1, 0.9, 1] : 1,
                }}
                transition={{ duration: 0.5, repeat: state === "dancing" ? Infinity : 0 }}
            />

            {/* Bright slit with dynamic effects */}
            <motion.rect
                x={cx - 12}
                y={28 - getEyeHeight() / 2}
                width={24}
                height={getEyeHeight()}
                rx={4}
                fill={palette.primary}
                animate={{
                    height: getEyeHeight(),
                    y: 28 - getEyeHeight() / 2,
                    opacity: state === "error" ? [0.9, 0.4, 0.9] : 0.95,
                    filter: [
                        `drop-shadow(0 0 ${4 * intensity}px ${palette.glow})`,
                        `drop-shadow(0 0 ${8 * intensity}px ${palette.primary})`,
                        `drop-shadow(0 0 ${4 * intensity}px ${palette.glow})`,
                    ],
                }}
                transition={{
                    height: { duration: blink ? 0.05 : 0.2 },
                    opacity: { duration: 0.5, repeat: state === "error" ? Infinity : 0 },
                    filter: { duration: 1, repeat: Infinity },
                }}
            />

            {/* Iris effect overlay */}
            {getIrisEffect()}

            {/* Corner markers */}
            <path
                d={`M${cx - 18},22 L${cx - 14},22 M${cx + 18},22 L${cx + 14},22`}
                stroke={palette.accent}
                strokeWidth={1.5}
                strokeLinecap="round"
                opacity={0.4}
            />
        </g>
    );
}

/* ──────────────── Advanced Frequency Analyzer ──────────────── */
function AdvancedFrequencyBar({
    palette, state, intensity = 1,
}: {
    palette: ColorPalette; state: RobotState; intensity?: number;
}) {
    const NUM_BARS = 13;
    const BAR_W = 3;
    const GAP = 3;
    const TOTAL = NUM_BARS * (BAR_W + GAP) - GAP;
    const startX = (104 - TOTAL) / 2;

    // Generate dynamic frequencies based on state
    const frequencies = useMemo(() => {
        return Array.from({ length: NUM_BARS }, (_, i) => ({
            base: 3 + Math.sin(i * 1.2) * 4 + Math.cos(i * 0.7) * 3,
            phase: i * 0.5,
        }));
    }, []);

    const getBarAnimations = (index: number) => {
        const time = Date.now() * 0.002;
        const phase = frequencies[index].phase;

        switch (state) {
            case "speaking":
                return {
                    height: 4 + Math.sin(time + phase) * 8 + Math.cos(time * 2 + phase) * 4,
                };
            case "listening":
                return {
                    height: 3 + Math.abs(Math.sin(time * 0.5 + phase)) * 10,
                };
            case "processing":
            case "analyzing":
                return {
                    height: 5 + Math.sin(time * 2 + phase) * 5 + Math.cos(time + phase) * 3,
                };
            case "dancing":
                return {
                    height: 6 + Math.sin(time * 3 + phase) * 8 + Math.sin(time * 5 + phase * 2) * 4,
                };
            case "error":
                return {
                    height: 8 + Math.random() * 4,
                };
            default:
                return { height: 4 };
        }
    };

    if (state === "idle" || state === "loading") {
        // Pulsing line with particles
        return (
            <g>
                <motion.line
                    x1={startX} y1={54} x2={startX + TOTAL} y2={54}
                    stroke={palette.primary}
                    strokeWidth={1.5}
                    strokeLinecap="round"
                    animate={{
                        opacity: [0.2, 0.6, 0.2],
                        strokeDasharray: ["2 6", "4 8", "2 6"],
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                />
                {/* Floating particles */}
                {[0, 1, 2].map((i) => (
                    <motion.circle
                        key={i}
                        cx={startX + (i * TOTAL) / 2}
                        cy={54}
                        r={1.5}
                        fill={palette.primary}
                        animate={{
                            y: [54, 48, 54],
                            opacity: [0, 0.5, 0],
                        }}
                        transition={{
                            duration: 1.5,
                            delay: i * 0.3,
                            repeat: Infinity,
                        }}
                    />
                ))}
            </g>
        );
    }

    if (state === "error") {
        return (
            <motion.path
                d={`M${startX} 56 Q${startX + TOTAL / 2} ${48 + Math.sin(Date.now() * 0.01) * 4} ${startX + TOTAL} 56`}
                fill="none"
                stroke={palette.primary}
                strokeWidth={2}
                strokeLinecap="round"
                animate={{
                    d: [
                        `M${startX} 56 Q${startX + TOTAL / 2} 48 ${startX + TOTAL} 56`,
                        `M${startX} 56 Q${startX + TOTAL / 2} 64 ${startX + TOTAL} 56`,
                        `M${startX} 56 Q${startX + TOTAL / 2} 48 ${startX + TOTAL} 56`,
                    ],
                }}
                transition={{ duration: 0.3, repeat: Infinity }}
                style={{ filter: `drop-shadow(0 0 6px ${palette.primary})` }}
            />
        );
    }

    return (
        <g>
            {/* Background bars */}
            {frequencies.map((_, i) => (
                <rect
                    key={`bg-${i}`}
                    x={startX + i * (BAR_W + GAP)}
                    y={44}
                    width={BAR_W}
                    height={16}
                    rx={2}
                    fill={palette.dim}
                    opacity={0.3}
                />
            ))}

            {/* Animated frequency bars */}
            {frequencies.map((_freq, i) => {
                const anim = getBarAnimations(i);
                return (
                    <motion.rect
                        key={i}
                        x={startX + i * (BAR_W + GAP)}
                        width={BAR_W}
                        rx={1.5}
                        fill={palette.primary}
                        animate={{
                            height: anim.height * intensity,
                            y: 54 - anim.height * intensity,
                            opacity: [0.7, 1, 0.7],
                        }}
                        transition={{
                            height: {
                                duration: 0.15,
                                repeat: Infinity,
                                repeatType: "mirror",
                                ease: "easeInOut",
                            },
                            opacity: {
                                duration: 1,
                                repeat: Infinity,
                            },
                        }}
                        style={{ filter: `drop-shadow(0 0 3px ${palette.glow})` }}
                    />
                );
            })}

            {/* Scanning line for special states */}
            {(state === "scanning" || state === "analyzing") && (
                <motion.rect
                    x={startX}
                    y={52}
                    width={2}
                    height={4}
                    rx={1}
                    fill={palette.accent}
                    animate={{ x: [startX, startX + TOTAL - 2, startX] }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "linear",
                    }}
                    style={{ filter: `blur(1px)` }}
                />
            )}
        </g>
    );
}

/* ──────────────── Enhanced HUD with Dynamic Elements ──────────────── */
function EnhancedHUDFrame({ palette }: { palette: ColorPalette; state: RobotState }) {
    return (
        <g>
            {/* Corner brackets */}
            {[
                [2, 2, 10],
                [92, 2, 10],
                [2, 64, 10],
                [92, 64, 10],
            ].map(([x, y, size], i) => (
                <g key={i}>
                    <path
                        d={`M${x},${y + size} L${x},${y} L${x + size},${y}`}
                        fill="none"
                        stroke={palette.primary}
                        strokeWidth={1.2}
                        strokeLinecap="round"
                        opacity={0.6}
                    />
                    <motion.circle
                        cx={x + 2}
                        cy={y + 2}
                        r={1.5}
                        fill={palette.primary}
                        animate={{
                            opacity: [0.2, 0.8, 0.2],
                            scale: [1, 1.2, 1],
                        }}
                        transition={{ duration: 2, delay: i * 0.2, repeat: Infinity }}
                    />
                </g>
            ))}

            {/* Top and bottom scan lines */}
            <motion.line
                x1="4" y1="4" x2="100" y2="4"
                stroke={palette.primary}
                strokeWidth={0.5}
                strokeDasharray="4 4"
                animate={{ strokeDashoffset: [0, -8] }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                opacity={0.3}
            />
            <motion.line
                x1="4" y1="72" x2="100" y2="72"
                stroke={palette.primary}
                strokeWidth={0.5}
                strokeDasharray="4 4"
                animate={{ strokeDashoffset: [0, 8] }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                opacity={0.3}
            />
        </g>
    );
}

/* ──────────────── Emotion Faces ──────────────── */
const EmotionFaces = {
    shy: ({ palette }: { palette: ColorPalette }) => (
        <g>
            {/* Blush effects */}
            <motion.circle cx="20" cy="44" r="10" fill="rgba(255,140,185,0.15)" />
            <motion.circle cx="84" cy="44" r="10" fill="rgba(255,140,185,0.15)" />
            <motion.ellipse cx="20" cy="46" rx="8" ry="5" fill="rgba(255,100,150,0.2)" />
            <motion.ellipse cx="84" cy="46" rx="8" ry="5" fill="rgba(255,100,150,0.2)" />

            {/* Happy squinting eyes */}
            <path d="M28,26 Q36,20 44,26" stroke={palette.primary} strokeWidth="3" fill="none" />
            <path d="M60,26 Q68,20 76,26" stroke={palette.primary} strokeWidth="3" fill="none" />

            {/* Gentle smile */}
            <path d="M38,56 Q52,64 66,56" stroke={palette.primary} strokeWidth="2.5" fill="none" />

            {/* Floating hearts */}
            <motion.g
                animate={{ y: [0, -5, 0], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
            >
                <path d="M52,12 L55,15 L58,12 Q58,9 55,9 Q52,9 52,12" fill={palette.primary} />
            </motion.g>
        </g>
    ),

    curious: ({ palette }: { palette: ColorPalette }) => (
        <g>
            {/* Tilted head effect */}
            <motion.g
                animate={{ rotate: [-1, 1, -1] }}
                transition={{ duration: 3, repeat: Infinity }}
            >
                <circle cx="30" cy="28" r="8" fill="none" stroke={palette.primary} strokeWidth="2" />
                <circle cx="74" cy="28" r="8" fill="none" stroke={palette.primary} strokeWidth="2" />
                <circle cx="32" cy="26" r="2" fill={palette.primary} />
                <circle cx="76" cy="26" r="2" fill={palette.primary} />
            </motion.g>

            {/* Question mark animation */}
            <motion.text
                x="52" y="40"
                textAnchor="middle"
                fill={palette.primary}
                fontSize="20"
                fontWeight="bold"
                animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
            >
                ?
            </motion.text>
        </g>
    ),

    excited: ({ palette }: { palette: ColorPalette }) => (
        <g>
            {/* Star eyes */}
            <g transform="translate(30,28)">
                <motion.path
                    d="M-6,0 L0,-6 L6,0 L0,6 Z"
                    stroke={palette.primary}
                    strokeWidth="2"
                    fill="none"
                    animate={{ rotate: 360, scale: [1, 1.2, 1] }}
                    transition={{ duration: 3, repeat: Infinity }}
                />
            </g>
            <g transform="translate(74,28)">
                <motion.path
                    d="M-6,0 L0,-6 L6,0 L0,6 Z"
                    stroke={palette.primary}
                    strokeWidth="2"
                    fill="none"
                    animate={{ rotate: 360, scale: [1, 1.2, 1] }}
                    transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
                />
            </g>

            {/* Excitement lines */}
            {[0, 1, 2].map((i) => (
                <motion.line
                    key={i}
                    x1={20 + i * 30}
                    y1={50}
                    x2={30 + i * 30}
                    y2={40}
                    stroke={palette.primary}
                    strokeWidth="1.5"
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 1, delay: i * 0.2, repeat: Infinity }}
                />
            ))}
        </g>
    ),

    confused: ({ palette }: { palette: ColorPalette }) => (
        <g>
            {/* Spiral eyes */}
            <g transform="translate(30,28)">
                <motion.circle
                    r="8"
                    fill="none"
                    stroke={palette.primary}
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity }}
                />
            </g>
            <g transform="translate(74,28)">
                <motion.circle
                    r="8"
                    fill="none"
                    stroke={palette.primary}
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    animate={{ rotate: -360 }}
                    transition={{ duration: 4, repeat: Infinity }}
                />
            </g>

            {/* Wavy mouth */}
            <motion.path
                d="M30,56 Q52,64 74,56"
                stroke={palette.primary}
                strokeWidth="2"
                fill="none"
                animate={{ d: ["M30,56 Q52,64 74,56", "M30,60 Q52,52 74,60"] }}
                transition={{ duration: 1, repeat: Infinity }}
            />
        </g>
    ),
};

/* ──────────────── Main Export ──────────────── */
export function RobotFace({
    state,
    emotion = "neutral",
    mouseOffset = { x: 0, y: 0 },
    intensity = 1,
}: RobotFaceProps) {
    const palette = PALETTE[state] ?? PALETTE.idle;
    const [particleSystem, setParticleSystem] = useState<Array<{ x: number; y: number; delay: number }>>([]);

    // Initialize particle system
    useEffect(() => {
        setParticleSystem(
            Array.from({ length: 8 }, (_, i) => ({
                x: Math.random() * 104,
                y: Math.random() * 76,
                delay: i * 0.2,
            }))
        );
    }, []);

    return (
        <motion.div
            className="absolute pointer-events-none select-none"
            animate={{
                x: mouseOffset.x,
                y: mouseOffset.y,
                scale: emotion === "excited" ? [1, 1.05, 1] : 1,
            }}
            transition={{
                type: "spring",
                stiffness: 180,
                damping: 22,
                mass: 0.5,
                scale: { duration: 0.3, repeat: emotion === "excited" ? Infinity : 0 }
            }}
            style={{
                top: "16%",
                left: "50%",
                marginLeft: "-52px",
                width: "104px",
                height: "76px",
                zIndex: 20,
                filter: `drop-shadow(0 0 ${10 * intensity}px ${palette.glow})`,
            }}
        >
            <svg viewBox="0 0 104 76" width="104" height="76">
                <defs>
                    <linearGradient id={`grad-${state}`} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={palette.gradient.start} stopOpacity="0.8" />
                        <stop offset="100%" stopColor={palette.gradient.end} stopOpacity="0.8" />
                    </linearGradient>
                    <filter id={`glow-${state}`}>
                        <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                <AnimatePresence mode="wait">
                    {emotion !== "neutral" ? (
                        <motion.g
                            key={emotion}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ duration: 0.35 }}
                        >
                            {/* Background glow */}
                            <motion.rect
                                x="0" y="0" width="104" height="76" rx="16"
                                fill={`url(#grad-${state})`}
                                opacity={0.1}
                                animate={{
                                    opacity: [0.1, 0.2, 0.1],
                                }}
                                transition={{ duration: 2, repeat: Infinity }}
                            />

                            {/* Emotion-specific face */}
                            {EmotionFaces[emotion as keyof typeof EmotionFaces]?.({ palette })}

                            {/* Particle system */}
                            {particleSystem.map((particle, i) => (
                                <motion.circle
                                    key={i}
                                    cx={particle.x}
                                    cy={particle.y}
                                    r={1}
                                    fill={palette.primary}
                                    animate={{
                                        opacity: [0, 0.5, 0],
                                        scale: [0, 1, 0],
                                        x: particle.x + (Math.random() - 0.5) * 20,
                                        y: particle.y + (Math.random() - 0.5) * 20,
                                    }}
                                    transition={{
                                        duration: 2,
                                        delay: particle.delay,
                                        repeat: Infinity,
                                    }}
                                />
                            ))}
                        </motion.g>
                    ) : (
                        <motion.g
                            key="normal"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.25 }}
                        >
                            {/* Background with gradient */}
                            <motion.rect
                                x="2" y="2" width="100" height="72" rx="14"
                                fill={`url(#grad-${state})`}
                                opacity={0.08}
                                animate={{
                                    opacity: [0.08, 0.15, 0.08],
                                }}
                                transition={{ duration: 2, repeat: Infinity }}
                            />

                            <EnhancedHUDFrame palette={palette} state={state} />

                            <AdvancedApertureEye
                                cx={30}
                                palette={palette}
                                state={state}
                                intensity={intensity}
                            />
                            <AdvancedApertureEye
                                cx={74}
                                palette={palette}
                                state={state}
                                intensity={intensity}
                            />

                            <AdvancedFrequencyBar
                                palette={palette}
                                state={state}
                                intensity={intensity}
                            />

                            {/* Floating particles for dynamic states */}
                            {(state === "processing" || state === "analyzing") && (
                                <g>
                                    {[0, 1, 2].map((i) => (
                                        <motion.circle
                                            key={i}
                                            cx={20 + i * 30}
                                            cy={20}
                                            r={2}
                                            fill={palette.primary}
                                            animate={{
                                                y: [20, 10, 20],
                                                opacity: [0.3, 0.8, 0.3],
                                            }}
                                            transition={{
                                                duration: 1.5,
                                                delay: i * 0.3,
                                                repeat: Infinity,
                                            }}
                                        />
                                    ))}
                                </g>
                            )}
                        </motion.g>
                    )}
                </AnimatePresence>
            </svg>
        </motion.div>
    );
}