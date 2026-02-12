import { Canvas } from "@react-three/fiber";
import { useGLTF, OrbitControls, Environment } from "@react-three/drei";
import { Suspense, useEffect, useRef } from "react";
import * as THREE from "three";

// Pre-load the model
useGLTF.preload("https://models.readyplayer.me/698d662a773780b71b5dee00.glb");

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

function AvatarModel({ state, voiceLevel = 0 }: { state: RobotState; voiceLevel?: number }) {
  const { scene } = useGLTF("https://models.readyplayer.me/698d662a773780b71b5dee00.glb");
  const modelRef = useRef<THREE.Group>(null);

  useEffect(() => {
    if (modelRef.current) {
      // Reset position
      modelRef.current.position.y = -1.6;
    }
  }, []);

  // Simple animation using useFrame is better, but for now we can use simple react updates or just pass props.
  // Ideally we would access the bone structure for lip sync, but that requires more complex setup.
  // For now, let's just gently bob the head/body when speaking.

  const isSpeaking = state === 'speaking';

  // Rotate/Scale based on voice to simulate activity
  useEffect(() => {
    if (modelRef.current) {
      if (isSpeaking) {
        const scale = 1.2 + (voiceLevel * 0.05);
        modelRef.current.scale.setScalar(scale);
      } else {
        modelRef.current.scale.setScalar(1.2);
      }
    }
  }, [isSpeaking, voiceLevel]);

  return (
    <primitive
      object={scene}
      ref={modelRef}
      scale={1.2}
      position={[0, -1.8, 0]}
    />
  );
}

export function Robot({
  state,
  voiceLevel = 0
}: RobotProps) {

  return (
    <div className="flex flex-col items-center justify-center h-full w-full relative overflow-hidden bg-black/20">
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-t from-cyan-900/10 via-transparent to-transparent pointer-events-none" />

      <div className="w-full h-full relative z-10">
        <Canvas
          camera={{ position: [0, 0, 3], fov: 40 }} // Moved camera back to 3
          style={{ height: "100%", width: "100%" }}
        >
          <color attach="background" args={['#0a0a0a']} />
          <ambientLight intensity={1.5} />
          <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} />
          <pointLight position={[-10, -10, -10]} intensity={1} />
          <Environment preset="city" />

          <Suspense fallback={null}>
            <AvatarModel state={state} voiceLevel={voiceLevel} />
          </Suspense>

          <OrbitControls
            enableZoom={true}
            enablePan={false}
            minPolarAngle={Math.PI / 2.5}
            maxPolarAngle={Math.PI / 1.8}
            target={[0, 1.45, 0]} // Focus on face
          />
        </Canvas>
      </div>

      {/* Processing Indicator Overlay */}
      {state === 'processing' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-32 h-32 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
        </div>
      )}

      {/* Listening Indicator */}
      {state === 'listening' && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-cyan-900/80 backdrop-blur border border-cyan-500/30 px-4 py-1 rounded-full pointer-events-none">
          <span className="text-cyan-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
        </div>
      )}

      {/* Error Indicator */}
      {state === 'error' && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-red-900/80 backdrop-blur border border-red-500/30 px-4 py-1 rounded-full pointer-events-none">
          <span className="text-red-300 text-sm font-mono tracking-widest animate-pulse">SYSTEM ERROR</span>
        </div>
      )}
    </div>
  );
}