import { motion } from "motion/react";
// Import image - verify path
import robotImage from "../../assets/cyborg_talking_transparent.png";

export type RobotState =
  | "idle"
  | "speaking"
  | "processing"
  | "listening"
  | "error"
  | "dancing"
  | "scanning"
  | "loading"
  | "analyzing"
  | "rebooting";

export interface RobotProps {
  state: RobotState;
  message?: string;
  emotion?: "neutral" | "happy" | "curious" | "focused" | "confused" | "surprised";
  systemStatus?: {
    cpu: number;
    memory: number;
    network: number;
    temperature: number;
    power: number;
  };
  showDiagnostics?: boolean;
  onInteraction?: () => void;
  voiceLevel?: number;
  thoughtProcess?: string[];
}

export function Robot({
  state,
  voiceLevel = 0
}: RobotProps) {
  // Simple pulsing logic for speaking based on voice level or state
  const isSpeaking = state === "speaking";

  return (
    <div className="flex flex-col items-center justify-center h-full w-full relative overflow-hidden">
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-t from-cyan-900/20 via-transparent to-transparent pointer-events-none" />

      <motion.div
        className="relative z-10 flex flex-col items-center justify-center p-8"
        animate={{
          scale: isSpeaking ? [1, 1.02 + (voiceLevel * 0.1), 1] : 1,
          filter: state === 'listening' ? 'drop-shadow(0 0 15px rgba(0, 229, 255, 0.6)) brightness(1.2)' :
            state === 'speaking' ? 'drop-shadow(0 0 25px rgba(0, 255, 136, 0.4)) brightness(1.1)' :
              state === 'error' ? 'drop-shadow(0 0 15px rgba(255, 68, 68, 0.6)) grayscale(0.5) sepia(0.5)' :
                'drop-shadow(0 0 10px rgba(0, 229, 255, 0.2))'
        }}
        transition={{
          scale: {
            repeat: isSpeaking ? Infinity : 0,
            duration: 0.15,
            ease: "easeInOut"
          },
          filter: { duration: 0.5 }
        }}
      >
        <img
          src={robotImage}
          alt="AI Robot Assistant"
          className="max-h-[65vh] w-auto object-contain pointer-events-none select-none"
          style={{
            filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.5))"
          }}
        />

        {/* Processing Indicator Overlay */}
        {state === 'processing' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
            <div className="absolute w-24 h-24 border-4 border-purple-500/30 border-b-purple-500 rounded-full animate-spin-reverse" />
          </div>
        )}

        {/* Listening Indicator */}
        {state === 'listening' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -bottom-12 left-1/2 -translate-x-1/2 bg-cyan-900/80 backdrop-blur border border-cyan-500/30 px-4 py-1 rounded-full"
          >
            <span className="text-cyan-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
          </motion.div>
        )}

        {/* Error Indicator */}
        {state === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -bottom-12 left-1/2 -translate-x-1/2 bg-red-900/80 backdrop-blur border border-red-500/30 px-4 py-1 rounded-full"
          >
            <span className="text-red-300 text-sm font-mono tracking-widest animate-pulse">SYSTEM ERROR</span>
          </motion.div>
        )}
      </motion.div>

      {/* Grid Floor Effect (Simple CSS) */}
      <div className="absolute bottom-0 w-full h-1/3 bg-[linear-gradient(to_bottom,transparent_0%,rgba(0,229,255,0.05)_100%)] pointer-events-none border-t border-cyan-500/10" />

    </div>
  );
}