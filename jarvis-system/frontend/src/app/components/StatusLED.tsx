import { motion } from "motion/react";

interface StatusLEDProps {
  color: string;
  active: boolean;
  label: string;
}

export function StatusLED({ color, active, label }: StatusLEDProps) {
  return (
    <div className="flex items-center gap-2">
      <motion.div
        className="relative w-3 h-3 rounded-full"
        style={{
          backgroundColor: color,
          opacity: active ? 1 : 0.3,
        }}
        animate={
          active
            ? {
                boxShadow: [
                  `0 0 15px ${color}`,
                  `0 0 25px ${color}`,
                  `0 0 15px ${color}`,
                ],
              }
            : {}
        }
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <span className="text-xs uppercase font-medium tracking-wider" style={{ color: active ? "#00E5FF" : "#4a5a6a" }}>
        {label}
      </span>
    </div>
  );
}