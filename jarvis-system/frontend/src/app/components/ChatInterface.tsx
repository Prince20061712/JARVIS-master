import { motion, AnimatePresence } from "motion/react";
import { Send, Mic } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export interface Message {
  id: string;
  type: "user" | "ai" | "system";
  text: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  onMicClick: () => void;
  isListening: boolean;
}

export function ChatInterface({
  messages,
  onSendMessage,
  onMicClick,
  isListening,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-full bg-transparent">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.type === "user"
                ? "justify-end"
                : message.type === "system"
                  ? "justify-center"
                  : "justify-start"
                }`}
            >
              {message.type === "system" ? (
                <div className="text-sm italic text-center text-cyan-500/70" style={{ textShadow: "0 0 10px rgba(0, 229, 255, 0.3)" }}>
                  {message.text}
                </div>
              ) : (
                <div
                  className="max-w-[80%] px-4 py-3"
                  style={
                    message.type === "user"
                      ? {
                        color: "#FFFFFF",
                        textShadow: "0 0 10px rgba(0, 229, 255, 0.5)",
                        borderRight: "2px solid #00E5FF",
                        paddingRight: "15px",
                        background: "linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.1) 100%)",
                      }
                      : {
                        color: "#00E5FF",
                        textShadow: "0 0 10px rgba(0, 229, 255, 0.5)",
                        borderLeft: "2px solid #00E5FF",
                        paddingLeft: "15px",
                        background: "linear-gradient(90deg, rgba(0, 229, 255, 0.1) 0%, transparent 100%)",
                        fontFamily: "'Courier New', monospace", // Robotic feel
                        letterSpacing: "0.5px",
                      }
                  }
                >
                  <p className="text-sm md:text-base font-medium">{message.text}</p>
                  <div
                    className="text-[10px] mt-1 opacity-60"
                    style={{
                      color: "#00E5FF",
                      textAlign: message.type === "user" ? "right" : "left"
                    }}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 bg-transparent">
        <div className="flex gap-4 items-center">
          {/* Microphone Button - Floating Orb */}
          <motion.button
            type="button"
            onClick={onMicClick}
            className="w-12 h-12 rounded-full flex items-center justify-center backdrop-blur-sm"
            style={{
              background: isListening ? "rgba(255, 68, 68, 0.2)" : "rgba(0, 229, 255, 0.1)",
              border: isListening ? "1px solid #FF4444" : "1px solid #00E5FF",
              boxShadow: isListening
                ? "0 0 25px rgba(255, 68, 68, 0.5)"
                : "0 0 20px rgba(0, 229, 255, 0.3)",
            }}
            whileHover={{ scale: 1.1, boxShadow: "0 0 30px rgba(0, 229, 255, 0.6)" }}
            whileTap={{ scale: 0.95 }}
            animate={
              isListening
                ? {
                  scale: [1, 1.1, 1],
                  boxShadow: ["0 0 25px rgba(255, 68, 68, 0.5)", "0 0 40px rgba(255, 68, 68, 0.8)", "0 0 25px rgba(255, 68, 68, 0.5)"]
                }
                : {}
            }
            transition={{
              duration: 1.5,
              repeat: isListening ? Infinity : 0,
            }}
          >
            <Mic className="w-5 h-5" style={{ color: isListening ? "#FF4444" : "#00E5FF" }} />
          </motion.button>

          {/* Text Input - Floating Line */}
          <div className="flex-1 relative group">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Command Interface..."
              className="w-full h-12 px-6 bg-transparent outline-none transition-all duration-300"
              style={{
                color: "#00E5FF",
                borderBottom: "1px solid rgba(0, 229, 255, 0.3)",
                textShadow: "0 0 5px rgba(0, 229, 255, 0.3)",
                fontFamily: "monospace",
              }}
            />
            {/* Animated Bottom Line */}
            <div className="absolute bottom-0 left-0 w-0 h-[1px] bg-[#00E5FF] transition-all duration-500 group-hover:w-full shadow-[0_0_10px_#00E5FF]" />
          </div>

          {/* Send Button */}
          <motion.button
            type="submit"
            className="w-10 h-10 flex items-center justify-center opacity-70 hover:opacity-100"
            style={{
              color: "#00E5FF",
            }}
            whileHover={{ scale: 1.1, textShadow: "0 0 10px #00E5FF" }}
            whileTap={{ scale: 0.95 }}
            disabled={!input.trim()}
          >
            <Send className="w-6 h-6" />
          </motion.button>
        </div>
      </form>
    </div>
  );
}