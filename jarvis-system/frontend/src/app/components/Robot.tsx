import Spline from '@splinetool/react-spline';
import { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, useSpring, useTransform, MotionValue } from 'motion/react';

export type RobotState =
  | 'idle'
  | 'speaking'
  | 'processing'
  | 'listening'
  | 'error'
  | 'dancing'
  | 'scanning'
  | 'loading'
  | 'analyzing'
  | 'rebooting';

export interface EmotionData {
  emotion: string;
  intensity: number;
  needs_intervention: boolean;
}

interface EmotionPanelExpressionParams {
  browLeftAngle: number;
  browRightAngle: number;
  browYOffset: number;
  eyeOpenness: number;
  pupilSize: number;
  mouthType: 'smile' | 'frown' | 'flat' | 'wavy' | 'tight' | 'open';
  mouthExtra: number;
  blushIntensity: number;
  antennaPulse: boolean;
  glowColor: string;
}

const emotionPanelExpressionMap: Record<string, (intensity: number) => EmotionPanelExpressionParams> = {
  neutral: (_i) => ({
    browLeftAngle: 0,
    browRightAngle: 0,
    browYOffset: 0,
    eyeOpenness: 0.9,
    pupilSize: 0.7,
    mouthType: 'flat',
    mouthExtra: 0.1,
    blushIntensity: 0,
    antennaPulse: false,
    glowColor: '#00E5FF',
  }),
  confident: (i) => ({
    browLeftAngle: 5,
    browRightAngle: 5,
    browYOffset: -2,
    eyeOpenness: 1,
    pupilSize: 0.85,
    mouthType: 'smile',
    mouthExtra: 0.35 + i * 0.2,
    blushIntensity: 0.1,
    antennaPulse: true,
    glowColor: '#00FF88',
  }),
  frustrated: (i) => ({
    browLeftAngle: -12,
    browRightAngle: -12,
    browYOffset: 3,
    eyeOpenness: 0.7,
    pupilSize: 0.5,
    mouthType: 'frown',
    mouthExtra: -0.3 - i * 0.2,
    blushIntensity: 0.2,
    antennaPulse: false,
    glowColor: '#FF6B35',
  }),
  stressed: (i) => ({
    browLeftAngle: 8,
    browRightAngle: 8,
    browYOffset: 4,
    eyeOpenness: 0.5,
    pupilSize: 0.4,
    mouthType: 'tight',
    mouthExtra: 0.2 + i * 0.3,
    blushIntensity: 0.3,
    antennaPulse: false,
    glowColor: '#FF4444',
  }),
  confused: (i) => ({
    browLeftAngle: -5,
    browRightAngle: 8,
    browYOffset: 1,
    eyeOpenness: 0.85,
    pupilSize: 0.6,
    mouthType: 'wavy',
    mouthExtra: 0.25 + i * 0.15,
    blushIntensity: 0.05,
    antennaPulse: false,
    glowColor: '#FFD700',
  }),
};

const getEmotionPanelMouthPath = (
  type: EmotionPanelExpressionParams['mouthType'],
  extra: number,
  width = 60,
  centerY = 30
): string => {
  const startX = -width / 2;
  const endX = width / 2;
  const midX = 0;

  switch (type) {
    case 'smile':
      return `M ${startX} ${centerY} Q ${midX} ${centerY - (10 + extra * 20)} ${endX} ${centerY}`;
    case 'frown':
      return `M ${startX} ${centerY} Q ${midX} ${centerY + (10 + Math.abs(extra) * 20)} ${endX} ${centerY}`;
    case 'flat':
      return `M ${startX} ${centerY} L ${endX} ${centerY}`;
    case 'wavy':
      return `M ${startX} ${centerY} C ${startX + width * 0.25} ${centerY - (8 + extra * 15)}, ${startX + width * 0.75} ${centerY + (8 + extra * 15)}, ${endX} ${centerY}`;
    case 'tight':
      return `M ${startX} ${centerY - 2} L ${endX} ${centerY - 2}`;
    case 'open':
      return `M ${startX} ${centerY} Q ${midX} ${centerY + (15 + extra * 20)} ${endX} ${centerY} L ${endX} ${centerY - 4} Q ${midX} ${centerY + (8 + extra * 15)} ${startX} ${centerY - 4} Z`;
    default:
      return `M ${startX} ${centerY} L ${endX} ${centerY}`;
  }
};

interface EmotionPanelProps {
  emotion: EmotionData;
  size?: number;
  className?: string;
}

