import { motion, AnimatePresence, useSpring, useTransform } from "motion/react";
import { useEffect, useState, useRef, useCallback } from "react";
import { RobotState } from "./Robot";

/* -------------------------------------------------
   Public API - backward compatible, no changes
   ------------------------------------------------- */
interface RobotFaceProps {
    state: RobotState;
    emotion?: "neutral" | "shy" | "curious" | "excited" | "confused";
    mouseOffset?: { x: number; y: number };
    intensity?: number;
}

/* -------------------------------------------------
   Design tokens - centralised tunables
   ------------------------------------------------- */
const T = {
    /** Eye geometry */
    EYE: {
        outerR: 17,
        lensR: 13.5,
        irisR: 9,
        pupilR: 5,
        glintR: 2.2,
        glintOffset: { x: -3.5, y: -3.5 },
        bladeCount: 6,
    },
    /** Frequency bar analyzer */
    BARS: { count: 13, width: 2.5, gap: 2.5 },
    /** Motion spring presets */
    SPRING: {
        lazy: { stiffness: 60, damping: 18 },
        snappy: { stiffness: 200, damping: 28 },
        micro: { stiffness: 400, damping: 40 },
    },
    /** Per-state animation timing (seconds) */
    TIMING: {
        idle: { blink: 3.8, drift: 4.5, pulse: 2.8 },
        speaking: { blink: 2.6, drift: 1.8, pulse: 0.35 },
        listening: { blink: 4.5, drift: 2.8, pulse: 1.2 },
        processing: { blink: 0, drift: 0.8, pulse: 0.22 },
        error: { blink: 0.4, drift: 0.4, pulse: 0.18 },
        scanning: { blink: 5, drift: 1.2, pulse: 0.9 },
        loading: { blink: 6, drift: 3.5, pulse: 1.6 },
        analyzing: { blink: 5, drift: 1.6, pulse: 0.7 },
        rebooting: { blink: 0, drift: 5, pulse: 2 },
        dancing: { blink: 1.8, drift: 0.6, pulse: 0.25 },
    },
} as const;

/* -------------------------------------------------
   Colour palette - state-keyed, physically motivated
   ------------------------------------------------- */
interface Palette {
    iris: string;
    irisAlt: string;
    pupil: string;
    glint: string;
    glow: string;
    glowSoft: string;
    bar: string;
    barDim: string;
    hud: string;
    hudDim: string;
    shell: string;
    lensReflect: string;
    scanline: string;
    /** CSS filter string applied to the outer container */
    dropShadow: string;
}

