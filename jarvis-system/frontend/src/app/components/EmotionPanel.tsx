import { motion, AnimatePresence } from "motion/react";
import { Heart, Zap, Brain, Smile } from "lucide-react";

export interface EmotionData {
    emotion: string;
    intensity: number;
    needs_intervention: boolean;
}

interface EmotionPanelProps {
    emotion: EmotionData;
}

const emotionConfig: Record<string, { color: string; icon: React.ReactNode; label: string; tip: string }> = {
    neutral: { color: "#00E5FF", icon: <Smile className="w-4 h-4" />, label: "Focused", tip: "Great focus! Ask me anything." },
    confident: { color: "#00FF88", icon: <Zap className="w-4 h-4" />, label: "Confident", tip: "You're on a roll! Try a harder problem." },
    frustrated: { color: "#FF6B35", icon: <Brain className="w-4 h-4" />, label: "Frustrated", tip: "Let's break it down step by step." },
    stressed: { color: "#FF4444", icon: <Heart className="w-4 h-4" />, label: "Stressed", tip: "Take a breath — 4-7-8 breathing helps." },
    confused: { color: "#FFD700", icon: <Brain className="w-4 h-4" />, label: "Confused", tip: "Let me simplify this for you." },
};

export function EmotionPanel({ emotion }: EmotionPanelProps) {
    const config = emotionConfig[emotion.emotion] ?? emotionConfig.neutral;
    const pct = Math.round(emotion.intensity * 100);

    return (
        <div className="rounded-2xl border border-white/10 bg-black/30 backdrop-blur-md p-4 space-y-3">
            <div className="flex items-center gap-2">
                <div style={{ color: config.color }}>{config.icon}</div>
                <span className="text-xs font-semibold tracking-widest uppercase" style={{ color: config.color }}>
                    {config.label}
                </span>
                {emotion.needs_intervention && (
                    <span className="ml-auto text-[10px] bg-orange-500/20 text-orange-300 border border-orange-500/30 px-2 py-0.5 rounded-full animate-pulse">
                        Intervention Active
                    </span>
                )}
            </div>

            {/* Intensity Bar */}
            <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: config.color }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                />
            </div>

            {/* Tip */}
            <AnimatePresence mode="wait">
                <motion.p
                    key={emotion.emotion}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="text-[11px] text-white/50 italic"
                >
                    💡 {config.tip}
                </motion.p>
            </AnimatePresence>
        </div>
    );
}
