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

  // Initialize WebSocket
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
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

        // Clear any existing timeout before setting a new one
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
        // Remove onclose handler to prevent accidental reconnection trigger during cleanup
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
          // User message echoed back
          setMessages((prev) => [...prev, {
            id: Date.now().toString(),
            type: "user",
            text: data.content,
            timestamp: new Date(),
          }]);
        }
        // AI response handling moved to 'text' event for better sync
        break;

      case 'text':
        // Display AI text immediately
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
        // Optional: clear current message bubble after a delay?
        // setCurrentMessage(""); 
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
    // Check for admiration keywords
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
              backgroundColor: "#111", // Darker background for avatar
              borderColor: "rgba(0, 229, 255, 0.2)",
              backgroundImage: "radial-gradient(circle at center, #1a2c4e 0%, #000 100%)",
            }}
          >
            <Robot
              state={robotState}
              message={currentMessage}
              emotion={robotEmotion}
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

        {/* Footer Controls: REMOVED */}
      </div>
    </div>
  );
}