const PALETTE: Record<string, Palette> = {
    idle: {
        iris: "#00e8ff", irisAlt: "#0077cc",
        pupil: "#001830", glint: "#ffffff",
        glow: "rgba(0,232,255,0.55)", glowSoft: "rgba(0,200,240,0.18)",
        bar: "#00d8f0", barDim: "rgba(0,200,220,0.3)",
        hud: "#00bcd4", hudDim: "rgba(0,188,212,0.25)",
        shell: "#0d2a38", lensReflect: "rgba(160,240,255,0.25)",
        scanline: "#00e8ff",
        dropShadow: "drop-shadow(0 0 12px rgba(0,232,255,0.5))",
    },
    speaking: {
        iris: "#00ffb0", irisAlt: "#009966",
        pupil: "#001a12", glint: "#ffffff",
        glow: "rgba(0,255,160,0.55)", glowSoft: "rgba(0,220,140,0.18)",
        bar: "#00ee99", barDim: "rgba(0,200,130,0.3)",
        hud: "#00cc88", hudDim: "rgba(0,180,120,0.25)",
        shell: "#0a2218", lensReflect: "rgba(160,255,210,0.25)",
        scanline: "#00ffb0",
        dropShadow: "drop-shadow(0 0 14px rgba(0,255,160,0.6))",
    },
    processing: {
        iris: "#c060ff", irisAlt: "#8800dd",
        pupil: "#150028", glint: "#f0d0ff",
        glow: "rgba(192,80,255,0.6)", glowSoft: "rgba(170,60,230,0.2)",
        bar: "#bb44ff", barDim: "rgba(160,50,220,0.3)",
        hud: "#aa33ee", hudDim: "rgba(140,40,200,0.25)",
        shell: "#1a0030", lensReflect: "rgba(230,180,255,0.2)",
        scanline: "#cc55ff",
        dropShadow: "drop-shadow(0 0 16px rgba(192,80,255,0.65))",
    },
    listening: {
        iris: "#ffb300", irisAlt: "#cc7700",
        pupil: "#1a0e00", glint: "#fffbe0",
        glow: "rgba(255,179,0,0.55)", glowSoft: "rgba(240,160,0,0.18)",
        bar: "#ffaa00", barDim: "rgba(220,150,0,0.3)",
        hud: "#ee9900", hudDim: "rgba(200,130,0,0.25)",
        shell: "#211400", lensReflect: "rgba(255,240,160,0.22)",
        scanline: "#ffb300",
        dropShadow: "drop-shadow(0 0 12px rgba(255,179,0,0.55))",
    },
    error: {
        iris: "#ff3030", irisAlt: "#aa0000",
        pupil: "#200000", glint: "#ffdddd",
        glow: "rgba(255,48,48,0.7)", glowSoft: "rgba(220,20,20,0.22)",
        bar: "#ff2222", barDim: "rgba(200,20,20,0.3)",
        hud: "#dd1111", hudDim: "rgba(180,10,10,0.25)",
        shell: "#220000", lensReflect: "rgba(255,180,180,0.2)",
        scanline: "#ff3030",
        dropShadow: "drop-shadow(0 0 18px rgba(255,48,48,0.75))",
    },
    scanning: {
        iris: "#00ff88", irisAlt: "#009944",
        pupil: "#001a0e", glint: "#ffffff",
        glow: "rgba(0,255,136,0.55)", glowSoft: "rgba(0,220,110,0.18)",
        bar: "#00ee77", barDim: "rgba(0,200,100,0.3)",
        hud: "#00cc66", hudDim: "rgba(0,160,80,0.25)",
        shell: "#001f10", lensReflect: "rgba(160,255,200,0.22)",
        scanline: "#00ff88",
        dropShadow: "drop-shadow(0 0 12px rgba(0,255,136,0.55))",
    },
    loading: {
        iris: "#aa88ff", irisAlt: "#6644cc",
        pupil: "#0e0020", glint: "#e8dfff",
        glow: "rgba(170,136,255,0.45)", glowSoft: "rgba(150,110,240,0.15)",
        bar: "#9977ee", barDim: "rgba(130,90,210,0.28)",
        hud: "#8866dd", hudDim: "rgba(110,70,190,0.22)",
        shell: "#0f0520", lensReflect: "rgba(200,180,255,0.2)",
        scanline: "#aa88ff",
        dropShadow: "drop-shadow(0 0 10px rgba(170,136,255,0.45))",
    },
    analyzing: {
        iris: "#00ccff", irisAlt: "#0077aa",
        pupil: "#001520", glint: "#ddf8ff",
        glow: "rgba(0,204,255,0.5)", glowSoft: "rgba(0,180,230,0.17)",
        bar: "#00bbee", barDim: "rgba(0,160,200,0.28)",
        hud: "#009fcc", hudDim: "rgba(0,140,180,0.22)",
        shell: "#001b28", lensReflect: "rgba(160,240,255,0.22)",
        scanline: "#00ccff",
        dropShadow: "drop-shadow(0 0 12px rgba(0,204,255,0.5))",
    },
    rebooting: {
        iris: "#ffaa00", irisAlt: "#995500",
        pupil: "#1a0e00", glint: "#fff0c0",
        glow: "rgba(255,170,0,0.45)", glowSoft: "rgba(220,140,0,0.15)",
        bar: "#ee9900", barDim: "rgba(200,120,0,0.25)",
        hud: "#cc8800", hudDim: "rgba(170,100,0,0.2)",
        shell: "#1a1000", lensReflect: "rgba(255,230,140,0.2)",
        scanline: "#ffaa00",
        dropShadow: "drop-shadow(0 0 8px rgba(255,170,0,0.4))",
    },
    dancing: {
        iris: "#ff44ff", irisAlt: "#cc00cc",
        pupil: "#1a001a", glint: "#ffddff",
        glow: "rgba(255,68,255,0.6)", glowSoft: "rgba(220,40,220,0.2)",
        bar: "#ee33ee", barDim: "rgba(200,20,200,0.28)",
        hud: "#dd22dd", hudDim: "rgba(180,10,180,0.22)",
        shell: "#200020", lensReflect: "rgba(255,200,255,0.22)",
        scanline: "#ff44ff",
        dropShadow: "drop-shadow(0 0 16px rgba(255,68,255,0.65))",
    },
};

