import { motion } from "motion/react";
import { useEffect } from "react";
import cyborgImage from "../../assets/Gemini_Generated_Image_y8mmppy8mmppy8mm.png";

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
  // Robot animations based on state
  const robotAnimation =
    state === "dancing"
      ? {
        y: [0, -20, 0],
        rotate: [-2, 2, -2],
      }
      : state === "listening"
        ? {
          scale: 1.05,
        }
        : state === "error"
          ? {
            x: [-5, 5, -5, 5, 0],
          }
          : {};

  const robotTransition =
    state === "dancing"
      ? {
        duration: 0.5,
        repeat: Infinity,
        ease: "easeInOut",
      }
      : state === "error"
        ? {
          duration: 0.5,
        }
        : {
          duration: 0.3,
        };

  // Glow intensity based on state
  const glowIntensity =
    state === "speaking"
      ? "0 0 80px rgba(0, 229, 255, 0.8)"
      : state === "processing"
        ? "0 0 60px rgba(0, 229, 255, 0.6)"
        : state === "listening"
          ? "0 0 70px rgba(0, 255, 0, 0.6)"
          : state === "error"
            ? "0 0 60px rgba(255, 68, 68, 0.6)"
            : "0 0 50px rgba(0, 229, 255, 0.4)";

  return (
    <div className="relative flex items-center justify-center h-full overflow-hidden">
      {/* Matrix-style background code */}
      <div className="absolute inset-0 opacity-20">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute text-xs font-mono"
            style={{
              color: "#00E5FF",
              left: `${Math.random() * 100}%`,
              top: "-20px",
            }}
            animate={{
              y: ["0vh", "100vh"],
            }}
            transition={{
              duration: 10 + Math.random() * 10,
              repeat: Infinity,
              ease: "linear",
              delay: Math.random() * 5,
            }}
          >
            {Math.random().toString(36).substring(2, 15)}
          </motion.div>
        ))}
      </div>

      {/* Glowing circles background */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute top-1/2 left-1/2 rounded-full border-2"
            style={{
              width: `${300 + i * 150}px`,
              height: `${300 + i * 150}px`,
              borderColor: "rgba(0, 229, 255, 0.2)",
              transform: "translate(-50%, -50%)",
            }}
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 4 + i,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Speech bubble */}
      {message && state === "speaking" && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          className="absolute top-20 right-10 max-w-[300px] p-4 rounded-[20px] border-2 z-20"
          style={{
            backgroundColor: "rgba(10, 20, 50, 0.95)",
            borderColor: "#00E5FF",
            boxShadow: "0 0 30px rgba(0, 229, 255, 0.5)",
          }}
        >
          <div className="absolute -bottom-3 left-1/2 transform -translate-x-1/2">
            <div
              className="w-0 h-0 border-l-[15px] border-l-transparent border-r-[15px] border-r-transparent border-t-[15px]"
              style={{ borderTopColor: "#00E5FF" }}
            />
          </div>
          <p className="text-white text-sm font-light">{message}</p>
        </motion.div>
      )}

      {/* Cyborg Robot */}
      <motion.div
        className="relative z-10"
        animate={robotAnimation}
        transition={robotTransition}
      >
        {/* Main robot image with glow */}
        <motion.div
          className="relative"
          animate={{
            boxShadow: glowIntensity,
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            repeatType: "reverse",
          }}
        >
          <img
            src={cyborgImage}
            alt="AI Cyborg"
            className="w-[500px] h-[500px] object-contain"
            style={{
              filter: `drop-shadow(${glowIntensity}) brightness(${state === "speaking" ? 1.1 : state === "error" ? 0.8 : 1
                })`,
            }}
          />

          {/* Eye glow overlay effect */}
          <motion.div
            className="absolute top-[32%] left-1/2 -translate-x-1/2 w-[200px] h-[40px]"
            style={{
              background:
                "radial-gradient(ellipse, rgba(0, 229, 255, 0.8) 0%, transparent 70%)",
              filter: "blur(10px)",
            }}
            animate={{
              opacity:
                state === "speaking"
                  ? [0.8, 1, 0.8]
                  : state === "processing"
                    ? [0.5, 1, 0.5]
                    : [0.6, 0.8, 0.6],
            }}
            transition={{
              duration: state === "processing" ? 0.5 : 2,
              repeat: Infinity,
            }}
          />
        </motion.div>

        {/* Status indicator on chest */}
        <motion.div
          className="absolute bottom-20 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg border"
          style={{
            backgroundColor: "rgba(0, 20, 40, 0.9)",
            borderColor: "#00E5FF",
            boxShadow: "0 0 20px rgba(0, 229, 255, 0.4)",
          }}
          animate={{
            opacity: [0.8, 1, 0.8],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
          }}
        >
          {state === "processing" ? (
            <div className="flex items-center gap-2">
              <motion.div
                className="w-4 h-4 border-2 border-t-[#00E5FF] border-r-[#00E5FF] border-b-transparent border-l-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "linear",
                }}
              />
              <span className="text-[#00E5FF] text-xs font-mono">PROCESSING</span>
            </div>
          ) : state === "listening" ? (
            <div className="flex items-center gap-2">
              <motion.div
                className="w-3 h-3 rounded-full bg-[#00FF00]"
                animate={{
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                }}
              />
              <span className="text-[#00FF00] text-xs font-mono">LISTENING</span>
            </div>
          ) : state === "error" ? (
            <div className="flex items-center gap-2">
              <motion.div
                className="w-3 h-3 rounded-full bg-[#FF4444]"
                animate={{
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 0.3,
                  repeat: Infinity,
                }}
              />
              <span className="text-[#FF4444] text-xs font-mono">ERROR</span>
            </div>
          ) : (
            <div className="text-[#00E5FF] text-xs font-mono tracking-wider">
              {state === "speaking" ? "SPEAKING" : "J.A.R.V.I.S ONLINE"}
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* Dancing lights effect */}
      {state === "dancing" && (
        <div className="absolute inset-0 pointer-events-none z-20">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-3 h-3 rounded-full"
              style={{
                backgroundColor: i % 3 === 0 ? "#00E5FF" : i % 3 === 1 ? "#0099FF" : "#00FFFF",
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                opacity: [0, 1, 0],
                scale: [0, 1.5, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.1,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
