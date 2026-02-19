import { useState, useEffect, useRef } from "react";
import { Robot, RobotState } from "./components/Robot";
import {
  ChatInterface,
  Message,
} from "./components/ChatInterface";
import { StatusLED } from "./components/StatusLED";

export default function App() {
  const [robotState, setRobotState] = useState<RobotState>("idle");
  const [robotEmotion, setRobotEmotion] = useState<'neutral' | 'shy'>('neutral');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "system",
      text: "J.A.R.V.I.S Interface Initialized",
      timestamp: new Date(),
    }
  ]);
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/ws`;

      console.log("Connecting to WebSocket:", wsUrl);
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        if (!isMounted) {
          socket.close();
          return;
        }
        setIsConnected(true);
        addSystemMessage("Connected to JARVIS core.");
        setRobotState("idle");
      };

      socket.onclose = () => {
        if (!isMounted) return;

        setIsConnected(false);
        addSystemMessage("Connection lost. Reconnecting in 3s...");
        setRobotState("error");

        clearTimeout(reconnectTimeout);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = (error) => {
        if (!isMounted) return;
        console.error('WebSocket Error:', error);
        setRobotState("error");
      };

      socket.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data = JSON.parse(event.data);
          handleBackendMessage(data);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      socketRef.current = socket;
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, []);

  const addSystemMessage = (text: string) => {
    setMessages((prev) => [...prev, {
      id: Date.now().toString(),
      type: "system",
      text,
      timestamp: new Date(),
    }]);
  };

  const addAiMessage = (text: string) => {
    setMessages((prev) => {
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.type === 'ai' && lastMsg.text === text) {
        return prev;
      }
      return [...prev, {
        id: Date.now().toString(),
        type: "ai",
        text: text,
        timestamp: new Date(),
      }];
    });
  };

  // Handle Backend Messages
  const handleBackendMessage = (data: any) => {
    console.log("Received backend message:", data);

    switch (data.type) {
      case 'response':
        if (data.sender === 'user') {
          setMessages((prev) => [...prev, {
            id: Date.now().toString(),
            type: "user",
            text: data.content,
            timestamp: new Date(),
          }]);
        }
        break;

      case 'text':
        if (data.text) {
          addAiMessage(data.text);
          setCurrentMessage(data.text);
        }
        break;

      case 'lipsync_start':
        console.log("[App] Received lipsync_start, setting state to speaking");
        setRobotState("speaking");
        break;

      case 'lipsync_stop':
        console.log("[App] Received lipsync_stop, setting state to idle");
        setRobotState("idle");
        setRobotEmotion("neutral");
        break;

      case 'voice_status':
        setIsListening(data.listening);
        setRobotState(data.listening ? "listening" : "idle");
        break;

      case 'processing':
        setRobotState("processing");
        break;

      case 'error':
        addSystemMessage("Error: " + data.message);
        setRobotState("error");
        setTimeout(() => setRobotState("idle"), 3000);
        break;

      default:
        console.log("Unhandled message type:", data.type);
    }
  };

  const handleSendMessage = (text: string) => {
    const lowerText = text.toLowerCase();
    if (
      lowerText.includes('good work') ||
      lowerText.includes('thank you') ||
      lowerText.includes('great job') ||
      lowerText.includes('well done') ||
      lowerText.includes('nice work')
    ) {
      setRobotEmotion('shy');
    } else {
      setRobotEmotion('neutral');
    }

    if (isConnected && socketRef.current) {
      setRobotState("processing");
      socketRef.current.send(JSON.stringify({
        type: 'command',
        content: text
      }));
    }
  };

  const handleMicClick = () => {
    if (isConnected && socketRef.current) {
      socketRef.current.send(JSON.stringify({
        type: 'toggle_voice'
      }));
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Dynamic Live Wallpaper */}
      {/* Dynamic Live Wallpaper */}
      <div className="fixed inset-0 z-0 bg-[#050505]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(25,25,25,1)_0%,rgba(5,5,5,1)_100%)] animate-pulse-slow">
          {/* Glossy overlay */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent opacity-20 transform rotate-12 scale-150 animate-gloss-slide"></div>
        </div>

        {/* Animated Particles - Subtle Dust */}
        <div className="absolute inset-0">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-white/10 animate-float"
              style={{
                width: Math.random() * 3 + 1 + 'px',
                height: Math.random() * 3 + 1 + 'px',
                left: Math.random() * 100 + '%',
                top: Math.random() * 100 + '%',
                animationDelay: Math.random() * 5 + 's',
                animationDuration: Math.random() * 20 + 20 + 's',
                opacity: Math.random() * 0.5 + 0.1,
              }}
            />
          ))}
        </div>

        {/* Grid Overlay - Faint Tech Grid */}
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          transform: 'perspective(500px) rotateX(60deg)',
          transformOrigin: 'top',
          opacity: 0.2,
          maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)'
        }} />

        {/* Animated Light Beams - Subtle Scan lines */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="absolute w-full h-full animate-scan"
              style={{
                background: `linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.02), transparent)`,
                left: `${i * 30}%`,
                animationDelay: `${i * 4}s`,
                animationDuration: '15s'
              }}
            />
          ))}
        </div>
      </div>

      {/* Floating Robot Interface */}
      {/* Floating Robot Interface - Positioned at bottom */}
      <div className="absolute bottom-[-50px] left-1/2 transform -translate-x-1/2 w-[500px] h-[500px] md:w-[900px] md:h-[900px] flex items-end justify-center pointer-events-auto">
        <Robot
          state={robotState}
          message={currentMessage}
          emotion={robotEmotion}
        />

        {/* Status LEDs overlay */}
        <div className="absolute top-4 right-4 flex gap-3">
          <StatusLED
            color="#00E5FF"
            active={isConnected}
            label=""
            size="sm"
          />
          <StatusLED
            color="#00FF00"
            active={robotState === "processing"}
            label=""
            size="sm"
          />
          <StatusLED
            color="#FF4444"
            active={robotState === "error"}
            label=""
            size="sm"
          />
        </div>
      </div>

      {/* Floating Chat Interface - Positioned at bottom right */}
      <div className="fixed bottom-8 right-8 z-20 w-[400px] h-[500px] pointer-events-auto">
        <div className="h-full rounded-3xl overflow-hidden bg-black/20 backdrop-blur-3xl border border-white/10 shadow-2xl flex flex-col">
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            onMicClick={handleMicClick}
            isListening={isListening}
          />
        </div>
      </div>

      {/* Optional: Floating Status Bar at top */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-20">
        <div className="backdrop-blur-xl px-6 py-2 rounded-full border border-white/10 bg-white/5 shadow-lg">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-white/80 font-medium tracking-wide">J.A.R.V.I.S</span>
            <span className="text-white/20">|</span>
            <span className={`text-xs font-semibold tracking-wider ${isConnected ? 'text-green-400/90' : 'text-red-400/90'}`}>
              {isConnected ? '● ONLINE' : '○ OFFLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* Custom CSS Animations */}
      <style>{`
        @keyframes gloss-slide {
          0% { background-position: 0% 50%; opacity: 0.1; }
          50% { background-position: 100% 50%; opacity: 0.2; }
          100% { background-position: 0% 50%; opacity: 0.1; }
        }
        
        .animate-gloss-slide {
          background-size: 200% 200%;
          animation: gloss-slide 10s ease-in-out infinite;
        }

        @keyframes pulse-slow {
          0%, 100% { opacity: 0.8; }
          50% { opacity: 1; }
        }

        .animate-pulse-slow {
          animation: pulse-slow 8s ease-in-out infinite;
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          25% { transform: translateY(-20px) translateX(10px); }
          50% { transform: translateY(-30px) translateX(-10px); }
          75% { transform: translateY(-10px) translateX(20px); }
        }
        
        .animate-float {
          animation: float 20s ease-in-out infinite;
        }
        
        @keyframes scan {
          0% { transform: translateX(-100%) rotate(0deg); opacity: 0; }
          20% { opacity: 1; }
          80% { opacity: 1; }
          100% { transform: translateX(200%) rotate(0deg); opacity: 0; }
        }
        
        .animate-scan {
          animation: scan 15s linear infinite;
        }
      `}</style>
    </div>
  );
}