import { motion, AnimatePresence } from "motion/react";
import { Send, Mic, ChevronDown, Hash, Loader2, Square } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export interface Message {
  id: string;
  type: "user" | "ai" | "system";
  text: string;
  timestamp: Date;
  marks?: number;
  subject?: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (text: string, marks: number | null, subject: string) => void;
  onMicClick: () => void;
  onStopClick: () => void;
  onSubjectChange?: (subject: string) => void;
  activeSubject: string;
  isListening: boolean;
  isProcessing?: boolean;
  isSpeaking?: boolean;
}

const MARKS_OPTIONS = [0, 2, 5, 10, 15];

function formatMarkdownLike(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\$\$(.*?)\$\$/gs, '<code class="math">$1</code>')
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/\n/g, '<br/>');
}

export function ChatInterface({ messages, onSendMessage, onMicClick, onStopClick, onSubjectChange, activeSubject, isListening, isProcessing, isSpeaking }: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const [marks, setMarks] = useState<number>(0);
  const [showMarks, setShowMarks] = useState(false);
  const [showSubject, setShowSubject] = useState(false);
  const [flashcards, setFlashcards] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  useEffect(() => {
    // Fetch flashcards to populate the subject dropdown
    const fetchFlashcards = async () => {
      try {
        const protocol = window.location.protocol;
        const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
        const res = await fetch(`${protocol}//${host}/api/local-flashcards`);
        if (res.ok) {
          const data = await res.json();
          setFlashcards(["General", ...(data.flashcards || [])]);
        }
      } catch (e) {
        console.error("Failed to fetch flashcards", e);
        setFlashcards(["General"]);
      }
    };
    fetchFlashcards();
    // Poll for updates every 1 minute instead of 5 seconds to reduce battery drain
    const intervalId = setInterval(fetchFlashcards, 60000);
    return () => clearInterval(intervalId);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input, marks || null, activeSubject);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-full bg-transparent">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.type === "user" ? "justify-end" : message.type === "system" ? "justify-center" : "justify-start"}`}
            >
              {message.type === "system" ? (
                <div className="text-[11px] italic text-center text-white/30 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  {message.text}
                </div>
              ) : (
                <div className="w-full">
                  {message.type === "ai" && (message.marks || message.subject !== "General") && (
                    <div className="flex gap-1.5 mb-1.5 ml-1">
                      {message.subject && message.subject !== "General" && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{message.subject}</span>
                      )}
                      {message.marks && message.marks > 0 ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">{message.marks} marks</span>
                      ) : null}
                    </div>
                  )}
                  <div
                    className={`max-w-[88%] px-4 py-3 rounded-2xl backdrop-blur-md shadow-lg border text-sm leading-relaxed ${message.type === "user"
                      ? "ml-auto bg-white/15 border-white/25 text-white rounded-br-sm"
                      : "bg-black/40 border-white/10 text-white/90 rounded-bl-sm"
                      }`}
                    dangerouslySetInnerHTML={{ __html: formatMarkdownLike(message.text) }}
                  />
                  <div className={`text-[10px] mt-1.5 px-1 font-medium text-white/40 ${message.type === "user" ? "text-right" : "text-left"}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-black/40 border-white/10 text-white/50 px-4 py-3 rounded-2xl rounded-bl-sm backdrop-blur-md border text-xs flex items-center gap-3">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                <span className="tracking-wide">JARVIS is thinking...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Academic Controls */}
      <div className="px-4 pt-3 border-t border-white/10">
        <div className="flex gap-2 mb-3">
          {/* Subject Selector (Flashcards) */}
          <div className="relative">
            <button
              onClick={() => { setShowSubject(s => !s); setShowMarks(false); }}
              className="h-7 px-3 rounded-full text-[11px] font-medium border border-white/10 bg-white/5 text-white/60 hover:bg-white/10 hover:text-white/90 transition-all flex items-center gap-1"
              title="Select a Flashcard Subject"
            >
              {activeSubject} <ChevronDown className="w-3 h-3" />
            </button>
            <AnimatePresence>
              {showSubject && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                  className="absolute bottom-9 left-0 z-50 bg-black/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-xl min-w-[140px]"
                >
                  {flashcards.map(s => (
                    <button key={s} onClick={() => { 
                      setShowSubject(false); 
                      onSubjectChange?.(s);
                    }}
                      className={`w-full text-left px-3 py-2 text-[11px] hover:bg-white/10 transition-colors ${activeSubject === s ? "text-cyan-400 bg-cyan-500/10" : "text-white/70"}`}
                    >
                      {s === "General" ? "General Conversation" : s}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Marks Selector */}
          <div className="relative">
            <button
              onClick={() => { setShowMarks(m => !m); setShowSubject(false); }}
              className="h-7 px-3 rounded-full text-[11px] font-medium border border-white/10 bg-white/5 text-white/60 hover:bg-white/10 hover:text-white/90 transition-all flex items-center gap-1"
            >
              <Hash className="w-3 h-3" />
              {marks > 0 ? `${marks}m` : "Marks"} <ChevronDown className="w-3 h-3" />
            </button>
            <AnimatePresence>
              {showMarks && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                  className="absolute bottom-9 left-0 z-50 bg-black/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-xl"
                >
                  {MARKS_OPTIONS.map(m => (
                    <button key={m} onClick={() => { setMarks(m); setShowMarks(false); }}
                      className={`w-full text-left px-4 py-2 text-[11px] hover:bg-white/10 transition-colors ${marks === m ? "text-purple-400 bg-purple-500/10" : "text-white/70"}`}
                    >{m === 0 ? "Any" : `${m} marks`}</button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2 items-center pb-4">
          <motion.button
            type="button"
            onClick={onMicClick}
            className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border transition-all ${isListening
              ? "bg-red-500/20 border-red-500/50 shadow-[0_0_12px_rgba(239,68,68,0.3)]"
              : "bg-white/5 border-white/10 hover:bg-white/10"
              }`}
            whileTap={{ scale: 0.92 }}
          >
            <Mic className={`w-4 h-4 ${isListening ? "text-red-400 animate-pulse" : "text-white/60"}`} />
          </motion.button>
          
          <AnimatePresence>
            {(isProcessing || isSpeaking || isListening) && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="button"
                onClick={onStopClick}
                className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border transition-all bg-red-500/20 border-red-500/50 hover:bg-red-500/30 text-red-500"
                whileTap={{ scale: 0.92 }}
                title="Stop JARVIS"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </motion.button>
            )}
          </AnimatePresence>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask about ${activeSubject !== "General" ? activeSubject : "Engineering"}${marks > 0 ? ` (${marks} marks)` : ""}…`}
            className="flex-1 h-9 px-4 bg-white/5 border border-white/10 rounded-full text-white/90 placeholder-white/30 text-sm focus:outline-none focus:bg-white/10 focus:border-white/20 transition-all"
          />

          <motion.button
            type="submit"
            disabled={!input.trim()}
            className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border transition-all ${input.trim()
              ? "bg-cyan-500/20 border-cyan-500/40 hover:bg-cyan-500/30 shadow-[0_0_10px_rgba(0,229,255,0.2)]"
              : "bg-white/5 border-white/10 opacity-40 cursor-not-allowed"
              }`}
            whileTap={input.trim() ? { scale: 0.92 } : {}}
          >
            <Send className="w-4 h-4 text-white/80" />
          </motion.button>
        </form>
      </div>
    </div>
  );
}