/* -------------------------------------------------
   Utility - stable pseudo-random per eye slot
   ------------------------------------------------- */
function seededRand(seed: number) {
    return ((Math.sin(seed) * 43758.5453) % 1 + 1) % 1;
}

/* -------------------------------------------------
   Aperture blade helper - generates a single iris blade path
   ------------------------------------------------- */
function bladeD(cx: number, cy: number, outerR: number, innerR: number, angleDeg: number): string {
    const r = (angleDeg * Math.PI) / 180;
    const spread = Math.PI / T.EYE.bladeCount;
    const ox1 = cx + outerR * Math.cos(r - spread * 0.6);
    const oy1 = cy + outerR * Math.sin(r - spread * 0.6);
    const ox2 = cx + outerR * Math.cos(r + spread * 0.6);
    const oy2 = cy + outerR * Math.sin(r + spread * 0.6);
    const ix = cx + innerR * Math.cos(r);
    const iy = cy + innerR * Math.sin(r);
    return `M${cx},${cy} Q${ox1},${oy1} ${ix},${iy} Q${ox2},${oy2} Z`;
}

/* -------------------------------------------------
   Micro-saccade hook - tiny random jitter imitating biological eye movement
   ------------------------------------------------- */
function useMicroSaccade(state: RobotState) {
    const [offset, setOffset] = useState({ x: 0, y: 0 });

    useEffect(() => {
        if (state === "rebooting" || state === "error") {
            setOffset({ x: 0, y: 0 });
            return;
        }
        const amplitude = state === "listening" ? 0.6 : state === "scanning" ? 1.2 : 0.4;
        const intervalMs = state === "processing" ? 180 : state === "scanning" ? 350 : 600;

        const tick = () => {
            // 85% chance of tiny drift, 15% chance of a micro-saccade
            if (Math.random() < 0.15) {
                setOffset({
                    x: (Math.random() - 0.5) * amplitude * 2.5,
                    y: (Math.random() - 0.5) * amplitude * 1.5,
                });
                // Snap back after a saccade
                setTimeout(() => setOffset({ x: 0, y: 0 }), 80);
            } else {
                setOffset({
                    x: (Math.random() - 0.5) * amplitude,
                    y: (Math.random() - 0.5) * amplitude * 0.6,
                });
            }
        };

        const id = setInterval(tick, intervalMs);
        return () => clearInterval(id);
    }, [state]);

    return offset;
}

/* -------------------------------------------------
   Blink hook - produces 0 (open) or 1 (closed) scale values
   ------------------------------------------------- */
function useBlink(state: RobotState): number {
    const [blink, setBlink] = useState(0);
    const timeout = useRef<ReturnType<typeof setTimeout>>();

    const scheduleNext = useCallback((delay: number) => {
        timeout.current = setTimeout(() => {
            if (state === "processing" || state === "rebooting") return;
            // Rapid double-blink for error
            if (state === "error") {
                setBlink(1);
                setTimeout(() => {
                    setBlink(0);
                    setTimeout(() => {
                        setBlink(1);
                        setTimeout(() => setBlink(0), 80);
                    }, 100);
                }, 60);
                scheduleNext(700 + Math.random() * 400);
                return;
            }
            setBlink(1);
            setTimeout(() => setBlink(0), state === "dancing" ? 100 : 130);
            const base = T.TIMING[state]?.blink ?? 3.5;
            scheduleNext((base + (Math.random() - 0.5) * base * 0.6) * 1000);
        }, delay);
    }, [state]);

    useEffect(() => {
        const base = T.TIMING[state]?.blink ?? 3.5;
        scheduleNext((base * 0.5 + Math.random() * base * 0.5) * 1000);
        return () => {
            if (timeout.current) clearTimeout(timeout.current);
        };
    }, [state, scheduleNext]);

    return blink;
}

/* -------------------------------------------------
   Frequency bar heights hook - animated per-state
   ------------------------------------------------- */
