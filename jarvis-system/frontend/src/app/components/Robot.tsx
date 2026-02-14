import { useRef, useEffect } from 'react';
import NormalFace from './avatar/Normal_face.mp4';
import TalkingFace from './avatar/Talking_face.mp4';
import ShyFace from './avatar/Shy_face.mp4';
import DancingBody from './avatar/Dancing_body.mp4';

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
  voiceLevel?: number;
  emotion?: 'neutral' | 'shy';
}

export function Robot({ state, emotion = 'neutral' }: RobotProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // Determine which video to play based on state and emotion
  const getVideoSource = () => {
    if (state === 'dancing') return DancingBody;
    if (emotion === 'shy') return ShyFace;
    if (state === 'speaking') return TalkingFace;
    return NormalFace;
  };

  const videoSrc = getVideoSource();

  // Handle video source change
  useEffect(() => {
    console.log(`[Robot] State: ${state}, Emotion: ${emotion}, Video Src: ${videoSrc}`);
    if (videoRef.current) {
      console.log(`[Robot] Loading video: ${videoSrc}`);
      videoRef.current.load();
      videoRef.current.play().catch(e => console.error("[Robot] Auto-play error:", e));
    }
  }, [videoSrc, state, emotion]);

  return (
    <div className="flex flex-col items-center justify-center h-full w-full relative overflow-hidden bg-black">
      {/* Video Avatar */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay
        loop
        muted
        playsInline
      >
        <source src={videoSrc} type="video/mp4" />
      </video>

      {/* Overlay Effects (Optional: keep existing overlays if desired) */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />

      {/* Processing Indicator Overlay */}
      {state === 'processing' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="w-64 h-64 border-2 border-cyan-400/20 rounded-full animate-pulse" />
        </div>
      )}

      {/* Listening Indicator */}
      {state === 'listening' && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-cyan-900/80 backdrop-blur border border-cyan-500/30 px-4 py-1 rounded-full pointer-events-none z-10">
          <span className="text-cyan-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
        </div>
      )}
    </div>
  );
}