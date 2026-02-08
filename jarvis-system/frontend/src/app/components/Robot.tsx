import { motion, AnimatePresence } from "motion/react";
import { useEffect, useState } from "react";
import cyborgImage from "../../assets/cyborg_transparent_final.png";
import cyborgTalkingImage from "../../assets/cyborg_talking_transparent.png";
import cyborgTalkingHalfImage from "../../assets/cyborg_talking_half_transparent.png";

export type RobotState =
  | "idle"
  | "speaking"
  | "processing"
  | "listening"
  | "error"
  | "dancing";

interface RobotProps {
  state: RobotState;
  message?: string;
}

export function Robot({ state, message }: RobotProps) {
  const [frameIndex, setFrameIndex] = useState(0); // 0: Closed, 1: Half, 2: Open

  // Smoother Lip-sync effect with 3 frames
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    if (state === "speaking") {
      // Sequence: Closed -> Half -> Open -> Half -> Closed ...
      // Indices: 0 -> 1 -> 2 -> 1 -> 0 ...
      const sequence = [0, 1, 2, 1];
      let currentIndex = 0;

      interval = setInterval(() => {
        currentIndex = (currentIndex + 1) % sequence.length;
        setFrameIndex(sequence[currentIndex]);
      }, 80); // Faster interval for smoother animation (approx 12fps)
    } else {
      setFrameIndex(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [state]);

  // Determine which image to show based on frame index
  const currentImage =
    state === "speaking"
      ? (frameIndex === 0 ? cyborgImage :
        frameIndex === 1 ? cyborgTalkingHalfImage :
          cyborgTalkingImage)
      : cyborgImage;

  // Keyframe animations for hologram effect
  const scanlineVariants = {
    animate: {
      y: ["0%", "100%"],
      opacity: [0, 1, 0],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "linear" as const,
      },
    },
  };

  const glitchVariants = {
    idle: { x: 0, opacity: 1 },
    processing: {
      x: [-2, 2, -2, 2, 0],
      opacity: [1, 0.8, 1, 0.9, 1],
      transition: { duration: 0.2, repeat: Infinity, repeatDelay: 0.5 },
    },
    error: {
      x: [-5, 5, -5, 5, 0],
      y: [-2, 2, 0],
      transition: { duration: 0.1, repeat: Infinity },
    },
  };

  return (
    <div className="relative flex items-end justify-center h-full overflow-hidden pb-0 bg-transparent">
      {/* Holographic Emitter Base */}
      <div className="absolute bottom-0 w-[400px] h-[100px] bg-gradient-to-t from-[rgba(0,229,255,0.2)] to-transparent rounded-[50%] blur-xl transform scale-x-150" />

      <div className="absolute bottom-10 w-[300px] h-[30px] border-[1px] border-[rgba(0,229,255,0.4)] rounded-[50%] animate-pulse shadow-[0_0_20px_rgba(0,229,255,0.5)]">
        <div className="absolute inset-2 border-[1px] border-[rgba(0,229,255,0.2)] rounded-[50%]" />
      </div>

      {/* Upward Projection Beams */}
      <div className="absolute bottom-10 w-full h-full flex justify-center pointer-events-none overflow-hidden">
        <div
          className="w-[300px] h-full bg-gradient-to-t from-[rgba(0,229,255,0.1)] via-[rgba(0,229,255,0.05)] to-transparent"
          style={{ clipPath: "polygon(20% 0%, 80% 0%, 100% 100%, 0% 100%)" }}
        />
      </div>

      {/* Rotating Data Rings (Background) */}
      <div className="absolute bottom-[20%] w-[500px] h-[500px] border border-[rgba(0,229,255,0.1)] rounded-full animate-[spin_10s_linear_infinite]" />
      <div className="absolute bottom-[20%] w-[450px] h-[450px] border border-[rgba(0,229,255,0.1)] border-dashed rounded-full animate-[spin_15s_linear_infinite_reverse]" />

      {/* Speech bubble */}
      <AnimatePresence>
        {message && state === "speaking" && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            className="absolute top-20 right-10 max-w-[300px] p-4 rounded-xl border border-[rgba(0,229,255,0.4)] z-30 backdrop-blur-md"
            style={{
              background: "linear-gradient(135deg, rgba(0, 20, 50, 0.9), rgba(0, 10, 30, 0.95))",
              boxShadow: "0 0 30px rgba(0, 229, 255, 0.2)",
            }}
          >
            {/* Tech decoration corners */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-[#00E5FF]" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-[#00E5FF]" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-[#00E5FF]" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-[#00E5FF]" />

            <p className="text-[#00E5FF] text-sm font-light tracking-wide leading-relaxed font-mono">
              <span className="mr-2 text-xs opacity-70">Running output...</span><br />
              {message}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Holographic Robot Container */}
      <motion.div
        className="relative z-10 w-full h-full flex items-end justify-center pb-12"
        variants={glitchVariants}
        animate={state}
      >
        <motion.div className="relative max-h-full group">
          {/* Hologram Scanlines */}
          <div className="absolute inset-0 z-20 pointer-events-none bg-[linear-gradient(transparent_50%,rgba(0,229,255,0.1)_50%)] bg-[length:100%_4px]" />
          <motion.div
            className="absolute inset-0 z-20 bg-gradient-to-b from-transparent via-[rgba(0,229,255,0.1)] to-transparent h-[20%]"
            variants={scanlineVariants}
            animate="animate"
          />

          {/* Main Robot Image */}
          <img
            src={currentImage}
            alt="Holographic AI"
            className="w-auto h-auto max-h-[85vh] object-contain transition-none" // Disable transition for instant frame swap
            style={{
              filter: `
                    drop-shadow(0 0 10px rgba(0, 229, 255, 0.5)) 
                    drop-shadow(0 0 30px rgba(0, 229, 255, 0.2))
                    hue-rotate(180deg) sepia(50%) saturate(150%) hue-rotate(-180deg) 
                    brightness(1.1) contrast(1.1) text-shadow(0 0 10px #00e5ff)
                  `,
              opacity: 0.9,
            }}
          />

          {/* Hologram Tint Overlay */}
          <div className="absolute inset-0 z-10 mix-blend-color bg-[rgba(0,229,255,0.2)] pointer-events-none" />

          {/* Eye glow override */}
          <motion.div
            className="absolute top-[32%] left-1/2 -translate-x-1/2 w-[120px] h-[30px] z-30 pointer-events-none"
            style={{
              background: "radial-gradient(ellipse, #00E5FF 0%, transparent 70%)",
              filter: "blur(5px)",
              opacity: 0.8
            }}
            animate={{
              opacity: [0.6, 1, 0.6],
              scale: [0.9, 1.1, 0.9]
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />

        </motion.div>
      </motion.div>

      {/* Status Text Overlay */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 z-30">
        <div className="text-[10px] items-center flex gap-2 text-[#00E5FF] font-mono tracking-[0.2em] opacity-80 decoration-none">
          <div className="w-2 h-2 bg-[#00E5FF] rounded-full animate-pulse" />
          {state === "speaking" ? "TRANSMITTING" :
            state === "listening" ? "RECEIVING INPUT" :
              state === "processing" ? "ANALYZING DATA" :
                state === "error" ? "SYSTEM FAILURE" : "SYSTEM ONLINE"}
        </div>
        <div className="w-[150px] h-[1px] bg-gradient-to-r from-transparent via-[#00E5FF] to-transparent opacity-50" />
      </div>

    </div>
  );
}