function useBarHeights(state: RobotState, intensity: number): number[] {
    const [heights, setHeights] = useState<number[]>(
        Array.from({ length: T.BARS.count }, () => 2)
    );
    const raf = useRef<number>();
    const t = useRef(0);

    useEffect(() => {
        const animate = () => {
            t.current += 0.04;
            const time = t.current;

            setHeights(Array.from({ length: T.BARS.count }, (_, i) => {
                const phase = i * 0.62 + seededRand(i) * Math.PI;
                switch (state) {
                    case "speaking":
                        return (3 + Math.sin(time * 5.5 + phase) * 7 + Math.cos(time * 8 + phase * 1.3) * 3.5) * intensity;
                    case "listening":
                        return (2 + Math.abs(Math.sin(time * 2.2 + phase)) * 10 + Math.sin(time * 0.9 + phase) * 2) * intensity;
                    case "processing":
                        return (3 + Math.sin(time * 9 + phase) * 5 + Math.cos(time * 6 + phase) * 3) * intensity;
                    case "scanning":
                        return (2 + Math.sin(time * 3.5 + phase) * 6 + Math.abs(Math.cos(time * 2 + phase)) * 3) * intensity;
                    case "error":
                        return (5 + seededRand(i + Math.floor(time * 20)) * 8) * intensity;
                    case "dancing":
                        return (2 + Math.abs(Math.sin(time * 7 + phase)) * 9 + Math.cos(time * 11 + phase * 2) * 3) * intensity;
                    case "analyzing":
                        return (2 + Math.sin(time * 4 + phase) * 5 + Math.cos(time * 2.5 + phase * 1.5) * 3.5) * intensity;
                    case "loading":
                        // Sweeping wave
                        return (2 + Math.abs(Math.sin(time * 2 - i * 0.4)) * 8) * intensity;
                    case "rebooting":
                        // Slow fade-in
                        return (1 + Math.sin(time * 0.8 + phase) * (1 + Math.min(time * 0.2, 4))) * intensity;
                    default:
                        // idle
                        return (1.5 + Math.sin(time * 1.2 + phase) * 1.2) * intensity;
                }
            }));

            raf.current = requestAnimationFrame(animate);
        };
        raf.current = requestAnimationFrame(animate);
        return () => {
            if (raf.current) cancelAnimationFrame(raf.current);
        };
    }, [state, intensity]);

    return heights;
}

/* -------------------------------------------------
   Lens flare / glint component
   ------------------------------------------------- */
function LensGlint({ cx, cy, palette, blink }: {
    cx: number; cy: number; palette: Palette; blink: number;
}) {
    return (
        <motion.g
            animate={{ opacity: blink > 0.5 ? 0 : 1 }}
            transition={{ duration: 0.04 }}
        >
            {/* Primary specular highlight - physically positioned upper-left */}
            <ellipse
                cx={cx + T.EYE.glintOffset.x}
                cy={cy + T.EYE.glintOffset.y}
                rx={T.EYE.glintR}
                ry={T.EYE.glintR * 0.65}
                fill={palette.glint}
                opacity={0.88}
                transform={`rotate(-35 ${cx + T.EYE.glintOffset.x} ${cy + T.EYE.glintOffset.y})`}
            />
            {/* Secondary soft fill-light lower-right */}
            <ellipse
                cx={cx + 4.5}
                cy={cy + 4}
                rx={1.2}
                ry={0.8}
                fill={palette.glint}
                opacity={0.35}
            />
        </motion.g>
    );
}

/* -------------------------------------------------
   Single cinematic eye
   ------------------------------------------------- */
