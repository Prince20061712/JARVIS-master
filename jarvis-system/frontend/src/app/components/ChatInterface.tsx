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
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{
        background: "linear-gradient(180deg, rgba(0, 26, 51, 0.3) 0%, rgba(10, 20, 40, 0.5) 100%)"
      }}>
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
                <div className="text-sm italic text-center" style={{ color: "#888888" }}>
                  {message.text}
                </div>
              ) : (
                <div
                  className="max-w-[80%] px-4 py-3 rounded-[15px]"
                  style={
                    message.type === "user"
                      ? {
                        background: "linear-gradient(135deg, #00E5FF 0%, #0088CC 100%)",
                        color: "#000000",
                        borderRadius: "15px 15px 2px 15px",
                        boxShadow: "0 0 20px rgba(0, 229, 255, 0.4), 0 4px 10px rgba(0, 0, 0, 0.3)",
                        border: "1px solid rgba(255, 255, 255, 0.2)",
                      }
                      : {
                        background: "linear-gradient(135deg, rgba(0, 100, 200, 0.3) 0%, rgba(0, 50, 100, 0.3) 100%)",
                        color: "#FFFFFF",
                        border: "1px solid rgba(0, 229, 255, 0.5)",
                        borderRadius: "15px 15px 15px 2px",
                        boxShadow: "0 0 15px rgba(0, 229, 255, 0.3), 0 4px 10px rgba(0, 0, 0, 0.3)",
                        backdropFilter: "blur(10px)",
                      }
                  }
                >
                  <p className="text-sm">{message.text}</p>
                  <div
                    className="text-[10px] mt-1"
                    style={{
                      color: message.type === "user" ? "#000000" : "#888888",
                      opacity: 0.7,
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
      <form onSubmit={handleSubmit} className="p-4 border-t" style={{
        borderColor: "rgba(0, 229, 255, 0.3)",
        backgroundColor: "rgba(10, 20, 50, 0.6)",
      }}>
        <div className="flex gap-2 items-center">
          {/* Microphone Button */}
          <motion.button
            type="button"
            onClick={onMicClick}
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: isListening ? "#FF4444" : "#00E5FF",
              boxShadow: isListening
                ? "0 0 25px rgba(255, 68, 68, 0.8)"
                : "0 0 20px rgba(0, 229, 255, 0.6)",
            }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            animate={
              isListening
                ? {
                  scale: [1, 1.1, 1],
                }
                : {}
            }
            transition={{
              duration: 0.5,
              repeat: isListening ? Infinity : 0,
            }}
          >
            <Mic className="w-5 h-5" style={{ color: "#000000" }} />
          </motion.button>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 h-12 px-4 rounded-[25px] outline-none"
            style={{
              backgroundColor: "rgba(0, 50, 100, 0.4)",
              color: "#FFFFFF",
              border: "1px solid rgba(0, 229, 255, 0.5)",
              boxShadow: "inset 0 2px 10px rgba(0, 0, 0, 0.3)",
            }}
          />

          {/* Send Button */}
          <motion.button
            type="submit"
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: "#00E5FF",
              boxShadow: "0 0 20px rgba(0, 229, 255, 0.6)",
            }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            disabled={!input.trim()}
          >
            <Send className="w-5 h-5" style={{ color: "#000000" }} />
          </motion.button>
        </div>
      </form>
    </div>
  );
}