import Spline from '@splinetool/react-spline';
import { useRef, useEffect, useState, useCallback } from 'react';
import { RobotFace } from './RobotFace';

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
  const splineRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 });

  // Mirror the Spline cursor-tracking so the face overlay stays aligned
  const handleMouseMove = useCallback((e: MouseEvent) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    // Scale factor ≈ how far the Spline head shifts in screen pixels per unit offset
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

  function onLoad(splineApp: any) {
    splineRef.current = splineApp;
    console.log("Spline scene loaded");

    // Remove background color
    if (splineApp.setBackgroundColor) {
      splineApp.setBackgroundColor('transparent');
    }

    // Set zoom to ensure full robot is visible - adjusted based on feedback
    if (splineApp.setZoom) {
      splineApp.setZoom(0.9); // Increased zoom for larger appearance
    }

    // Aggressively remove watermark from DOM
    setTimeout(() => {
      const watermark = document.querySelector('a[href^="https://spline.design"]');
      if (watermark) {
        (watermark as HTMLElement).style.display = 'none';
      }

      // Also check shadow roots if possible
      const shadows = document.querySelectorAll('*');
      shadows.forEach(el => {
        if (el.shadowRoot) {
          const wm = el.shadowRoot.querySelector('a[href^="https://spline.design"]');
          if (wm) (wm as HTMLElement).style.display = 'none';
        }
      });

      // Try by ID as well
      const wmId = document.getElementById('spline-watermark');
      if (wmId) wmId.style.display = 'none';
    }, 1000);

    // Attempt to find and hide text/logo objects
    try {
      // Common specific names
      const objectsToHide = ['Text', 'Neobot', 'NEOBOT', 'Title', 'Label', 'Watermark', 'Logo', 'Brand', 'Background', 'Scene'];

      objectsToHide.forEach(name => {
        const obj = splineApp.findObjectByName(name);
        if (obj) {
          console.log(`Hiding Spline object: ${name}`);
          obj.visible = false;
        }
      });

      // Also iterate all objects to catch others case-insensitively
      if (typeof splineApp.getAllObjects === 'function') {
        const allObjects = splineApp.getAllObjects();
        if (allObjects && Array.isArray(allObjects)) {
          allObjects.forEach((obj: any) => {
            const name = obj.name ? obj.name.toLowerCase() : '';
            const type = obj.type;

            if (name.includes('text') || name.includes('neobot') || name.includes('brand') || name.includes('logo') || name.includes('watermark')) {
              console.log(`Hiding object based on name: ${obj.name}`);
              obj.visible = false;
            }

            if (type === 'Text') {
              console.log(`Hiding object based on type: ${obj.name}`);
              obj.visible = false;
            }
          });
        }
      }
    } catch (e) {
      console.warn("Error iterating Spline objects:", e);
    }

  }

  // Trigger Spline events based on state
  useEffect(() => {
    if (splineRef.current) {
      try {
        // Map states to Spline events/variables if available in the scene
        // For now, we just load the scene which looks cool by default
        console.log(`[Robot] State changed to: ${state}`);

        // Example: If the scene has variables, we could set them:
        // splineRef.current.setVariable('state', state);
      } catch (e) {
        console.error("Error updating Spline state:", e);
      }
    }
  }, [state, emotion]);

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden rounded-[30px]">
      <Spline
        scene="https://prod.spline.design/Ge8D8rQPojoko8eQ/scene.splinecode"
        onLoad={onLoad}
        className="w-full h-full"
      />

      {/* Animated face overlay – tracks cursor just like the Spline head does */}
      <RobotFace state={state} emotion={emotion} mouseOffset={mouseOffset} />

      {/* Processing Indicator Overlay */}
      {state === 'processing' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="w-64 h-64 border-2 border-cyan-400/20 rounded-full animate-pulse" />
        </div>
      )}

      {/* Listening Indicator */}
      {state === 'listening' && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-yellow-900/80 backdrop-blur border border-yellow-500/30 px-4 py-1 rounded-full pointer-events-none z-10">
          <span className="text-yellow-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
        </div>
      )}
    </div>
  );
}