function Eye({
    cx, cy, palette, state, intensity, blink, saccade, parallaxLayer,
}: {
    cx: number; cy: number; palette: Palette; state: RobotState;
    intensity: number; blink: number; saccade: { x: number; y: number };
    parallaxLayer: number; // 0-1, larger = more parallax
}) {
    const { outerR, lensR, irisR, pupilR, bladeCount } = T.EYE;
    const uniqueId = `eye-${cx}`;

    // Pupil dilation by state
    const pupilScale = state === "error" ? 1.3 + Math.random() * 0.2
        : state === "processing" ? 0.75
            : state === "listening" ? 0.85
                : state === "scanning" ? 0.7
                    : state === "dancing" ? 1.25
                        : 1.0;

    // Iris contraction - pupils dilate while iris ring narrows
    const irisScale = state === "scanning" ? 0.82
        : state === "processing" ? 1.1
            : state === "error" ? 1.15
                : 1.0;

    // Aperture blade rotation - closes/opens like a real lens
    const bladeRotation = state === "processing" ? 18
        : state === "scanning" ? 45
            : state === "error" ? -22
                : 0;

    return (
        <g>
            <defs>
                {/* Radial gradient: ambient occlusion inside the lens cup */}
                <radialGradient id={`aocup-${uniqueId}`} cx="45%" cy="40%" r="55%">
                    <stop offset="0%" stopColor={palette.iris} stopOpacity="0" />
                    <stop offset="100%" stopColor="#000000" stopOpacity="0.65" />
                </radialGradient>
                {/* Lens surface reflection gradient */}
                <radialGradient id={`lensrefl-${uniqueId}`} cx="35%" cy="30%" r="60%">
                    <stop offset="0%" stopColor={palette.lensReflect} />
                    <stop offset="100%" stopColor="rgba(0,0,0,0)" />
                </radialGradient>
                <clipPath id={`clip-${uniqueId}`}>
                    <circle cx={cx} cy={cy} r={lensR} />
                </clipPath>
            </defs>

            {/* Layer 0: Outer shell ring - brushed metal casing */}
            <circle cx={cx} cy={cy} r={outerR} fill={palette.shell} opacity={0.9} />
            <circle cx={cx} cy={cy} r={outerR} fill="none" stroke={palette.hud} strokeWidth={1.2} opacity={0.5} />
            {/* Micro-notch details at 12/3/6/9 o'clock - machined look */}
            {[0, 90, 180, 270].map((a) => {
                const rad = (a * Math.PI) / 180;
                return (
                    <line
                        key={a}
                        x1={cx + (outerR - 2) * Math.cos(rad)}
                        y1={cy + (outerR - 2) * Math.sin(rad)}
                        x2={cx + (outerR + 1.5) * Math.cos(rad)}
                        y2={cy + (outerR + 1.5) * Math.sin(rad)}
                        stroke={palette.hud}
                        strokeWidth={1}
                        opacity={0.5}
                    />
                );
            })}

            {/* Layer 1: Lens body - emissive fill */}
            <motion.circle
                cx={cx} cy={cy} r={lensR}
                fill={palette.iris}
                animate={{ opacity: [0.15, 0.22, 0.15] }}
                transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Layer 2: Iris mechanism - aperture blades (clipped) */}
            <g clipPath={`url(#clip-${uniqueId})`}>
                <motion.g
                    style={{ transformOrigin: `${cx}px ${cy}px` }}
                    animate={{ rotate: bladeRotation }}
                    transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                >
                    {Array.from({ length: bladeCount }, (_, i) => {
                        const angle = (i / bladeCount) * 360;
                        return (
                            <motion.path
                                key={i}
                                d={bladeD(cx, cy, lensR * irisScale, irisR * irisScale * 0.6, angle)}
                                fill={palette.irisAlt}
                                animate={{ opacity: [0.55, 0.7, 0.55] }}
                                transition={{
                                    duration: T.TIMING[state]?.pulse ?? 2.2,
                                    repeat: Infinity,
                                    delay: i * 0.06,
                                    ease: "easeInOut",
                                }}
                            />
                        );
                    })}
                </motion.g>
            </g>

            {/* Layer 3: Iris ring */}
            <motion.circle
                cx={cx} cy={cy}
                r={irisR * irisScale}
                fill="none"
                stroke={palette.iris}
                strokeWidth={1.5}
                animate={{
                    r: [irisR * irisScale, irisR * irisScale * 1.04, irisR * irisScale],
                    opacity: [0.8, 1, 0.8],
                }}
                transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Layer 4: Pupil - moves with saccade + parallax */}
            <motion.g
                animate={{
                    x: saccade.x * (1 + parallaxLayer),
                    y: saccade.y * (1 + parallaxLayer * 0.6),
                }}
                transition={{ type: "spring", ...T.SPRING.lazy }}
            >
                <motion.circle
                    cx={cx} cy={cy} r={pupilR}
                    fill={palette.pupil}
                    animate={{ r: pupilR * pupilScale }}
                    transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                    style={{
                        filter: `drop-shadow(0 0 ${4 * intensity}px ${palette.glow})`,
                    }}
                />
                {/* Hot emissive core */}
                <motion.circle
                    cx={cx} cy={cy} r={pupilR * 0.45}
                    fill={palette.iris}
                    animate={{ opacity: [0.7, 1, 0.7] }}
                    transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity }}
                    style={{ filter: "blur(1px)" }}
                />
            </motion.g>

            {/* Layer 5: Ambient occlusion cup */}
            <circle cx={cx} cy={cy} r={lensR} fill={`url(#aocup-${uniqueId})`} />

            {/* Layer 6: Blink eyelid */}
            <motion.rect
                x={cx - outerR}
                y={cy - outerR}
                width={outerR * 2}
                height={outerR * 2}
                fill={palette.shell}
                style={{ scaleY: blink, originY: "center", transformOrigin: `${cx}px ${cy}px` }}
                animate={{ scaleY: blink }}
                transition={{ duration: 0.06, ease: "easeIn" }}
            />

            {/* Layer 7: Glass lens surface - top-level reflection */}
            <circle
                cx={cx}
                cy={cy}
                r={lensR}
                fill={`url(#lensrefl-${uniqueId})`}
                opacity={0.6}
                style={{ pointerEvents: "none" }}
            />

            {/* Specular glint */}
            <LensGlint cx={cx} cy={cy} palette={palette} blink={blink} />

            {/* Processing: data-stream wavelet overlay */}
            {state === "processing" && (
                <motion.circle
                    cx={cx} cy={cy}
                    r={lensR}
                    fill="none"
                    stroke={palette.iris}
                    strokeWidth={1}
                    strokeDasharray="3 5"
                    animate={{ rotate: [0, 360] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
                    style={{ transformOrigin: `${cx}px ${cy}px` }}
                    opacity={0.35}
                />
            )}

            {/* Scanning: precision target arcs */}
            {state === "scanning" && (
                <motion.g
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.9, repeat: Infinity }}
                >
                    <circle
                        cx={cx}
                        cy={cy}
                        r={outerR + 3}
                        fill="none"
                        stroke={palette.iris}
                        strokeWidth={0.5}
                        strokeDasharray="3 7"
                        opacity={0.4}
                    />
                    <circle
                        cx={cx}
                        cy={cy}
                        r={outerR + 6}
                        fill="none"
                        stroke={palette.irisAlt}
                        strokeWidth={0.4}
                        strokeDasharray="5 9"
                        opacity={0.25}
                    />
                </motion.g>
            )}
        </g>
    );
}

