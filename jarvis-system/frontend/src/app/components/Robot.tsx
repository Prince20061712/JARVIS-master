import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF, useTexture, Environment, useFBX, useAnimations, OrthographicCamera } from "@react-three/drei";
import { Suspense, useEffect, useMemo } from "react";
import * as THREE from "three";
import { MeshStandardMaterial, LineBasicMaterial, MeshPhysicalMaterial, Vector2, SRGBColorSpace, LinearSRGBColorSpace } from "three";
import blinkData from "./blendDataBlink.json";

// Pre-load the model
useGLTF.preload("/model.glb");

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
}

// Animation helper function (adapted from converter.js)
function createAnimation(recordedData: any[], morphTargetDictionary: any, bodyPart: string) {
  if (recordedData.length !== 0) {
    let animation: any[] = [];
    for (let i = 0; i < Object.keys(morphTargetDictionary).length; i++) {
      animation.push([]);
    }
    let time: number[] = [];
    let finishedFrames = 0;
    const fps = 60;

    recordedData.forEach((d) => {
      Object.entries(d.blendshapes).forEach(([key, value]) => {
        let modifiedKey = key;
        if (modifiedKey.endsWith("Right")) modifiedKey = modifiedKey.replace("Right", "_R");
        if (modifiedKey.endsWith("Left")) modifiedKey = modifiedKey.replace("Left", "_L");

        if (!(modifiedKey in morphTargetDictionary)) return;

        // Type assertion for value as it's coming from JSON
        animation[morphTargetDictionary[modifiedKey]].push(value as number);
      });
      time.push(finishedFrames / fps);
      finishedFrames++;
    });

    let tracks: any[] = [];

    Object.entries(recordedData[0].blendshapes).forEach(([key]) => {
      let modifiedKey = key;
      if (modifiedKey.endsWith("Right")) modifiedKey = modifiedKey.replace("Right", "_R");
      if (modifiedKey.endsWith("Left")) modifiedKey = modifiedKey.replace("Left", "_L");

      if (!(modifiedKey in morphTargetDictionary)) return;

      let i = morphTargetDictionary[modifiedKey];
      let track = new THREE.NumberKeyframeTrack(`${bodyPart}.morphTargetInfluences[${i}]`, time, animation[i]);
      tracks.push(track);
    });

    const clip = new THREE.AnimationClip('animation', -1, tracks);
    return clip;
  }
  return null;
}