export function EmotionPanel({ emotion, size = 180, className = '' }: EmotionPanelProps) {
  const intensity = Math.min(1, Math.max(0, emotion.intensity));
  const params = useMemo(() => {
    const mapper = emotionPanelExpressionMap[emotion.emotion] ?? emotionPanelExpressionMap.neutral;
    return mapper(intensity);
  }, [emotion.emotion, intensity]);

  const eyeY = params.eyeOpenness < 0.6 ? 2 : 0;
  const needsIntervention = emotion.needs_intervention;
  const mouthPath = getEmotionPanelMouthPath(params.mouthType, params.mouthExtra, 50, 30);

  return (
    <div className={`relative flex justify-center items-center ${className}`} style={{ width: size, height: size }}>
      <motion.div
        className="absolute rounded-full"
        style={{
          width: size * 0.9,
          height: size * 0.9,
          background: `radial-gradient(circle, ${params.glowColor}20 0%, transparent 70%)`,
          filter: 'blur(12px)',
        }}
        animate={{
          opacity: needsIntervention ? [0.4, 0.8, 0.4] : 0.3,
          scale: needsIntervention ? [1, 1.05, 1] : 1,
        }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
      />

      <svg viewBox="-50 -50 100 100" width="100%" height="100%" className="drop-shadow-lg">
        <rect x="-42" y="-42" width="84" height="84" rx="20" fill="#111827" stroke="#2D3748" strokeWidth="1.5" />

        <motion.line
          x1="0"
          y1="-42"
          x2="0"
          y2="-52"
          stroke={params.glowColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          animate={{ opacity: params.antennaPulse || needsIntervention ? [0.5, 1, 0.5] : 0.6 }}
          transition={{ duration: 0.8, repeat: Infinity }}
        />
        <motion.circle
          cx="0"
          cy="-54"
          r="4"
          fill={params.glowColor}
          animate={{ scale: params.antennaPulse || needsIntervention ? [1, 1.3, 1] : 1 }}
          transition={{ duration: 0.8, repeat: Infinity }}
        />

        <g transform={`translate(-18, ${eyeY})`}>
          <circle cx="0" cy="0" r="12" fill="#1F2937" stroke="#4B5563" strokeWidth="1.5" />
          <motion.circle
            cx="0"
            cy="0"
            r="10"
            fill="#0F172A"
            animate={{ scaleY: params.eyeOpenness }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          />
          <motion.circle cx="0" cy="0" r={6 * params.pupilSize} fill={params.glowColor} animate={{ scale: params.pupilSize }} transition={{ duration: 0.3 }} />
          <circle cx="-2" cy="-2" r="1.5" fill="white" opacity="0.7" />
        </g>

        <g transform={`translate(18, ${eyeY})`}>
          <circle cx="0" cy="0" r="12" fill="#1F2937" stroke="#4B5563" strokeWidth="1.5" />
          <motion.circle
            cx="0"
            cy="0"
            r="10"
            fill="#0F172A"
            animate={{ scaleY: params.eyeOpenness }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          />
          <motion.circle cx="0" cy="0" r={6 * params.pupilSize} fill={params.glowColor} animate={{ scale: params.pupilSize }} />
          <circle cx="-2" cy="-2" r="1.5" fill="white" opacity="0.7" />
        </g>

        <motion.line
          x1="-28"
          y1="-18"
          x2="-12"
          y2="-18"
          stroke={params.glowColor}
          strokeWidth="3"
          strokeLinecap="round"
          animate={{ rotate: params.browLeftAngle, y: params.browYOffset }}
          transition={{ type: 'spring', stiffness: 500 }}
          style={{ transformOrigin: '-20px -18px' }}
        />
        <motion.line
          x1="12"
          y1="-18"
          x2="28"
          y2="-18"
          stroke={params.glowColor}
          strokeWidth="3"
          strokeLinecap="round"
          animate={{ rotate: params.browRightAngle, y: params.browYOffset }}
          transition={{ type: 'spring', stiffness: 500 }}
          style={{ transformOrigin: '20px -18px' }}
        />

        <motion.path d={mouthPath} stroke={params.glowColor} strokeWidth="2.5" fill="none" strokeLinecap="round" animate={{ d: mouthPath }} transition={{ duration: 0.4, ease: 'easeOut' }} />

        {params.blushIntensity > 0 && (
          <>
            <motion.circle cx="-28" cy="12" r="6" fill="#FF8A8A" opacity={params.blushIntensity * 0.5} animate={{ opacity: params.blushIntensity * 0.5 }} />
            <motion.circle cx="28" cy="12" r="6" fill="#FF8A8A" opacity={params.blushIntensity * 0.5} animate={{ opacity: params.blushIntensity * 0.5 }} />
          </>
        )}

        <AnimatePresence>
          {needsIntervention && (
            <motion.g initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0, opacity: 0 }} transition={{ type: 'spring', stiffness: 300 }}>
              <circle cx="35" cy="-35" r="10" fill="#FF4444" stroke="#fff" strokeWidth="1.5" />
              <text x="35" y="-31" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">!</text>
            </motion.g>
          )}
        </AnimatePresence>
      </svg>

      <motion.div
        className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-[9px] font-mono tracking-wider"
        style={{ color: params.glowColor }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.7 }}
      >
        {emotion.emotion.toUpperCase()}
      </motion.div>
    </div>
  );
}

interface RobotFaceProps {
  state: RobotState;
  emotion?: 'neutral' | 'shy' | 'curious' | 'excited' | 'confused';
  mouseOffset?: { x: number; y: number };
  intensity?: number;
  modelOffset?: { x: number; y: number };
  faceWidth?: number;
  anchorXPercent?: number;
  anchorYPercent?: number;
}

type RobotEmotion = NonNullable<RobotFaceProps['emotion']>;

const T = {
  EYE: {
    outerR: 17,
    lensR: 13.5,
    irisR: 9,
    pupilR: 5,
    glintR: 2.2,
    glintOffset: { x: -3.5, y: -3.5 },
    bladeCount: 6,
  },
  BARS: {
    count: 13,
    width: 2.5,
    gap: 2.5,
    groups: 3,
    travelSpeed: 1.8,
  },
  SPRING: {
    primary: { stiffness: 280, damping: 24 },
    secondary: { stiffness: 180, damping: 20 },
    tertiary: { stiffness: 80, damping: 16 },
    parallax: { stiffness: 60, damping: 18 },
  },
  TIMING: {
    idle: { blink: 3.8, drift: 4.5, pulse: 2.8, focusDelay: 0 },
    speaking: { blink: 2.6, drift: 1.8, pulse: 0.35, focusDelay: 0.2 },
    listening: { blink: 4.5, drift: 2.8, pulse: 1.2, focusDelay: 0.4 },
    processing: { blink: 0, drift: 0.8, pulse: 0.22, focusDelay: 0.6 },
    error: { blink: 0.4, drift: 0.4, pulse: 0.18, focusDelay: 0 },
    scanning: { blink: 5, drift: 1.2, pulse: 0.9, focusDelay: 0.5 },
    loading: { blink: 6, drift: 3.5, pulse: 1.6, focusDelay: 0 },
    analyzing: { blink: 5, drift: 1.6, pulse: 0.7, focusDelay: 0.3 },
    rebooting: { blink: 0, drift: 5, pulse: 2, focusDelay: 0 },
    dancing: { blink: 1.8, drift: 0.6, pulse: 0.25, focusDelay: 0 },
  },
  GLOW: {
    coreIntensity: 0.6,
    midIntensity: 0.3,
    ambientIntensity: 0.15,
    flickerAmp: 0.04,
  },
  BLEND: {
    emotionWeight: 0.7,
    stateWeight: 0.3,
  },
} as const;

interface Palette {
  iris: string;
  irisAlt: string;
  pupil: string;
  glint: string;
  glow: string;
  glowSoft: string;
  bar: string;
  hud: string;
  hudDim: string;
  shell: string;
  lensReflect: string;
  scanline: string;
  dropShadow: string;
}

const PALETTE: Record<string, Palette> = {
  idle: { iris: '#00e8ff', irisAlt: '#0077cc', pupil: '#001830', glint: '#ffffff', glow: 'rgba(0,232,255,0.55)', glowSoft: 'rgba(0,200,240,0.18)', bar: '#00d8f0', hud: '#00bcd4', hudDim: 'rgba(0,188,212,0.25)', shell: '#0d2a38', lensReflect: 'rgba(160,240,255,0.25)', scanline: '#00e8ff', dropShadow: 'drop-shadow(0 0 12px rgba(0,232,255,0.5))' },
  speaking: { iris: '#00ffb0', irisAlt: '#009966', pupil: '#001a12', glint: '#ffffff', glow: 'rgba(0,255,160,0.55)', glowSoft: 'rgba(0,220,140,0.18)', bar: '#00ee99', hud: '#00cc88', hudDim: 'rgba(0,180,120,0.25)', shell: '#0a2218', lensReflect: 'rgba(160,255,210,0.25)', scanline: '#00ffb0', dropShadow: 'drop-shadow(0 0 14px rgba(0,255,160,0.6))' },
  processing: { iris: '#c060ff', irisAlt: '#8800dd', pupil: '#150028', glint: '#f0d0ff', glow: 'rgba(192,80,255,0.6)', glowSoft: 'rgba(170,60,230,0.2)', bar: '#bb44ff', hud: '#aa33ee', hudDim: 'rgba(140,40,200,0.25)', shell: '#1a0030', lensReflect: 'rgba(230,180,255,0.2)', scanline: '#cc55ff', dropShadow: 'drop-shadow(0 0 16px rgba(192,80,255,0.65))' },
  listening: { iris: '#ffb300', irisAlt: '#cc7700', pupil: '#1a0e00', glint: '#fffbe0', glow: 'rgba(255,179,0,0.55)', glowSoft: 'rgba(240,160,0,0.18)', bar: '#ffaa00', hud: '#ee9900', hudDim: 'rgba(200,130,0,0.25)', shell: '#211400', lensReflect: 'rgba(255,240,160,0.22)', scanline: '#ffb300', dropShadow: 'drop-shadow(0 0 12px rgba(255,179,0,0.55))' },
  error: { iris: '#ff3030', irisAlt: '#aa0000', pupil: '#200000', glint: '#ffdddd', glow: 'rgba(255,48,48,0.7)', glowSoft: 'rgba(220,20,20,0.22)', bar: '#ff2222', hud: '#dd1111', hudDim: 'rgba(180,10,10,0.25)', shell: '#220000', lensReflect: 'rgba(255,180,180,0.2)', scanline: '#ff3030', dropShadow: 'drop-shadow(0 0 18px rgba(255,48,48,0.75))' },
  scanning: { iris: '#00ff88', irisAlt: '#009944', pupil: '#001a0e', glint: '#ffffff', glow: 'rgba(0,255,136,0.55)', glowSoft: 'rgba(0,220,110,0.18)', bar: '#00ee77', hud: '#00cc66', hudDim: 'rgba(0,160,80,0.25)', shell: '#001f10', lensReflect: 'rgba(160,255,200,0.22)', scanline: '#00ff88', dropShadow: 'drop-shadow(0 0 12px rgba(0,255,136,0.55))' },
  loading: { iris: '#aa88ff', irisAlt: '#6644cc', pupil: '#0e0020', glint: '#e8dfff', glow: 'rgba(170,136,255,0.45)', glowSoft: 'rgba(150,110,240,0.15)', bar: '#9977ee', hud: '#8866dd', hudDim: 'rgba(110,70,190,0.22)', shell: '#0f0520', lensReflect: 'rgba(200,180,255,0.2)', scanline: '#aa88ff', dropShadow: 'drop-shadow(0 0 10px rgba(170,136,255,0.45))' },
  analyzing: { iris: '#00ccff', irisAlt: '#0077aa', pupil: '#001520', glint: '#ddf8ff', glow: 'rgba(0,204,255,0.5)', glowSoft: 'rgba(0,180,230,0.17)', bar: '#00bbee', hud: '#009fcc', hudDim: 'rgba(0,140,180,0.22)', shell: '#001b28', lensReflect: 'rgba(160,240,255,0.22)', scanline: '#00ccff', dropShadow: 'drop-shadow(0 0 12px rgba(0,204,255,0.5))' },
  rebooting: { iris: '#ffaa00', irisAlt: '#995500', pupil: '#1a0e00', glint: '#fff0c0', glow: 'rgba(255,170,0,0.45)', glowSoft: 'rgba(220,140,0,0.15)', bar: '#ee9900', hud: '#cc8800', hudDim: 'rgba(170,100,0,0.2)', shell: '#1a1000', lensReflect: 'rgba(255,230,140,0.2)', scanline: '#ffaa00', dropShadow: 'drop-shadow(0 0 8px rgba(255,170,0,0.4))' },
  dancing: { iris: '#ff44ff', irisAlt: '#cc00cc', pupil: '#1a001a', glint: '#ffddff', glow: 'rgba(255,68,255,0.6)', glowSoft: 'rgba(220,40,220,0.2)', bar: '#ee33ee', hud: '#dd22dd', hudDim: 'rgba(180,10,180,0.22)', shell: '#200020', lensReflect: 'rgba(255,200,255,0.22)', scanline: '#ff44ff', dropShadow: 'drop-shadow(0 0 16px rgba(255,68,255,0.65))' },
};

type FaceExpressionParams = {
  browLeftAngle: number;
  browRightAngle: number;
  browYOffset: number;
  eyeScaleY: number;
  mouthType: 'smile' | 'frown' | 'flat' | 'oShape';
  mouthCurve: number;
  mouthOpen: number;
  extraGlow: number;
};

const FACE_EXPRESSION_MAP: Record<RobotEmotion, (intensity: number) => FaceExpressionParams> = {
  neutral: () => ({ browLeftAngle: 0, browRightAngle: 0, browYOffset: 0, eyeScaleY: 1, mouthType: 'flat', mouthCurve: 0, mouthOpen: 0, extraGlow: 0 }),
  shy: (i) => ({ browLeftAngle: 4, browRightAngle: 4, browYOffset: -1, eyeScaleY: 0.85 - i * 0.1, mouthType: 'smile', mouthCurve: 0.3 + i * 0.3, mouthOpen: 0, extraGlow: 0.1 }),
  curious: (i) => ({ browLeftAngle: 10, browRightAngle: 12, browYOffset: -2, eyeScaleY: 1.05, mouthType: 'oShape', mouthCurve: 0, mouthOpen: 0.4 + i * 0.3, extraGlow: 0.2 }),
  excited: (i) => ({ browLeftAngle: 14, browRightAngle: 14, browYOffset: -3, eyeScaleY: 1.1, mouthType: 'smile', mouthCurve: 0.7 + i * 0.3, mouthOpen: 0.1, extraGlow: 0.4 }),
  confused: (i) => ({ browLeftAngle: -6, browRightAngle: 8, browYOffset: 2, eyeScaleY: 0.9, mouthType: 'frown', mouthCurve: -0.4 - i * 0.2, mouthOpen: 0, extraGlow: 0 }),
};

const stateOverlay = (state: RobotState): Partial<FaceExpressionParams> => {
  switch (state) {
    case 'speaking':
      return { mouthType: 'oShape', mouthOpen: 0.7, mouthCurve: 0 };
    case 'listening':
      return { mouthOpen: 0.3 };
    case 'error':
      return { browLeftAngle: -12, browRightAngle: -12, browYOffset: 2, eyeScaleY: 0.6, mouthType: 'frown', mouthCurve: -0.5 };
    case 'scanning':
      return { mouthType: 'flat', mouthCurve: 0 };
    case 'processing':
      return { mouthOpen: 0.1 };
    default:
      return {};
  }
};

const seededRand = (seed: number) => ((Math.sin(seed) * 43758.5453) % 1 + 1) % 1;
const randRange = (min: number, max: number, seed: number) => min + seededRand(seed) * (max - min);

const bladeD = (cx: number, cy: number, outerR: number, innerR: number, angleDeg: number): string => {
  const r = (angleDeg * Math.PI) / 180;
  const spread = Math.PI / T.EYE.bladeCount;
  const ox1 = cx + outerR * Math.cos(r - spread * 0.6);
  const oy1 = cy + outerR * Math.sin(r - spread * 0.6);
  const ox2 = cx + outerR * Math.cos(r + spread * 0.6);
  const oy2 = cy + outerR * Math.sin(r + spread * 0.6);
  const ix = cx + innerR * Math.cos(r);
  const iy = cy + innerR * Math.sin(r);
  return `M${cx},${cy} Q${ox1},${oy1} ${ix},${iy} Q${ox2},${oy2} Z`;
};

const useEyeMotion = (state: RobotState, isLeft: boolean) => {
  const [drift, setDrift] = useState({ x: 0, y: 0 });
  const [focusLock, setFocusLock] = useState(false);
  const driftRef = useRef({ x: 0, y: 0 });
  const timeRef = useRef(0);

  useEffect(() => {
    let frame: number;
    let lastTimestamp = 0;
    const animate = (now: number) => {
      if (!lastTimestamp) lastTimestamp = now;
      const dt = Math.min(0.033, (now - lastTimestamp) / 1000);
      lastTimestamp = now;
      timeRef.current += dt;

      const timing = T.TIMING[state] ?? T.TIMING.idle;
      const focusDelay = timing.focusDelay ?? 0;

      if (focusDelay > 0 && !focusLock && timeRef.current > focusDelay) {
        setFocusLock(true);
        setTimeout(() => setFocusLock(false), 600 + Math.random() * 400);
      }

      if (!focusLock) {
        const targetX = Math.sin(timeRef.current * 0.3 + (isLeft ? 0.5 : 0)) * 1.2;
        const targetY = Math.cos(timeRef.current * 0.27 + (isLeft ? 0.2 : 0)) * 0.8;
        driftRef.current.x += (targetX - driftRef.current.x) * 0.08;
        driftRef.current.y += (targetY - driftRef.current.y) * 0.08;
        setDrift({ x: driftRef.current.x, y: driftRef.current.y });
      } else {
        driftRef.current.x *= 0.98;
        driftRef.current.y *= 0.98;
        setDrift({ x: driftRef.current.x, y: driftRef.current.y });
      }

      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [state, isLeft, focusLock]);

  const [saccade, setSaccade] = useState({ x: 0, y: 0 });
  useEffect(() => {
    if (state === 'rebooting' || state === 'error') return;
    const interval = setInterval(() => {
      if (Math.random() < 0.15) {
        setSaccade({
          x: (Math.random() - 0.5) * 2.5,
          y: (Math.random() - 0.5) * 1.5,
        });
        setTimeout(() => setSaccade({ x: 0, y: 0 }), 80);
      } else {
        setSaccade({
          x: (Math.random() - 0.5),
          y: (Math.random() - 0.5) * 0.6,
        });
      }
    }, state === 'processing' ? 180 : state === 'scanning' ? 350 : 600);
    return () => clearInterval(interval);
  }, [state]);

  return { drift, saccade };
};

const useBlink = (state: RobotState, eyeSeed: number): MotionValue<number> => {
  const [blinkValue, setBlinkValue] = useState(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const schedule = useCallback(() => {
    const timing = T.TIMING[state] ?? T.TIMING.idle;
    if (timing.blink === 0) return;
    const delay = (timing.blink + randRange(-0.8, 0.8, eyeSeed)) * 1000;
    timeoutRef.current = setTimeout(() => {
      setBlinkValue(1);
      setTimeout(() => setBlinkValue(0), state === 'dancing' ? 80 : 110);
      schedule();
    }, delay);
  }, [state, eyeSeed]);

  useEffect(() => {
    schedule();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [schedule]);

  return useSpring(blinkValue, { stiffness: 400, damping: 20 });
};

const useBarHeights = (state: RobotState, intensity: number): number[] => {
  const [heights, setHeights] = useState<number[]>(Array(T.BARS.count).fill(2));
  const rafRef = useRef<number>();
  const timeRef = useRef(0);
  const prevHeights = useRef<number[]>(heights);

  useEffect(() => {
    const animate = () => {
      timeRef.current += 0.04;
      const t = timeRef.current;

      const newHeights = Array.from({ length: T.BARS.count }, (_, i) => {
        const group = Math.floor(i / (T.BARS.count / T.BARS.groups));
        const phase = i * 0.5 + group * 2.3;
        let raw = 0;
        switch (state) {
          case 'speaking':
            raw = 2 + Math.sin(t * 6 + phase) * 6 + Math.cos(t * 9 + phase * 1.2) * 3;
            break;
          case 'listening':
            raw = 1.5 + Math.abs(Math.sin(t * 2.5 + phase)) * 9;
            break;
          case 'processing':
            raw = 2 + (Math.sin(t * 12 + phase) * 4 + Math.sin(t * 23 + phase) * 2);
            break;
          case 'scanning': {
            const sweep = (Math.sin(t * 1.2) + 1) / 2;
            const bandPos = i / T.BARS.count;
            const proximity = 1 - Math.abs(bandPos - sweep) * 2.5;
            raw = 2 + Math.max(0, proximity) * 10;
            break;
          }
          case 'error':
            raw = 4 + seededRand(i + Math.floor(t * 15)) * 10;
            break;
          case 'dancing':
            raw = 2 + Math.abs(Math.sin(t * 7 + phase)) * 10 + Math.cos(t * 13 + phase) * 3;
            break;
          default:
            raw = 1.5 + Math.sin(t * 1.5 + phase) * 1.5;
        }
        const smoothed = prevHeights.current[i] * 0.6 + raw * 0.4;
        return Math.min(14, Math.max(1.5, smoothed * intensity));
      });

      prevHeights.current = newHeights;
      setHeights(newHeights);
      rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [state, intensity]);

  return heights;
};

const MultiLayerGlow = ({ state, intensity, extraBoost }: { state: RobotState; intensity: number; extraBoost: number }) => {
  const baseIntensity = Math.min(1, intensity + extraBoost);
  const [flicker, setFlicker] = useState(1);
  useEffect(() => {
    const interval = setInterval(() => {
      setFlicker(0.96 + Math.random() * 0.08);
    }, 150);
    return () => clearInterval(interval);
  }, []);

  const coreOpacity = baseIntensity * T.GLOW.coreIntensity * flicker;
  const midOpacity = baseIntensity * T.GLOW.midIntensity;
  const ambientOpacity = baseIntensity * T.GLOW.ambientIntensity;

  return (
    <>
      <rect x="0" y="0" width="104" height="76" rx="8" fill={`url(#face-glow-core-${state})`} opacity={coreOpacity} />
      <rect x="0" y="0" width="104" height="76" rx="8" fill={`url(#face-glow-mid-${state})`} opacity={midOpacity} />
      <rect x="0" y="0" width="104" height="76" rx="8" fill={`url(#face-glow-ambient-${state})`} opacity={ambientOpacity} />
    </>
  );
};

const LensGlint = ({ cx, cy, palette, blink }: { cx: number; cy: number; palette: Palette; blink: MotionValue<number> }) => (
  <motion.g style={{ opacity: useTransform(blink, (v) => (v > 0.5 ? 0 : 1)) }}>
    <ellipse
      cx={cx + T.EYE.glintOffset.x}
      cy={cy + T.EYE.glintOffset.y}
      rx={T.EYE.glintR}
      ry={T.EYE.glintR * 0.65}
      fill={palette.glint}
      opacity={0.88}
      transform={`rotate(-35 ${cx + T.EYE.glintOffset.x} ${cy + T.EYE.glintOffset.y})`}
    />
    <ellipse cx={cx + 4.5} cy={cy + 4} rx={1.2} ry={0.8} fill={palette.glint} opacity={0.35} />
  </motion.g>
);

const Eye = ({
  cx,
  cy,
  palette,
  state,
  intensity,
  blink,
  drift,
  saccade,
  parallaxLayer,
  eyeScaleY,
  focusPull,
}: {
  cx: number;
  cy: number;
  palette: Palette;
  state: RobotState;
  intensity: number;
  blink: MotionValue<number>;
  drift: { x: number; y: number };
  saccade: { x: number; y: number };
  parallaxLayer: number;
  eyeScaleY: number;
  focusPull: boolean;
}) => {
  const { outerR, lensR, irisR, pupilR, bladeCount } = T.EYE;
  const uniqueId = `eye-${cx}`;

  const pupilScale = useMemo(() => {
    if (state === 'error') return 1.3;
    if (state === 'processing') return 0.75;
    if (state === 'listening') return 0.85;
    if (state === 'scanning') return 0.7;
    if (state === 'dancing') return 1.25;
    return 1.0;
  }, [state]);

  const irisScale = useMemo(() => {
    if (state === 'scanning') return 0.82;
    if (state === 'processing') return 1.1;
    if (state === 'error') return 1.15;
    return 1.0;
  }, [state]);

  const bladeRotation = useMemo(() => {
    if (state === 'processing') return 18;
    if (state === 'scanning') return 45;
    if (state === 'error') return -22;
    return 0;
  }, [state]);

  const totalOffset = useMemo(() => ({
    x: (drift.x + saccade.x) * (1 + parallaxLayer) * (focusPull ? 0.2 : 1),
    y: (drift.y + saccade.y) * (1 + parallaxLayer * 0.6) * (focusPull ? 0.2 : 1),
  }), [drift, saccade, parallaxLayer, focusPull]);

  return (
    <motion.g
      animate={{ scaleY: eyeScaleY }}
      transition={{ type: 'spring', ...T.SPRING.primary }}
      style={{ transformOrigin: `${cx}px ${cy}px` }}
    >
      <defs>
        <radialGradient id={`aocup-${uniqueId}`} cx="45%" cy="40%" r="55%">
          <stop offset="0%" stopColor={palette.iris} stopOpacity="0" />
          <stop offset="100%" stopColor="#000000" stopOpacity="0.65" />
        </radialGradient>
        <radialGradient id={`lensrefl-${uniqueId}`} cx="35%" cy="30%" r="60%">
          <stop offset="0%" stopColor={palette.lensReflect} />
          <stop offset="100%" stopColor="rgba(0,0,0,0)" />
        </radialGradient>
        <clipPath id={`clip-${uniqueId}`}>
          <circle cx={cx} cy={cy} r={lensR} />
        </clipPath>
      </defs>

      <circle cx={cx} cy={cy} r={outerR} fill={palette.shell} opacity={0.9} />
      <circle cx={cx} cy={cy} r={outerR} fill="none" stroke={palette.hud} strokeWidth={1.2} opacity={0.5} />
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

      <motion.circle
        cx={cx}
        cy={cy}
        r={lensR}
        fill={palette.iris}
        animate={{ opacity: [0.15, 0.22, 0.15] }}
        transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity, ease: 'easeInOut' }}
      />

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
                transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity, delay: i * 0.06, ease: 'easeInOut' }}
              />
            );
          })}
        </motion.g>
      </g>

      <motion.circle
        cx={cx}
        cy={cy}
        r={irisR * irisScale}
        fill="none"
        stroke={palette.iris}
        strokeWidth={1.5}
        animate={{ r: [irisR * irisScale, irisR * irisScale * 1.04, irisR * irisScale], opacity: [0.8, 1, 0.8] }}
        transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity, ease: 'easeInOut' }}
      />

      <motion.g animate={{ x: totalOffset.x, y: totalOffset.y }} transition={{ type: 'spring', ...T.SPRING.secondary }}>
        <motion.circle
          cx={cx}
          cy={cy}
          r={pupilR}
          fill={palette.pupil}
          animate={{ r: pupilR * pupilScale }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 ${4 * intensity}px ${palette.glow})` }}
        />
        <motion.circle
          cx={cx}
          cy={cy}
          r={pupilR * 0.45}
          fill={palette.iris}
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: T.TIMING[state]?.pulse ?? 2.2, repeat: Infinity }}
          style={{ filter: 'blur(1px)' }}
        />
      </motion.g>

      <circle cx={cx} cy={cy} r={lensR} fill={`url(#aocup-${uniqueId})`} />

      <motion.rect
        x={cx - outerR}
        y={cy - outerR}
        width={outerR * 2}
        height={outerR * 2}
        fill={palette.shell}
        style={{ scaleY: blink, originY: 'center', transformOrigin: `${cx}px ${cy}px` }}
      />

      <circle cx={cx} cy={cy} r={lensR} fill={`url(#lensrefl-${uniqueId})`} opacity={0.6} style={{ pointerEvents: 'none' }} />

      <LensGlint cx={cx} cy={cy} palette={palette} blink={blink} />

      {state === 'processing' && (
        <motion.circle
          cx={cx}
          cy={cy}
          r={lensR}
          fill="none"
          stroke={palette.iris}
          strokeWidth={1}
          strokeDasharray="3 5"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: `${cx}px ${cy}px` }}
          opacity={0.35}
        />
      )}

      {state === 'scanning' && (
        <motion.g animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 0.9, repeat: Infinity }}>
          <circle cx={cx} cy={cy} r={outerR + 3} fill="none" stroke={palette.iris} strokeWidth={0.5} strokeDasharray="3 7" opacity={0.4} />
          <circle cx={cx} cy={cy} r={outerR + 6} fill="none" stroke={palette.irisAlt} strokeWidth={0.4} strokeDasharray="5 9" opacity={0.25} />
        </motion.g>
      )}
    </motion.g>
  );
};