/* -------------------------------------------------
   Frequency analyser - "mouth/expression" strip
   ------------------------------------------------- */
function FrequencyAnalyzer({ palette, state, intensity }: {
    palette: Palette; state: RobotState; intensity: number;
}) {
    const { count, width, gap } = T.BARS;
    const totalWidth = count * (width + gap) - gap;
    const startX = (104 - totalWidth) / 2;
    const baseY = 68; // bottom of bar area
    const heights = useBarHeights(state, intensity);

    return (
        <g>
            {/* Subtle grid substrate */}
            <rect x={startX - 1} y={baseY - 16} width={totalWidth + 2} height={16}
                fill={palette.hudDim} rx={2} />

            {heights.map((h, i) => {
                const clampedH = Math.max(1.5, Math.min(h, 14));
                return (
                    <motion.rect
                        key={i}
                        x={startX + i * (width + gap)}
                        width={width}
                        rx={1}
                        fill={palette.bar}
                        animate={{ height: clampedH, y: baseY - clampedH }}
                        transition={{
                            duration: state === "error" ? 0.04 : 0.09,
                            ease: "easeOut",
                        }}
                        style={{ filter: `drop-shadow(0 0 2px ${palette.glowSoft})` }}
                    />
                );
            })}

            {/* Scanning sweep line for scanning/processing */}
            {(state === "scanning" || state === "processing" || state === "analyzing") && (
                <motion.rect
                    x={startX}
                    y={baseY - 16}
                    width={2}
                    height={16}
                    rx={1}
                    fill={palette.scanline}
                    animate={{ x: [startX, startX + totalWidth - 2, startX] }}
                    transition={{ duration: 1.8, repeat: Infinity, ease: "linear" }}
                    opacity={0.7}
                    style={{ filter: "blur(0.5px)" }}
                />
            )}
        </g>
    );
}

/* -------------------------------------------------
   HUD chrome - corner markers, scanlines, status text
   ------------------------------------------------- */