function AvatarModel({ state, voiceLevel = 0 }: { state: RobotState; voiceLevel?: number }) {
  const gltf = useGLTF("/model.glb");
  const mixer = useMemo(() => new THREE.AnimationMixer(gltf.scene), [gltf.scene]);

  // Load textures
  const [
    bodyTexture, eyesTexture, teethTexture, bodySpecularTexture, bodyRoughnessTexture,
    bodyNormalTexture, teethNormalTexture, hairTexture, tshirtDiffuseTexture,
    tshirtNormalTexture, tshirtRoughnessTexture, hairAlphaTexture, hairNormalTexture,
    hairRoughnessTexture
  ] = useTexture([
    "/images/body.webp", "/images/eyes.webp", "/images/teeth_diffuse.webp", "/images/body_specular.webp",
    "/images/body_roughness.webp", "/images/body_normal.webp", "/images/teeth_normal.webp", "/images/h_color.webp",
    "/images/tshirt_diffuse.webp", "/images/tshirt_normal.webp", "/images/tshirt_roughness.webp",
    "/images/h_alpha.webp", "/images/h_normal.webp", "/images/h_roughness.webp",
  ]);

  // Configure textures
  useEffect(() => {
    [bodyTexture, eyesTexture, teethTexture, teethNormalTexture, bodySpecularTexture,
      bodyRoughnessTexture, bodyNormalTexture, tshirtDiffuseTexture, tshirtNormalTexture,
      tshirtRoughnessTexture, hairAlphaTexture, hairNormalTexture, hairRoughnessTexture].forEach(t => {
        t.colorSpace = SRGBColorSpace;
        t.flipY = false;
      });

    bodyNormalTexture.colorSpace = LinearSRGBColorSpace;
    tshirtNormalTexture.colorSpace = LinearSRGBColorSpace;
    teethNormalTexture.colorSpace = LinearSRGBColorSpace;
    hairNormalTexture.colorSpace = LinearSRGBColorSpace;
  }, [bodyTexture, eyesTexture, teethTexture, teethNormalTexture, bodySpecularTexture,
    bodyRoughnessTexture, bodyNormalTexture, tshirtDiffuseTexture, tshirtNormalTexture,
    tshirtRoughnessTexture, hairAlphaTexture, hairNormalTexture, hairRoughnessTexture]);

  // Configure materials
  useEffect(() => {
    gltf.scene.traverse((node: any) => {
      if (node.type === 'Mesh' || node.type === 'LineSegments' || node.type === 'SkinnedMesh') {
        node.castShadow = true;
        node.receiveShadow = true;
        node.frustumCulled = false;

        if (node.name.includes("Body")) {
          node.material = new MeshPhysicalMaterial();
          node.material.map = bodyTexture;
          node.material.roughness = 1.7;
          node.material.roughnessMap = bodyRoughnessTexture;
          node.material.normalMap = bodyNormalTexture;
          node.material.normalScale = new Vector2(0.6, 0.6);
          node.material.envMapIntensity = 0.8;
        }

        if (node.name.includes("Eyes")) {
          node.material = new MeshStandardMaterial();
          node.material.map = eyesTexture;
          node.material.roughness = 0.1;
          node.material.envMapIntensity = 0.5;
        }

        if (node.name.includes("Brows")) {
          node.material = new LineBasicMaterial({ color: 0x000000 });
          node.material.linewidth = 1;
          node.material.opacity = 0.5;
          node.material.transparent = true;
          node.visible = false;
        }

        if (node.name.includes("Teeth")) {
          node.material = new MeshStandardMaterial();
          node.material.roughness = 0.1;
          node.material.map = teethTexture;
          node.material.normalMap = teethNormalTexture;
          node.material.envMapIntensity = 0.7;
        }

        if (node.name.includes("Hair")) {
          node.material = new MeshStandardMaterial();
          node.material.map = hairTexture;
          node.material.alphaMap = hairAlphaTexture;
          node.material.normalMap = hairNormalTexture;
          node.material.roughnessMap = hairRoughnessTexture;
          node.material.transparent = true;
          node.material.depthWrite = false;
          node.material.side = 2; // DoubleSide
          node.material.color.setHex(0x000000);
          node.material.envMapIntensity = 0.3;
        }

        if (node.name.includes("TSHIRT")) {
          node.material = new MeshStandardMaterial();
          node.material.map = tshirtDiffuseTexture;
          node.material.roughnessMap = tshirtRoughnessTexture;
          node.material.normalMap = tshirtNormalTexture;
          node.material.color.setHex(0xffffff);
          node.material.envMapIntensity = 0.5;
        }
      }
    });
  }, [gltf.scene, bodyTexture, bodyRoughnessTexture, bodyNormalTexture, eyesTexture, teethTexture, teethNormalTexture, hairTexture, hairAlphaTexture, hairNormalTexture, hairRoughnessTexture, tshirtDiffuseTexture, tshirtRoughnessTexture, tshirtNormalTexture]);

  // Handle Idle Animation
  const idleFbx = useFBX('/idle.fbx');
  const { clips: idleClips } = useAnimations(idleFbx.animations);

  useEffect(() => {
    if (idleClips && idleClips.length > 0) {
      // Filter tracks for idle animation to only affect head/neck/spine
      idleClips[0].tracks = idleClips[0].tracks.filter((track) => {
        return track.name.includes("Head") || track.name.includes("Neck") || track.name.includes("Spine2");
      });

      idleClips[0].tracks = idleClips[0].tracks.map((track) => {
        if (track.name.includes("Head")) track.name = "head.quaternion";
        if (track.name.includes("Neck")) track.name = "neck.quaternion";
        if (track.name.includes("Spine")) track.name = "spine2.quaternion";
        return track;
      });

      const idleClipAction = mixer.clipAction(idleClips[0]);
      idleClipAction.play();

      // Blink Animation
      const bodyNode: any = gltf.scene.children.find((child: any) => child.name.includes("Body"));
      if (bodyNode && bodyNode.morphTargetDictionary) {
        const blinkClip = createAnimation(blinkData, bodyNode.morphTargetDictionary, 'HG_Body');
        if (blinkClip) {
          const blinkAction = mixer.clipAction(blinkClip);
          blinkAction.play();
        }
      }
    }

    return () => {
      mixer.stopAllAction();
    };
  }, [mixer, idleClips, gltf.scene]);

  // Handle Volume-based Lip Sync
  useFrame((stateThree, delta) => {
    mixer.update(delta);

    // Volume-based jaw movement
    const teethNode: any = gltf.scene.getObjectByName("HG_TeethLower");
    const bodyNode: any = gltf.scene.getObjectByName("HG_Body");

    if (teethNode && teethNode.morphTargetDictionary && bodyNode && bodyNode.morphTargetDictionary) {
      const startTeethDict = teethNode.morphTargetDictionary as Record<string, number>;
      const startBodyDict = bodyNode.morphTargetDictionary as Record<string, number>;

      const jawOpenIndexTeeth = startTeethDict["jawOpen"];
      const jawOpenIndexBody = startBodyDict["jawOpen"];

      let currentVoiceLevel = voiceLevel;

      // Simulate voice level if acting speaking but no audio level provided
      if (state === 'speaking' && voiceLevel === 0) {
        // Create a pseudo-random speech pattern
        // Combined sine waves for smooth but irregular motion
        const time = stateThree.clock.elapsedTime;
        // Base rhythm + faster variations
        currentVoiceLevel = (Math.sin(time * 15) * 0.5 + 0.5) * (Math.sin(time * 5) * 0.5 + 0.5);
        // Add some noise for realism
        currentVoiceLevel = Math.max(0.1, currentVoiceLevel);
      }

      // Calculate mouth opening based on voice level
      const targetOpen = (state === 'speaking') ? Math.min(currentVoiceLevel * 1.2, 0.8) : 0;

      // Smoothly interpolate
      const currentTeeth = teethNode.morphTargetInfluences[jawOpenIndexTeeth];
      const newOpen = THREE.MathUtils.lerp(currentTeeth, targetOpen, 0.3); // Increased lerp speed for snappier movement

      teethNode.morphTargetInfluences[jawOpenIndexTeeth] = newOpen;
      bodyNode.morphTargetInfluences[jawOpenIndexBody] = newOpen;
    }
  });

  return (
    <group name="avatar" position={[0, -0.05, 0]} scale={0.95}>
      <primitive object={gltf.scene} dispose={null} />
    </group>
  );
}

