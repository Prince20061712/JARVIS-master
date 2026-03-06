import { motion, AnimatePresence } from "motion/react";
import { useEffect, useState, useMemo } from "react";
import { RobotState } from "./Robot";

interface RobotFaceProps {
    state: RobotState;
    emotion?: "neutral" | "shy" | "curious" | "excited" | "confused";
    mouseOffset?: { x: number; y: number };
    intensity?: number; // 0-1 scale for expression intensity
}

/* ──────────────── Terminator-Inspired Color Palette ──────────────── */
interface ColorPalette {
    primary: string;
    secondary: string;
    dim: string;
    glow: string;
    accent: string;
    hud: string;
    scanline: string;
    gradient: {
        start: string;
        end: string;
    };
}

const PALETTE: Record<string, ColorPalette> = {
    idle: {
        primary: "#00ffff",
        secondary: "#0088ff",
        dim: "rgba(0, 255, 255, 0.15)",
        glow: "rgba(0, 255, 255, 0.4)",
        accent: "#ffffff",
        hud: "#00ccff",
        scanline: "#00ffff",
        gradient: { start: "#00ffff", end: "#0066ff" }
    },
    speaking: {
        primary: "#00ffaa",
        secondary: "#00cc88",
        dim: "rgba(0, 255, 170, 0.15)",
        glow: "rgba(0, 255, 170, 0.4)",
        accent: "#aaffff",
        hud: "#00ffaa",
        scanline: "#00ffaa",
        gradient: { start: "#00ffaa", end: "#00aa66" }
    },
    processing: {
        primary: "#bb44ff",
        secondary: "#9922dd",
        dim: "rgba(187, 68, 255, 0.18)",
        glow: "rgba(160, 32, 240, 0.5)",
        accent: "#dd99ff",
        hud: "#aa33ee",
        scanline: "#cc55ff",
        gradient: { start: "#bb44ff", end: "#7700cc" }
    },
    listening: {
        primary: "#ffaa00",
        secondary: "#ff8800",
        dim: "rgba(255, 170, 0, 0.15)",
        glow: "rgba(255, 170, 0, 0.4)",
        accent: "#ffffaa",
        hud: "#ffaa00",
        scanline: "#ffaa00",
        gradient: { start: "#ffaa00", end: "#cc6600" }
    },
    error: {
        primary: "#ff3333",
        secondary: "#cc0000",
        dim: "rgba(255, 51, 51, 0.2)",
        glow: "rgba(255, 51, 51, 0.6)",
        accent: "#ffaaaa",
        hud: "#ff3333",
        scanline: "#ff3333",
        gradient: { start: "#ff3333", end: "#990000" }
    },
    scanning: {
        primary: "#00ff88",
        secondary: "#00cc66",
        dim: "rgba(0, 255, 136, 0.15)",
        glow: "rgba(0, 255, 136, 0.4)",
        accent: "#aaffaa",
        hud: "#00ff88",
        scanline: "#00ff88",
        gradient: { start: "#00ff88", end: "#009944" }
    },
    loading: {
        primary: "#aa88ff",
        secondary: "#7755cc",
        dim: "rgba(170, 136, 255, 0.12)",
        glow: "rgba(170, 136, 255, 0.35)",
        accent: "#ccbbff",
        hud: "#9977ee",
        scanline: "#aa88ff",
        gradient: { start: "#aa88ff", end: "#7755cc" }
    },
    analyzing: {
        primary: "#00ccff",
        secondary: "#0099cc",
        dim: "rgba(0, 204, 255, 0.12)",
        glow: "rgba(0, 204, 255, 0.35)",
        accent: "#88eeff",
        hud: "#00bbee",
        scanline: "#00ccff",
        gradient: { start: "#00ccff", end: "#0077aa" }
    },
    rebooting: {
        primary: "#ffaa00",
        secondary: "#cc8800",
        dim: "rgba(255, 170, 0, 0.12)",
        glow: "rgba(255, 170, 0, 0.35)",
        accent: "#ffdd88",
        hud: "#ee9900",
        scanline: "#ffaa00",
        gradient: { start: "#ffaa00", end: "#cc6600" }
    },
    dancing: {
        primary: "#ff44ff",
        secondary: "#cc22cc",
        dim: "rgba(255, 68, 255, 0.12)",
        glow: "rgba(255, 68, 255, 0.4)",
        accent: "#ffaaff",
        hud: "#ee33ee",
        scanline: "#ff44ff",
        gradient: { start: "#ff44ff", end: "#aa00aa" }
    },
};