function HUDChrome({ palette, state }: { palette: Palette; state: RobotState }) {
    const corners: [number, number][] = [[4, 4], [80, 4], [4, 58], [80, 58]];

    return (
        <g>
            {/* Corner bracket markers - L-shaped, not circles */}
            {corners.map(([x, y], i) => {
                const sx = i % 2 === 0 ? 1 : -1; // horizontal direction
                const sy = i < 2 ? 1 : -1; // vertical direction
                return (
                    <g key={i} opacity={0.6}>
                        <line x1={x} y1={y} x2={x + sx * 6} y2={y} stroke={palette.hud} strokeWidth={1.2} />
                        <line x1={x} y1={y} x2={x} y2={y + sy * 6} stroke={palette.hud} strokeWidth={1.2} />
                    </g>
                );
            })}

            {/* Animated scanline pair - horizontal sweep */}
            <motion.line
                x1="6" y1="37" x2="98" y2="37"
                stroke={palette.scanline} strokeWidth={0.4}
                strokeDasharray="6 10"
                animate={{ strokeDashoffset: [0, -16] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
                opacity={0.25}
            />
            <motion.line
                x1="6" y1="39.5" x2="98" y2="39.5"
                stroke={palette.scanline} strokeWidth={0.3}
                strokeDasharray="10 6"
                animate={{ strokeDashoffset: [0, 16] }}
                transition={{ duration: 3.1, repeat: Infinity, ease: "linear" }}
                opacity={0.15}
            />

            {/* Status tag top-right - small HUD readout */}
            <text
                x={96} y={11}
                fill={palette.hud} fontSize={5.5}
                fontFamily="monospace" textAnchor="end"
                opacity={0.55}
            >
                {state.toUpperCase()}
            </text>

            {/* Subtle outer bezel */}
            <rect x="2" y="2" width="100" height="72" rx="7"
                fill="none" stroke={palette.hudDim} strokeWidth={1}
            />
        </g>
    );
}

/* -------------------------------------------------
   State-specific overlays (target lock, data rain, etc.)
   ------------------------------------------------- */
function StateOverlay({ palette, state, intensity }: {
    palette: Palette; state: RobotState; intensity: number;
}) {
    if (state === "scanning") {
        return (
            <motion.g
                animate={{ opacity: [0.3, 0.9, 0.3] }}
                transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
            >
                <circle cx={52} cy={36} r={10} fill="none"
                    stroke={palette.iris} strokeWidth={0.8} strokeDasharray="3 4" />
                <circle cx={52} cy={36} r={14} fill="none"
                    stroke={palette.irisAlt} strokeWidth={0.5} strokeDasharray="5 6" />
                {/* Cross-hair */}
                <line x1={48} y1={36} x2={44} y2={36} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
                <line x1={56} y1={36} x2={60} y2={36} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
                <line x1={52} y1={32} x2={52} y2={28} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
                <line x1={52} y1={40} x2={52} y2={44} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
            </motion.g>
        );
    }

    if (state === "error") {
        return (
            <motion.g>
                {/* Warning chevron - minimal, readable */}
                <motion.path
                    d="M52,22 L58,32 L46,32 Z"
                    fill="none"
                    stroke={palette.iris}
                    strokeWidth={1.2}
                    animate={{ opacity: [0, 1, 1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity, times: [0, 0.1, 0.7, 1] }}
                />
                <motion.line
                    x1={52} y1={25.5} x2={52} y2={29}
                    stroke={palette.iris} strokeWidth={1}
                    animate={{ opacity: [0, 1, 1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity, times: [0, 0.1, 0.7, 1] }}
                />
            </motion.g>
        );
    }

    if (state === "rebooting") {
        return (
            <motion.g
                animate={{ opacity: [0.2, 0.6, 0.2] }}
                transition={{ duration: 2.2, repeat: Infinity }}
            >
                {/* Circular progress arc */}
                <motion.circle
                    cx={52} cy={36} r={8}
                    fill="none"
                    stroke={palette.iris}
                    strokeWidth={1.5}
                    strokeDasharray="20 30"
                    animate={{ rotate: [0, 360] }}
                    transition={{ duration: 1.8, repeat: Infinity, ease: "linear" }}
                    style={{ transformOrigin: "52px 36px" }}
                />
            </motion.g>
        );
    }

    if (state === "dancing") {
        return (
            <motion.g>
                {[0, 1, 2].map((i) => (
                    <motion.circle
                        key={i}
                        cx={52} cy={36}
                        r={6 + i * 5}
                        fill="none"
                        stroke={palette.iris}
                        strokeWidth={0.5}
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{
                            duration: 0.5,
                            repeat: Infinity,
                            delay: i * 0.15,
                            ease: "easeOut",
                        }}
                        style={{ transformOrigin: "52px 36px" }}
                        opacity={0.4 * intensity}
                    />
                ))}
            </motion.g>
        );
    }

    if (state === "loading") {
        return (
            <motion.g>
                {/* Sweeping arc progress indicator */}
                <motion.circle
                    cx={52} cy={36} r={12}
                    fill="none"
                    stroke={palette.iris}
                    strokeWidth={1}
                    strokeDasharray="8 30"
                    strokeDashoffset={0}
                    animate={{ rotate: [0, 360] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    style={{ transformOrigin: "52px 36px" }}
                    opacity={0.4}
                />
            </motion.g>
        );
    }

    return null;
}

/* -------------------------------------------------
   Main exported component
   ------------------------------------------------- */
export function RobotFace({
    state,
    emotion: _emotion = "neutral",
    mouseOffset = { x: 0, y: 0 },
    intensity = 1,
}: RobotFaceProps) {
    const palette = PALETTE[state] ?? PALETTE.idle;

    // Spring-smoothed mouse parallax for each depth layer
    const springX = useSpring(mouseOffset.x, T.SPRING.lazy);

    // Subtle idle breathing rhythm - low-amplitude vertical float
    const [breathY, setBreathY] = useState(0);
    useEffect(() => {
        let frame: number;
        let t = 0;
        const tick = () => {
            t += 0.012;
            const amp = state === "idle" ? 1.2 : state === "speaking" ? 0.4 : 0.6;
            setBreathY(Math.sin(t) * amp);
            frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(frame);
    }, [state]);

    const blink = useBlink(state);
    const saccadeLeft = useMicroSaccade(state);
    const saccadeRight = useMicroSaccade(state); // independent micro-saccades

    // Per-layer parallax offsets - deeper layers move less
    const parallaxShallow = useTransform(springX, (v) => v * 0.12);
    const parallaxMid = useTransform(springX, (v) => v * 0.06);

    return (
        <motion.div
            className="absolute pointer-events-none select-none"
            style={{
                top: "16%",
                left: "50%",
                marginLeft: "-52px",
                width: "104px",
                height: "76px",
                zIndex: 20,
                y: breathY,
                filter: palette.dropShadow,
            }}
            animate={{ x: mouseOffset.x * 0.08, y: mouseOffset.y * 0.06 + breathY }}
            transition={{ type: "spring", ...T.SPRING.lazy }}
        >
            <svg viewBox="0 0 104 76" width="104" height="76" overflow="visible">
                <defs>
                    {/* Ambient emissive glow behind whole face */}
                    <radialGradient id={`face-glow-${state}`} cx="50%" cy="45%" r="55%">
                        <stop offset="0%" stopColor={palette.glowSoft} />
                        <stop offset="100%" stopColor="rgba(0,0,0,0)" />
                    </radialGradient>
                </defs>

                <AnimatePresence mode="wait">
                    <motion.g
                        key={state}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                    >
                        {/* Background emissive ambient */}
                        <rect x="0" y="0" width="104" height="76" rx="8"
                            fill={`url(#face-glow-${state})`} opacity={0.8 * intensity}
                        />

                        {/* HUD chrome layer */}
                        <HUDChrome palette={palette} state={state} />

                        {/* State overlay (scanning crosshair, error warn, etc.) */}
                        <StateOverlay palette={palette} state={state} intensity={intensity} />

                        {/* Left eye - slightly more parallax (foreground feel) */}
                        <motion.g style={{ x: parallaxShallow }}>
                            <Eye
                                cx={30} cy={28}
                                palette={palette}
                                state={state}
                                intensity={intensity}
                                blink={blink}
                                saccade={saccadeLeft}
                                parallaxLayer={0.4}
                            />
                        </motion.g>

                        {/* Right eye - slightly less parallax */}
                        <motion.g style={{ x: parallaxMid }}>
                            <Eye
                                cx={74} cy={28}
                                palette={palette}
                                state={state}
                                intensity={intensity}
                                blink={blink}
                                saccade={saccadeRight}
                                parallaxLayer={0.25}
                            />
                        </motion.g>

                        {/* Frequency analyser strip */}
                        <FrequencyAnalyzer
                            palette={palette}
                            state={state}
                            intensity={intensity}
                        />
                    </motion.g>
                </AnimatePresence>
            </svg>
        </motion.div>
    );
}