const Eyebrows = ({ cx, cy, leftAngle, rightAngle, yOffset, color }: {
  cx: number; cy: number; leftAngle: number; rightAngle: number; yOffset: number; color: string;
}) => {
  const y = cy - 12 + yOffset;
  const barWidth = 12;
  return (
    <g>
      <motion.line
        x1={cx - barWidth} y1={y} x2={cx} y2={y}
        stroke={color} strokeWidth={2.2} strokeLinecap="round"
        animate={{ rotate: leftAngle }}
        transition={{ type: 'spring', ...T.SPRING.secondary }}
        style={{ transformOrigin: `${cx - barWidth / 2}px ${y}px` }}
      />
      <motion.line
        x1={cx} y1={y} x2={cx + barWidth} y2={y}
        stroke={color} strokeWidth={2.2} strokeLinecap="round"
        animate={{ rotate: rightAngle }}
        transition={{ type: 'spring', ...T.SPRING.secondary }}
        style={{ transformOrigin: `${cx + barWidth / 2}px ${y}px` }}
      />
    </g>
  );
};

const ExpressionMouth = ({ cx, cy, type, curve, open, color }: {
  cx: number; cy: number; type: 'smile' | 'frown' | 'flat' | 'oShape'; curve: number; open: number; color: string;
}) => {
  const width = 28;
  const startX = cx - width / 2;
  const endX = cx + width / 2;
  const baseY = cy;

  let d = '';
  if (type === 'smile') {
    const ctrlY = baseY - (8 + curve * 12);
    d = `M ${startX} ${baseY} Q ${cx} ${ctrlY} ${endX} ${baseY}`;
  } else if (type === 'frown') {
    const ctrlY = baseY + (8 + Math.abs(curve) * 12);
    d = `M ${startX} ${baseY} Q ${cx} ${ctrlY} ${endX} ${baseY}`;
  } else if (type === 'oShape') {
    const h = 6 + open * 8;
    d = `M ${startX} ${baseY} C ${startX} ${baseY - h}, ${endX} ${baseY - h}, ${endX} ${baseY} C ${endX} ${baseY + h}, ${startX} ${baseY + h}, ${startX} ${baseY} Z`;
  } else {
    d = `M ${startX} ${baseY} L ${endX} ${baseY}`;
  }

  return (
    <motion.path
      d={d}
      stroke={color}
      strokeWidth={2.4}
      fill={type === 'oShape' ? `${color}30` : 'none'}
      strokeLinecap="round"
      animate={{ d }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    />
  );
};

const FrequencyAnalyzer = ({ palette, state, intensity }: { palette: Palette; state: RobotState; intensity: number }) => {
  const { count, width, gap } = T.BARS;
  const totalWidth = count * (width + gap) - gap;
  const startX = (104 - totalWidth) / 2;
  const baseY = 68;
  const heights = useBarHeights(state, intensity);

  return (
    <g>
      <rect x={startX - 1} y={baseY - 16} width={totalWidth + 2} height={16} fill={palette.hudDim} rx={2} />
      {heights.map((h, i) => (
        <motion.rect
          key={i}
          x={startX + i * (width + gap)}
          width={width}
          rx={1}
          fill={palette.bar}
          animate={{ height: h, y: baseY - h }}
          transition={{ duration: state === 'error' ? 0.02 : 0.06, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 2px ${palette.glowSoft})` }}
        />
      ))}
      {(state === 'scanning' || state === 'processing' || state === 'analyzing') && (
        <motion.rect
          x={startX}
          y={baseY - 16}
          width={2}
          height={16}
          rx={1}
          fill={palette.scanline}
          animate={{ x: [startX, startX + totalWidth - 2, startX] }}
          transition={{ duration: T.BARS.travelSpeed, repeat: Infinity, ease: 'linear' }}
          opacity={0.7}
          style={{ filter: 'blur(0.5px)' }}
        />
      )}
    </g>
  );
};

const HUDChrome = ({ palette, state }: { palette: Palette; state: RobotState }) => {
  const corners: [number, number][] = [[4, 4], [80, 4], [4, 58], [80, 58]];
  return (
    <g>
      {corners.map(([x, y], i) => {
        const sx = i % 2 === 0 ? 1 : -1;
        const sy = i < 2 ? 1 : -1;
        return (
          <g key={i} opacity={0.6}>
            <line x1={x} y1={y} x2={x + sx * 6} y2={y} stroke={palette.hud} strokeWidth={1.2} />
            <line x1={x} y1={y} x2={x} y2={y + sy * 6} stroke={palette.hud} strokeWidth={1.2} />
          </g>
        );
      })}
      <motion.line
        x1="6" y1="37" x2="98" y2="37"
        stroke={palette.scanline} strokeWidth={0.4}
        strokeDasharray="6 10"
        animate={{ strokeDashoffset: [0, -16] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
        opacity={0.25}
      />
      <motion.line
        x1="6" y1="39.5" x2="98" y2="39.5"
        stroke={palette.scanline} strokeWidth={0.3}
        strokeDasharray="10 6"
        animate={{ strokeDashoffset: [0, 16] }}
        transition={{ duration: 3.1, repeat: Infinity, ease: 'linear' }}
        opacity={0.15}
      />
      <text x={96} y={11} fill={palette.hud} fontSize={5.5} fontFamily="monospace" textAnchor="end" opacity={0.55}>
        {state.toUpperCase()}
      </text>
      <rect x="2" y="2" width="100" height="72" rx="7" fill="none" stroke={palette.hudDim} strokeWidth={1} />
    </g>
  );
};

const StateOverlay = ({ palette, state, intensity }: { palette: Palette; state: RobotState; intensity: number }) => {
  if (state === 'scanning') {
    return (
      <motion.g animate={{ opacity: [0.3, 0.9, 0.3] }} transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}>
        <circle cx={52} cy={36} r={10} fill="none" stroke={palette.iris} strokeWidth={0.8} strokeDasharray="3 4" />
        <circle cx={52} cy={36} r={14} fill="none" stroke={palette.irisAlt} strokeWidth={0.5} strokeDasharray="5 6" />
        <line x1={48} y1={36} x2={44} y2={36} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
        <line x1={56} y1={36} x2={60} y2={36} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
        <line x1={52} y1={32} x2={52} y2={28} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
        <line x1={52} y1={40} x2={52} y2={44} stroke={palette.iris} strokeWidth={0.7} opacity={0.6} />
      </motion.g>
    );
  }
  if (state === 'error') {
    return (
      <motion.g>
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
          stroke={palette.iris}
          strokeWidth={1}
          animate={{ opacity: [0, 1, 1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity, times: [0, 0.1, 0.7, 1] }}
        />
      </motion.g>
    );
  }
  if (state === 'rebooting') {
    return (
      <motion.g animate={{ opacity: [0.2, 0.6, 0.2] }} transition={{ duration: 2.2, repeat: Infinity }}>
        <motion.circle
          cx={52} cy={36} r={8}
          fill="none" stroke={palette.iris} strokeWidth={1.5}
          strokeDasharray="20 30"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '52px 36px' }}
        />
      </motion.g>
    );
  }
  if (state === 'dancing') {
    return (
      <motion.g>
        {[0, 1, 2].map((i) => (
          <motion.circle
            key={i}
            cx={52} cy={36} r={6 + i * 5}
            fill="none" stroke={palette.iris} strokeWidth={0.5}
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.15, ease: 'easeOut' }}
            style={{ transformOrigin: '52px 36px' }}
            opacity={0.4 * intensity}
          />
        ))}
      </motion.g>
    );
  }
  if (state === 'loading') {
    return (
      <motion.g>
        <motion.circle
          cx={52} cy={36} r={12}
          fill="none" stroke={palette.iris} strokeWidth={1}
          strokeDasharray="8 30"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '52px 36px' }}
          opacity={0.4}
        />
      </motion.g>
    );
  }
  return null;
};

export function RobotFace({
  state,
  emotion = 'neutral',
  mouseOffset = { x: 0, y: 0 },
  intensity = 1,
  modelOffset = { x: 0, y: 0 },
  faceWidth = 104,
  anchorXPercent = 50,
  anchorYPercent = 16,
}: RobotFaceProps) {
  const baseFaceWidth = 104;
  const baseFaceHeight = 76;
  const faceHeight = (faceWidth * baseFaceHeight) / baseFaceWidth;
  const palette = PALETTE[state] ?? PALETTE.idle;
  const expressionIntensity = Math.min(1, Math.max(0, intensity));
  const baseline = (FACE_EXPRESSION_MAP[emotion] ?? FACE_EXPRESSION_MAP.neutral)(expressionIntensity);
  const overlay = stateOverlay(state);

  const finalBrowLeft = baseline.browLeftAngle + (overlay.browLeftAngle ?? 0);
  const finalBrowRight = baseline.browRightAngle + (overlay.browRightAngle ?? 0);
  const finalBrowY = baseline.browYOffset + (overlay.browYOffset ?? 0);
  const finalEyeScale = Math.min(1.2, Math.max(0.5, baseline.eyeScaleY * (overlay.eyeScaleY ?? 1)));
  const finalMouthType = overlay.mouthType ?? baseline.mouthType;
  const finalMouthCurve = baseline.mouthCurve + (overlay.mouthCurve ?? 0);
  const finalMouthOpen = Math.min(1, baseline.mouthOpen + (overlay.mouthOpen ?? 0));
  const glowBoost = baseline.extraGlow;

  const springX = useSpring(mouseOffset.x, T.SPRING.parallax);
  const parallaxFore = useTransform(springX, (v) => v * 0.15);
  const parallaxMid = useTransform(springX, (v) => v * 0.08);

  const [breathY, setBreathY] = useState(0);
  useEffect(() => {
    let frame: number;
    let t = 0;
    const animate = () => {
      t += 0.012;
      const amp = state === 'idle' ? 1.2 : state === 'speaking' ? 0.4 : 0.6;
      setBreathY(Math.sin(t) * amp);
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [state]);

  const leftEyeMotion = useEyeMotion(state, true);
  const rightEyeMotion = useEyeMotion(state, false);
  const blinkLeft = useBlink(state, 0.123);
  const blinkRight = useBlink(state, 0.789);

  const focusPullActive = (state === 'processing' || state === 'scanning' || state === 'listening');

  return (
    <motion.div
      className="absolute pointer-events-none select-none"
      style={{
        top: `${anchorYPercent}%`,
        left: `${anchorXPercent}%`,
        marginLeft: `${-faceWidth / 2}px`,
        width: `${faceWidth}px`,
        height: `${faceHeight}px`,
        zIndex: 20,
        y: breathY,
        filter: palette.dropShadow,
      }}
      animate={{
        x: mouseOffset.x * 0.08 + modelOffset.x,
        y: mouseOffset.y * 0.06 + modelOffset.y + breathY,
      }}
      transition={{ type: 'spring', ...T.SPRING.tertiary }}
    >
      <svg viewBox="0 0 104 76" width="104" height="76" overflow="visible">
        <defs>
          <radialGradient id={`face-glow-core-${state}`} cx="50%" cy="45%" r="45%">
            <stop offset="0%" stopColor={palette.glow} stopOpacity="0.8" />
            <stop offset="100%" stopColor={palette.glow} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`face-glow-mid-${state}`} cx="50%" cy="45%" r="60%">
            <stop offset="0%" stopColor={palette.glowSoft} stopOpacity="0.6" />
            <stop offset="100%" stopColor={palette.glowSoft} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`face-glow-ambient-${state}`} cx="50%" cy="45%" r="80%">
            <stop offset="0%" stopColor={palette.glowSoft} stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgba(0,0,0,0)" />
          </radialGradient>
        </defs>

        <AnimatePresence mode="wait">
          <motion.g
            key={state}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <MultiLayerGlow state={state} intensity={intensity} extraBoost={glowBoost} />

            <HUDChrome palette={palette} state={state} />
            <StateOverlay palette={palette} state={state} intensity={intensity} />

            <Eyebrows cx={30} cy={28} leftAngle={finalBrowLeft} rightAngle={finalBrowRight} yOffset={finalBrowY} color={palette.iris} />
            <Eyebrows cx={74} cy={28} leftAngle={finalBrowLeft} rightAngle={finalBrowRight} yOffset={finalBrowY} color={palette.iris} />

            <motion.g style={{ x: parallaxFore }}>
              <Eye
                cx={30}
                cy={28}
                palette={palette}
                state={state}
                intensity={intensity}
                blink={blinkLeft}
                drift={leftEyeMotion.drift}
                saccade={leftEyeMotion.saccade}
                parallaxLayer={0.4}
                eyeScaleY={finalEyeScale}
                focusPull={focusPullActive}
              />
            </motion.g>

            <motion.g style={{ x: parallaxMid }}>
              <Eye
                cx={74}
                cy={28}
                palette={palette}
                state={state}
                intensity={intensity}
                blink={blinkRight}
                drift={rightEyeMotion.drift}
                saccade={rightEyeMotion.saccade}
                parallaxLayer={0.25}
                eyeScaleY={finalEyeScale}
                focusPull={focusPullActive}
              />
            </motion.g>

            <ExpressionMouth cx={52} cy={52} type={finalMouthType} curve={finalMouthCurve} open={finalMouthOpen} color={palette.iris} />

            <FrequencyAnalyzer palette={palette} state={state} intensity={intensity} />
          </motion.g>
        </AnimatePresence>
      </svg>
    </motion.div>
  );
}

export interface RobotProps {
  state: RobotState;
  message?: string;
  voiceLevel?: number;
  emotion?: 'neutral' | 'shy' | 'curious' | 'excited' | 'confused';
}

export function Robot({ state, emotion = 'neutral' }: RobotProps) {
  const splineRef = useRef<any>(null);
  const headObjectRef = useRef<any>(null);
  const modelOffsetRef = useRef({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 });
  const [modelOffset, setModelOffset] = useState({ x: 0, y: 0 });
  const [faceWidth, setFaceWidth] = useState(112);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const scale = 0.08;
    setMouseOffset({
      x: (e.clientX - cx) * scale,
      y: (e.clientY - cy) * scale,
    });
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));
    const syncSize = () => {
      const rect = el.getBoundingClientRect();
      setFaceWidth(clamp(rect.width * 0.19, 96, 148));
    };

    syncSize();
    const observer = new ResizeObserver(syncSize);
    observer.observe(el);

    return () => observer.disconnect();
  }, []);

  function onLoad(splineApp: any) {
    splineRef.current = splineApp;
    if (splineApp.setBackgroundColor) splineApp.setBackgroundColor('transparent');
    if (splineApp.setZoom) splineApp.setZoom(0.9);
    setTimeout(() => {
      const watermark = document.querySelector('a[href^="https://spline.design"]');
      if (watermark) (watermark as HTMLElement).style.display = 'none';
      const shadows = document.querySelectorAll('*');
      shadows.forEach((el) => {
        if (el.shadowRoot) {
          const wm = el.shadowRoot.querySelector('a[href^="https://spline.design"]');
          if (wm) (wm as HTMLElement).style.display = 'none';
        }
      });
      const wmId = document.getElementById('spline-watermark');
      if (wmId) wmId.style.display = 'none';
    }, 1000);

    try {
      const candidateHeadNames = ['Head', 'Robot_Head', 'Face', 'Skull', 'Neobot_Head'];
      for (const name of candidateHeadNames) {
        const headObj = splineApp.findObjectByName(name);
        if (headObj) {
          headObjectRef.current = headObj;
          break;
        }
      }

      const objectsToHide = ['Text', 'Neobot', 'NEOBOT', 'Title', 'Label', 'Watermark', 'Logo', 'Brand', 'Background', 'Scene'];
      objectsToHide.forEach((name) => {
        const obj = splineApp.findObjectByName(name);
        if (obj) obj.visible = false;
      });
      if (typeof splineApp.getAllObjects === 'function') {
        const allObjects = splineApp.getAllObjects();
        if (allObjects && Array.isArray(allObjects)) {
          allObjects.forEach((obj: any) => {
            const name = obj.name ? obj.name.toLowerCase() : '';
            const type = obj.type;
            if (name.includes('text') || name.includes('neobot') || name.includes('brand') || name.includes('logo') || name.includes('watermark')) obj.visible = false;
            if (type === 'Text') obj.visible = false;
          });
        }
      }
    } catch {
      // No-op
    }
  }

  useEffect(() => {
    if (splineRef.current) {
      // Future state-driven Spline events can be added here
    }
  }, [state, emotion]);

  useEffect(() => {
    const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));
    let frame = 0;

    const tick = () => {
      const head = headObjectRef.current;
      if (head && head.position) {
        const rawX = Number(head.position.x) || 0;
        const rawY = Number(head.position.y) || 0;
        const targetX = clamp(rawX * 14, -14, 14);
        const targetY = clamp(-rawY * 11, -10, 10);

        modelOffsetRef.current.x += (targetX - modelOffsetRef.current.x) * 0.14;
        modelOffsetRef.current.y += (targetY - modelOffsetRef.current.y) * 0.14;

        setModelOffset((prev) => {
          const nx = modelOffsetRef.current.x;
          const ny = modelOffsetRef.current.y;
          if (Math.abs(prev.x - nx) < 0.02 && Math.abs(prev.y - ny) < 0.02) {
            return prev;
          }
          return { x: nx, y: ny };
        });
      }

      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden rounded-[30px]">
      <Spline
        scene="https://prod.spline.design/Ge8D8rQPojoko8eQ/scene.splinecode"
        onLoad={onLoad}
        className="w-full h-full"
      />
      <RobotFace
        state={state}
        emotion={emotion}
        mouseOffset={mouseOffset}
        modelOffset={modelOffset}
        faceWidth={faceWidth}
        anchorXPercent={50}
        anchorYPercent={16}
      />
      {state === 'processing' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="w-64 h-64 border-2 border-cyan-400/20 rounded-full animate-pulse" />
        </div>
      )}
      {state === 'listening' && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-yellow-900/80 backdrop-blur border border-yellow-500/30 px-4 py-1 rounded-full pointer-events-none z-10">
          <span className="text-yellow-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
        </div>
      )}
    </div>
  );
}
