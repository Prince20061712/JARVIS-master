import { motion } from "motion/react";
import { Clock, TrendingUp, BookOpen, Lightbulb, Target } from "lucide-react";

export interface SessionData {
    duration_mins: number;
    current_topic: string;
    mastery_score: number;
    consistency_score: number;
    suggestion: string;
    exam_days_left: number | null;
}

interface StudyDashboardProps {
    session: SessionData;
}

function StatCard({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: string; accent: string }) {
    return (
        <div className="rounded-xl border border-white/8 bg-white/5 p-3 flex items-center gap-3">
            <div className="p-1.5 rounded-lg" style={{ background: `${accent}20`, color: accent }}>
                {icon}
            </div>
            <div>
                <p className="text-[10px] text-white/40 uppercase tracking-wider">{label}</p>
                <p className="text-sm font-semibold text-white">{value}</p>
            </div>
        </div>
    );
}

function MasteryBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const color = pct >= 70 ? "#00FF88" : pct >= 40 ? "#FFD700" : "#FF6B35";
    return (
        <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-white/40">
                <span>Topic Mastery</span>
                <span style={{ color }}>{pct}%</span>
            </div>
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: color }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8 }}
                />
            </div>
        </div>
    );
}

export function StudyDashboard({ session }: StudyDashboardProps) {
    return (
        <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-white/40 uppercase tracking-widest px-1">Study Session</h3>

            <div className="grid grid-cols-2 gap-2">
                <StatCard icon={<Clock className="w-3.5 h-3.5" />} label="Duration" value={`${session.duration_mins}m`} accent="#00E5FF" />
                <StatCard icon={<TrendingUp className="w-3.5 h-3.5" />} label="Consistency" value={`${Math.round(session.consistency_score * 100)}%`} accent="#00FF88" />
            </div>

            <div className="rounded-xl border border-white/8 bg-white/5 p-3 space-y-1">
                <div className="flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                    <p className="text-[10px] text-white/40 uppercase tracking-wider">Current Topic</p>
                </div>
                <p className="text-sm font-semibold text-white truncate">{session.current_topic}</p>
                <MasteryBar score={session.mastery_score} />
            </div>

            {session.exam_days_left !== null && (
                <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-3 flex items-center gap-2">
                    <Target className="w-3.5 h-3.5 text-orange-400" />
                    <p className="text-xs text-orange-300">
                        <span className="font-bold">{session.exam_days_left} days</span> until exam
                    </p>
                </div>
            )}

            {session.suggestion && (
                <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-3 flex gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-purple-400 mt-0.5 shrink-0" />
                    <p className="text-[11px] text-purple-200">{session.suggestion}</p>
                </div>
            )}
        </div>
    );
}