/* ──────────────── Terminator-Style Aperture Eye ──────────────── */
function TerminatorEye({
    cx, palette, state, intensity = 1, isLeft: _isLeft = true,
}: {
    cx: number; palette: ColorPalette; state: RobotState; intensity?: number; isLeft?: boolean;
}) {
    const [scanAngle, setScanAngle] = useState(0);
    const [irisPulse, setIrisPulse] = useState(0);

    // Scanning effect for certain states
    useEffect(() => {
        if (state === "scanning" || state === "processing") {
            const interval = setInterval(() => {
                setScanAngle(prev => (prev + 15) % 360);
            }, 50);
            return () => clearInterval(interval);
        }
    }, [state]);

    // Iris pulse effect
    useEffect(() => {
        const interval = setInterval(() => {
            setIrisPulse(prev => (prev + 0.1) % (Math.PI * 2));
        }, 50);
        return () => clearInterval(interval);
    }, []);

    const getEyeState = () => {
        switch (state) {
            case "error":
                return {
                    slitHeight: 4 + Math.sin(Date.now() * 0.02) * 2,
                    irisScale: 0.8 + Math.sin(Date.now() * 0.03) * 0.1,
                };
            case "processing":
                return {
                    slitHeight: 8 + Math.sin(Date.now() * 0.01) * 3,
                    irisScale: 1.2 + Math.sin(Date.now() * 0.02) * 0.2,
                };
            case "scanning":
                return {
                    slitHeight: 6 + Math.abs(Math.sin(Date.now() * 0.005)) * 4,
                    irisScale: 1.0 + Math.sin(Date.now() * 0.015) * 0.3,
                };
            default:
                return {
                    slitHeight: 10,
                    irisScale: 1.0,
                };
        }
    };

    const eyeState = getEyeState();

    return (
        <g>
            {/* Outer protective casing */}
            <circle
                cx={cx}
                cy={28}
                r={18}
                fill="none"
                stroke={palette.hud}
                strokeWidth={1.2}
                strokeOpacity={0.4}
                strokeDasharray="4 4"
            />

            {/* Rotating scan ring */}
            <motion.g
                animate={{ rotate: scanAngle }}
                style={{ transformOrigin: `${cx}px 28px` }}
            >
                <ellipse
                    cx={cx}
                    cy={28}
                    rx={16}
                    ry={14}
                    fill="none"
                    stroke={palette.primary}
                    strokeWidth={1}
                    strokeOpacity={0.3}
                    strokeDasharray="6 12"
                />
            </motion.g>

            {/* Iris mechanism */}
            <g>
                {/* Main iris aperture */}
                <motion.ellipse
                    cx={cx}
                    cy={28}
                    rx={14 * eyeState.irisScale}
                    ry={12 * eyeState.irisScale}
                    fill="none"
                    stroke={palette.primary}
                    strokeWidth={1.5}
                    strokeOpacity={0.8}
                />

                {/* Crosshair aiming reticle */}
                <line
                    x1={cx - 20}
                    y1={28}
                    x2={cx - 14}
                    y2={28}
                    stroke={palette.primary}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                <line
                    x1={cx + 14}
                    y1={28}
                    x2={cx + 20}
                    y2={28}
                    stroke={palette.primary}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                <line
                    x1={cx}
                    y1={14}
                    x2={cx}
                    y2={20}
                    stroke={palette.primary}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                <line
                    x1={cx}
                    y1={36}
                    x2={cx}
                    y2={42}
                    stroke={palette.primary}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
            </g>

            {/* Active aperture slit */}
            <motion.rect
                x={cx - 12}
                y={28 - eyeState.slitHeight / 2}
                width={24}
                height={eyeState.slitHeight}
                fill={palette.primary}
                style={{
                    filter: `drop-shadow(0 0 ${8 * intensity}px ${palette.glow})`,
                }}
                animate={{
                    opacity: [0.8, 1, 0.8],
                }}
                transition={{
                    duration: 1,
                    repeat: Infinity,
                }}
            />

            {/* Data stream overlay */}
            {state === "processing" && (
                <motion.path
                    d={`M${cx - 15},${28} L${cx - 8},${28 - irisPulse * 2} L${cx},${28 + irisPulse} L${cx + 8},${28 - irisPulse} L${cx + 15},${28}`}
                    stroke={palette.secondary}
                    strokeWidth={1}
                    fill="none"
                    animate={{
                        d: [
                            `M${cx - 15},${28} L${cx - 8},${20} L${cx},${36} L${cx + 8},${20} L${cx + 15},${28}`,
                            `M${cx - 15},${28} L${cx - 8},${36} L${cx},${20} L${cx + 8},${36} L${cx + 15},${28}`,
                        ],
                    }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                />
            )}
        </g>
    );
}

/* ──────────────── Terminator-Style Frequency Analyzer ──────────────── */
function TerminatorFrequencyBar({
    palette, state, intensity = 1,
}: {
    palette: ColorPalette; state: RobotState; intensity?: number;
}) {
    const NUM_BARS = 15;
    const BAR_W = 2;
    const GAP = 2;
    const TOTAL = NUM_BARS * (BAR_W + GAP) - GAP;
    const startX = (104 - TOTAL) / 2;

    const frequencies = useMemo(() => {
        return Array.from({ length: NUM_BARS }, (_, i) => ({
            base: 2 + Math.sin(i * 1.5) * 3 + Math.cos(i * 0.8) * 2,
            phase: i * 0.7,
        }));
    }, []);

    const getBarAnimations = (index: number) => {
        const time = Date.now() * 0.003;
        const phase = frequencies[index].phase;

        switch (state) {
            case "speaking":
                return {
                    height: 3 + Math.sin(time * 2 + phase) * 8 + Math.cos(time * 3 + phase) * 4,
                };
            case "listening":
                return {
                    height: 2 + Math.abs(Math.sin(time * 0.8 + phase)) * 12,
                };
            case "processing":
            case "scanning":
                return {
                    height: 4 + Math.sin(time * 3 + phase) * 6 + Math.cos(time * 2 + phase) * 4,
                };
            case "error":
                return {
                    height: 6 + Math.random() * 8,
                };
            default:
                return { height: 3 };
        }
    };

    if (state === "error") {
        return (
            <motion.path
                d={`M${startX} 56 Q${startX + TOTAL / 2} ${48 + Math.sin(Date.now() * 0.02) * 8} ${startX + TOTAL} 56`}
                fill="none"
                stroke={palette.primary}
                strokeWidth={2}
                strokeLinecap="round"
                animate={{
                    d: [
                        `M${startX} 56 Q${startX + TOTAL / 2} 48 ${startX + TOTAL} 56`,
                        `M${startX} 56 Q${startX + TOTAL / 2} 64 ${startX + TOTAL} 56`,
                    ],
                }}
                transition={{ duration: 0.2, repeat: Infinity }}
                style={{ filter: `drop-shadow(0 0 6px ${palette.primary})` }}
            />
        );
    }

    return (
        <g>
            {/* Digital grid background */}
            <rect
                x={startX - 2}
                y={44}
                width={TOTAL + 4}
                height={20}
                fill="none"
                stroke={palette.hud}
                strokeWidth={0.5}
                strokeOpacity={0.2}
            />

            {/* Frequency bars */}
            {frequencies.map((_freq, i) => {
                const anim = getBarAnimations(i);
                return (
                    <motion.rect
                        key={i}
                        x={startX + i * (BAR_W + GAP)}
                        width={BAR_W}
                        fill={palette.primary}
                        animate={{
                            height: anim.height * intensity,
                            y: 56 - anim.height * intensity,
                            opacity: [0.6, 1, 0.6],
                        }}
                        transition={{
                            height: {
                                duration: (state as string) === "error" ? 0.03 : 0.1,
                                repeat: Infinity,
                                repeatType: "mirror",
                            },
                        }}
                        style={{ filter: `drop-shadow(0 0 2px ${palette.glow})` }}
                    />
                );
            })}

            {/* Scanning line */}
            {(state === "scanning" || state === "processing") && (
                <motion.rect
                    x={startX}
                    y={52}
                    width={2}
                    height={8}
                    rx={1}
                    fill={palette.scanline}
                    animate={{ x: [startX, startX + TOTAL - 2, startX] }}
                    transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "linear",
                    }}
                    style={{ filter: `blur(1px)` }}
                />
            )}
        </g>
    );
}