export function Robot({ state, voiceLevel = 0 }: RobotProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full relative overflow-hidden bg-black/80">
      {/* Background glow effect */}
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-cyan-900/20 to-transparent pointer-events-none" />

      <div className="w-full h-full relative z-10">
        <Canvas
          dpr={2}
          style={{ height: "100%", width: "100%" }}
        >
          <OrthographicCamera
            makeDefault
            zoom={1500} // Zoomed in to face
            position={[0, 1.65, 1]}
          />

          <ambientLight intensity={1.5} />
          <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} />
          <pointLight position={[-10, -10, -10]} intensity={1} />

          <Suspense fallback={null}>
            <Environment preset="city" />
            <AvatarModel state={state} voiceLevel={voiceLevel} />
          </Suspense>
        </Canvas>
      </div>

      {/* Processing Indicator Overlay */}
      {state === 'processing' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-64 h-64 border-2 border-cyan-400/20 rounded-full animate-pulse" />
        </div>
      )}

      {/* Listening Indicator */}
      {state === 'listening' && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-cyan-900/80 backdrop-blur border border-cyan-500/30 px-4 py-1 rounded-full pointer-events-none">
          <span className="text-cyan-300 text-sm font-mono tracking-widest animate-pulse">LISTENING...</span>
        </div>
      )}
    </div>
  );
}