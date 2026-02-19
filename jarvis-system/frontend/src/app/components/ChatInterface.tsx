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
                <div className="text-sm italic text-center text-white/50">
                  {message.text}
                </div>
              ) : (
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl backdrop-blur-md shadow-lg border ${message.type === "user"
                      ? "bg-white/20 border-white/30 text-white rounded-br-sm"
                      : "bg-black/40 border-white/10 text-white/90 rounded-bl-sm"
                    }`}
                >
                  <p className="text-sm md:text-base font-medium leading-relaxed">{message.text}</p>
                  <div
                    className={`text-[10px] mt-1 opacity-50 ${message.type === "user" ? "text-right" : "text-left"
                      }`}
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
      <form onSubmit={handleSubmit} className="p-4 bg-transparent mt-2 border-t border-white/10">
        <div className="flex gap-3 items-center">
          {/* Microphone Button - Glassy */}
          <motion.button
            type="button"
            onClick={onMicClick}
            className={`w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md transition-all ${isListening
                ? "bg-red-500/20 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
              } border`}
            whileTap={{ scale: 0.95 }}
          >
            <Mic className={`w-5 h-5 ${isListening ? "text-red-400" : "text-white/70"}`} />
          </motion.button>

          {/* Text Input - Glassy Pill */}
          <div className="flex-1 relative group">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message..."
              className="w-full h-10 px-4 bg-white/5 border border-white/10 rounded-full text-white/90 placeholder-white/40 focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all backdrop-blur-md shadow-inner"
            />
          </div>

          {/* Send Button */}
          <motion.button
            type="submit"
            className={`w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md border border-white/10 transition-all ${!input.trim() ? "opacity-50 bg-white/5 cursor-not-allowed" : "bg-white/10 hover:bg-white/20 hover:border-white/30 shadow-lg"
              }`}
            whileTap={input.trim() ? { scale: 0.95 } : {}}
            disabled={!input.trim()}
          >
            <Send className="w-4 h-4 text-white/90" />
          </motion.button>
        </div>
      </form>
    </div>
  );
}