/* ──────────────── Terminator HUD Frame ──────────────── */
function TerminatorHUDFrame({ palette, state }: { palette: ColorPalette; state: RobotState }) {
    return (
        <g>
            {/* Main frame with bolt pattern */}
            <rect
                x="2" y="2" width="100" height="72" rx="8"
                fill="none"
                stroke={palette.hud}
                strokeWidth={1.5}
                strokeOpacity={0.3}
                strokeDasharray="6 6"
            />

            {/* Corner reinforcements */}
            {[
                [2, 2], [92, 2], [2, 64], [92, 64]
            ].map(([x, y], i) => (
                <g key={i}>
                    <circle
                        cx={x + 6}
                        cy={y + 6}
                        r={4}
                        fill="none"
                        stroke={palette.primary}
                        strokeWidth={1}
                        strokeOpacity={0.6}
                    />
                    <circle
                        cx={x + 6}
                        cy={y + 6}
                        r={1.5}
                        fill={palette.primary}
                        opacity={0.8}
                    />
                </g>
            ))}

            {/* Status indicators */}
            <text
                x="12" y="18"
                fill={palette.primary}
                fontSize="6"
                fontFamily="monospace"
                opacity="0.6"
            >
                SYS:ONLINE
            </text>
            <text
                x="72" y="18"
                fill={palette.primary}
                fontSize="6"
                fontFamily="monospace"
                opacity="0.6"
            >
                {state.toUpperCase()}
            </text>

            {/* Scan lines */}
            <motion.line
                x1="4" y1="38" x2="100" y2="38"
                stroke={palette.scanline}
                strokeWidth={0.5}
                strokeDasharray="4 8"
                animate={{ strokeDashoffset: [0, -12] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                opacity={0.3}
            />
            <motion.line
                x1="4" y1="40" x2="100" y2="40"
                stroke={palette.scanline}
                strokeWidth={0.5}
                strokeDasharray="8 4"
                animate={{ strokeDashoffset: [0, -12] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                opacity={0.3}
            />
        </g>
    );
}

/* ──────────────── Main Component ──────────────── */
export function RobotFace({
    state,
    emotion: _emotion = "neutral",
    mouseOffset = { x: 0, y: 0 },
    intensity = 1,
}: RobotFaceProps) {
    const palette = PALETTE[state] ?? PALETTE.idle;

    // Particle system for digital rain effect
    const [digitalRain, setDigitalRain] = useState<Array<{ x: number; y: number; char: string; delay: number }>>([]);

    useEffect(() => {
        const chars = "01アイウエオカキクケコサシスセソタチツテト";
        setDigitalRain(
            Array.from({ length: 15 }, (_, i) => ({
                x: Math.random() * 104,
                y: Math.random() * 76,
                char: chars[Math.floor(Math.random() * chars.length)],
                delay: i * 0.1,
            }))
        );
    }, []);

    return (
        <motion.div
            className="absolute pointer-events-none select-none"
            animate={{
                x: mouseOffset.x,
                y: mouseOffset.y,
            }}
            transition={{
                type: "spring",
                stiffness: 200,
                damping: 25,
            }}
            style={{
                top: "16%",
                left: "50%",
                marginLeft: "-52px",
                width: "104px",
                height: "76px",
                zIndex: 20,
                filter: `drop-shadow(0 0 ${15 * intensity}px ${palette.glow})`,
            }}
        >
            <svg viewBox="0 0 104 76" width="104" height="76">
                <defs>
                    <linearGradient id={`grad-${state}`} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={palette.gradient.start} stopOpacity="0.6" />
                        <stop offset="100%" stopColor={palette.gradient.end} stopOpacity="0.6" />
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
                    {/* Background digital rain effect */}
                    {state === "processing" && (
                        <motion.g
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.3 }}
                            exit={{ opacity: 0 }}
                        >
                            {digitalRain.map((drop, i) => (
                                <motion.text
                                    key={i}
                                    x={drop.x}
                                    y={drop.y}
                                    fill={palette.primary}
                                    fontSize="6"
                                    fontFamily="monospace"
                                    initial={{ opacity: 0 }}
                                    animate={{
                                        opacity: [0, 0.8, 0],
                                        y: [drop.y, drop.y + 50],
                                    }}
                                    transition={{
                                        duration: 2,
                                        delay: drop.delay,
                                        repeat: Infinity,
                                    }}
                                >
                                    {drop.char}
                                </motion.text>
                            ))}
                        </motion.g>
                    )}

                    {/* Main HUD */}
                    <motion.g
                        key="hud"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        {/* Background with subtle gradient */}
                        <rect
                            x="0" y="0" width="104" height="76" rx="8"
                            fill={`url(#grad-${state})`}
                            opacity={0.1}
                        />

                        <TerminatorHUDFrame palette={palette} state={state} />

                        <TerminatorEye
                            cx={30}
                            palette={palette}
                            state={state}
                            intensity={intensity}
                            isLeft={true}
                        />
                        <TerminatorEye
                            cx={74}
                            palette={palette}
                            state={state}
                            intensity={intensity}
                            isLeft={false}
                        />

                        <TerminatorFrequencyBar
                            palette={palette}
                            state={state}
                            intensity={intensity}
                        />

                        {/* Target lock indicators for scanning state */}
                        {state === "scanning" && (
                            <motion.g
                                animate={{ opacity: [0.4, 1, 0.4] }}
                                transition={{ duration: 1, repeat: Infinity }}
                            >
                                <circle cx="52" cy="38" r="12" fill="none" stroke={palette.primary} strokeWidth="1" strokeDasharray="4 4" />
                                <circle cx="52" cy="38" r="18" fill="none" stroke={palette.secondary} strokeWidth="0.5" strokeDasharray="6 6" />
                            </motion.g>
                        )}
                    </motion.g>
                </AnimatePresence>
            </svg>
        </motion.div>
    );
}