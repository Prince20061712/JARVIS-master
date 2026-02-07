import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "motion/react";
import { Bot, Music, RotateCcw } from "lucide-react";
import { Robot, RobotState } from "./components/Robot";
import {
  ChatInterface,
  Message,
} from "./components/ChatInterface";
import { StatusLED } from "./components/StatusLED";

export default function App() {
  const [robotState, setRobotState] = useState<RobotState>("idle");
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
  const speechQueue = useRef<string[]>([]);
  const isTalking = useRef(false);
  const synth = window.speechSynthesis;
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  // Initialize Voices
  useEffect(() => {
    const loadVoices = () => {
      setVoices(synth.getVoices());
    };
    loadVoices();
    if (synth.onvoiceschanged !== undefined) {
      synth.onvoiceschanged = loadVoices;
    }
  }, [synth]);

  // Initialize WebSocket
  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Adjust port if running on dev server (frontend 5173 -> backend 8000)
      const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/ws`;

      console.log("Connecting to WebSocket:", wsUrl);
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setIsConnected(true);
        addSystemMessage("Connected to JARVIS core.");
        setRobotState("idle");
      };

      socket.onclose = () => {
        setIsConnected(false);
        addSystemMessage("Connection lost. Reconnecting in 3s...");
        setRobotState("error");
        setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setRobotState("error");
      };

      socket.onmessage = (event) => {
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
      if (socketRef.current) {
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

  const handleBackendMessage = (data: any) => {
    if (data.type === 'response') {
      if (data.sender === 'user') {
        // User message echoed back
        setMessages((prev) => [...prev, {
          id: Date.now().toString(),
          type: "user",
          text: data.content,
          timestamp: new Date(),
        }]);
      } else {
        // AI response
        setMessages((prev) => [...prev, {
          id: Date.now().toString(),
          type: "ai",
          text: data.content,
          timestamp: new Date(),
        }]);
        // Make robot speak
        if (data.content && !data.content.startsWith('(')) {
          robotSpeak(data.content);
        }
      }
    } else if (data.type === 'voice_status') {
      setIsListening(data.listening);
      setRobotState(data.listening ? "listening" : "idle");
    } else if (data.type === 'processing') {
      setRobotState("processing");
    } else if (data.type === 'error') {
      robotSpeak("Error: " + data.message);
      setRobotState("error");
      setTimeout(() => setRobotState("idle"), 3000);
    }
  };

  const robotSpeak = (text: string) => {
    if (!text || isTalking.current) {
      speechQueue.current.push(text);
      return;
    }

    isTalking.current = true;
    setRobotState("speaking");
    setCurrentMessage(text);

    // Notify backend that speech has started
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'speech_state',
        status: 'started'
      }));
    }

    if (synth.speaking) {
      synth.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Voice Selection (Daniel Priority)
    if (voices.length > 0) {
      let preferredVoice = voices.find(v => v.name.includes('Daniel'));
      if (!preferredVoice) {
        preferredVoice = voices.find(v => v.name.includes('UK English Male') || v.name.includes('Google UK English Male'));
      }
      if (!preferredVoice) {
        preferredVoice = voices.find(v => v.lang === 'en-GB' && v.name.includes('Male'));
      }
      if (!preferredVoice) {
        preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Microsoft'));
      }

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
    }

    utterance.onend = () => {
      finishSpeaking();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      finishSpeaking();
    };

    synth.speak(utterance);
  };

  const finishSpeaking = () => {
    isTalking.current = false;
    setRobotState("idle");
    setCurrentMessage(""); // Clear message bubble

    // Notify backend that speech has finished
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'speech_state',
        status: 'finished'
      }));
    }

    // Process queue
    if (speechQueue.current.length > 0) {
      const nextText = speechQueue.current.shift();
      if (nextText) setTimeout(() => robotSpeak(nextText), 500);
    }
  };

  const handleSendMessage = (text: string) => {
    if (isConnected && socketRef.current) {
      setRobotState("processing");
      socketRef.current.send(JSON.stringify({
        type: 'command',
        content: text
      }));
      // Optimistically add user message? No, wait for echo to confirm persistence/order
    }
  };

  const handleMicClick = () => {
    if (isConnected && socketRef.current) {
      socketRef.current.send(JSON.stringify({
        type: 'toggle_voice'
      }));
    }
  };

  const handleTalkClick = () => {
    robotSpeak("Systems operational. Ready for commands.");
  };

  const handleDanceClick = () => {
    setRobotState("dancing");
    robotSpeak("Initiating dance protocol.");
    setTimeout(() => {
      setRobotState("idle");
    }, 5000);
  };

  const handleResetClick = () => {
    setRobotState("idle");
    setCurrentMessage("");
    setIsListening(false);
    if (synth.speaking) synth.cancel();
    speechQueue.current = [];
    isTalking.current = false;
    addSystemMessage("Interface reset.");
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: "linear-gradient(135deg, #001a33 0%, #000a1a 100%)",
      }}
    >
      <div
        className="w-full max-w-[1400px] h-[900px] rounded-[15px] overflow-hidden flex flex-col"
        style={{
          backgroundColor: "#0a1428",
          boxShadow: "0 0 60px rgba(0, 229, 255, 0.4)",
          border: "1px solid rgba(0, 229, 255, 0.2)",
        }}
      >
        {/* Header */}
        <div
          className="h-16 px-6 flex items-center justify-between border-b shrink-0"
          style={{
            backgroundColor: "rgba(10, 20, 50, 0.8)",
            borderColor: "rgba(0, 229, 255, 0.3)",
            boxShadow: "0 4px 20px rgba(0, 229, 255, 0.2)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="text-2xl font-light tracking-[3px]"
              style={{ color: "#00E5FF" }}
            >
              J.A.R.V.I.S
            </div>
            <div
              className="text-xs"
              style={{ color: "#888888" }}
            >
              Virtual Assistant Interface
            </div>
          </div>

          {/* Status LEDs */}
          <div className="flex gap-6">
            <StatusLED
              color="#00E5FF"
              active={isConnected}
              label="Online"
            />
            <StatusLED
              color="#00FF00"
              active={robotState === "processing"}
              label="Processing"
            />
            <StatusLED
              color="#FF4444"
              active={robotState === "error"}
              label="Error"
            />
          </div>
        </div>

        {/* Main Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Robot Interface - 60% */}
          <div
            className="w-[60%] border-r relative flex flex-col justify-center"
            style={{
              backgroundColor: "#0a1428",
              borderColor: "rgba(0, 229, 255, 0.2)",
              background:
                "linear-gradient(135deg, #001a33 0%, #0a1428 100%)",
            }}
          >
            <Robot
              state={robotState}
              message={currentMessage}
            />
          </div>

          {/* Chat Interface - 40% */}
          <div
            className="w-[40%] h-full"
            style={{
              backgroundColor: "#0a1428",
              background:
                "linear-gradient(135deg, #0a1428 0%, #001a33 100%)",
            }}
          >
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              onMicClick={handleMicClick}
              isListening={isListening}
            />
          </div>
        </div>

        {/* Footer Controls */}
        <div
          className="h-16 px-6 flex items-center justify-center gap-4 border-t shrink-0"
          style={{
            backgroundColor: "rgba(10, 20, 50, 0.8)",
            borderColor: "rgba(0, 229, 255, 0.3)",
            boxShadow: "0 -4px 20px rgba(0, 229, 255, 0.2)",
          }}
        >
          <ControlButton
            icon={<Bot className="w-5 h-5" />}
            label="Talk"
            onClick={handleTalkClick}
          />
          <ControlButton
            icon={<Music className="w-5 h-5" />}
            label="Dance"
            onClick={handleDanceClick}
          />
          <ControlButton
            icon={<RotateCcw className="w-5 h-5" />}
            label="Reset"
            onClick={handleResetClick}
          />
        </div>
      </div>
    </div>
  );
}

interface ControlButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

function ControlButton({
  icon,
  label,
  onClick,
}: ControlButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      className="flex items-center gap-2 px-6 py-2 rounded-lg"
      style={{
        backgroundColor: "rgba(0, 50, 100, 0.4)",
        border: "1px solid rgba(0, 229, 255, 0.6)",
        color: "#00E5FF",
        boxShadow: "0 0 15px rgba(0, 229, 255, 0.3)",
      }}
      whileHover={{
        scale: 1.05,
        boxShadow: "0 0 30px rgba(0, 229, 255, 0.6)",
        backgroundColor: "rgba(0, 100, 200, 0.5)",
      }}
      whileTap={{ scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      {icon}
      <span className="text-sm font-medium uppercase tracking-wider">
        {label}
      </span>
    </motion.button>
  );
}