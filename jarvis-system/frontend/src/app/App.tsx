import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Robot, RobotState } from "./components/Robot";
import { ChatInterface, Message } from "./components/ChatInterface";
import { StatusLED } from "./components/StatusLED";
import { EmotionPanel, EmotionData } from "./components/EmotionPanel";
import { StudyDashboard, SessionData } from "./components/StudyDashboard";
import { analyzeTextMood } from "./utils/textMoodAnalyzer";
import { isPraiseMessage, getComplimentResponse } from "./utils/complimentResponder";
import { speak } from "./utils/speak";
import {
  Brain, BookOpen, Clock, BarChart2, ChevronLeft, ChevronRight,
  Wifi, WifiOff, GraduationCap, FolderPlus, Upload, Loader2,
  ChevronDown, FileText, Trash2
} from "lucide-react";

type SidebarTab = "dashboard" | "emotion" | "flashcards";

const DEFAULT_SESSION: SessionData = {
  duration_mins: 0,
  current_topic: "Getting Started",
  mastery_score: 0,
  consistency_score: 0,
  suggestion: "Ask me your first question to begin your session!",
  exam_days_left: null,
};

const DEFAULT_EMOTION: EmotionData = {
  emotion: "neutral",
  intensity: 0.3,
  needs_intervention: false,
};

export default function App() {
  const [robotState, setRobotState] = useState<RobotState>("idle");
  const [robotEmotion, setRobotEmotion] = useState<"neutral" | "shy">("neutral");
  const [messages, setMessages] = useState<Message[]>([
    { id: "1", type: "system", text: "J.A.R.V.I.S. Academic Copilot Initialized", timestamp: new Date() },
  ]);
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<SidebarTab>("dashboard");
  const [robotSide, setRobotSide] = useState<"left" | "center" | "right">("center");

  const cycleRobotSide = () =>
    setRobotSide(s => s === "center" ? "right" : s === "right" ? "left" : "center");
  const [emotionData, setEmotionData] = useState<EmotionData>(DEFAULT_EMOTION);
  const [sessionData, setSessionData] = useState<SessionData>(DEFAULT_SESSION);
  const [flashcards, setFlashcards] = useState<string[]>([]);
  const [newFlashcardName, setNewFlashcardName] = useState("");
  const [isCreatingFlashcard, setIsCreatingFlashcard] = useState(false);
  const [uploadingToSubject, setUploadingToSubject] = useState<string | null>(null);
  const [expandedSubjects, setExpandedSubjects] = useState<{ [key: string]: any[] }>({});
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({});
  const socketRef = useRef<WebSocket | null>(null);
  const sessionStartRef = useRef<Date>(new Date());

  // Fetch flashcards on load and poll for updates
  useEffect(() => {
    const fetchFlashcards = async () => {
      try {
        const protocol = window.location.protocol;
        const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
        const res = await fetch(`${protocol}//${host}/api/local-flashcards`);
        if (res.ok) {
          const data = await res.json();
          setFlashcards(data.flashcards || []);
        }
      } catch (e) {
        console.error("Failed to fetch flashcards", e);
      }
    };
    fetchFlashcards();
    // Poll for updates every 5 seconds
    const intervalId = setInterval(fetchFlashcards, 5000);
    return () => clearInterval(intervalId);
  }, []);

  // Update session duration every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setSessionData(s => ({
        ...s,
        duration_mins: Math.floor((Date.now() - sessionStartRef.current.getTime()) / 60000),
      }));
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted) return;
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      const host = isLocal ? "localhost:8000" : window.location.host;
      const wsUrl = `${protocol}//${host}/ws`;

      const socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        if (!isMounted) { socket.close(); return; }
        setIsConnected(true);
        addSystemMessage("🟢 Connected to JARVIS Academic Core");
        setRobotState("idle");
      };

      socket.onclose = () => {
        if (!isMounted) return;
        setIsConnected(false);
        addSystemMessage("🔴 Connection lost. Reconnecting…");
        setRobotState("error");
        clearTimeout(reconnectTimeout);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = () => {
        if (!isMounted) return;
        setRobotState("error");
      };

      socket.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data = JSON.parse(event.data);
          handleBackendMessage(data);
        } catch {
          console.error("Message parse error");
        }
      };

      socketRef.current = socket;
    };

    connectWebSocket();
    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      if (socketRef.current) { socketRef.current.onclose = null; socketRef.current.close(); }
    };
  }, []);

  const addSystemMessage = (text: string) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), type: "system", text, timestamp: new Date() }]);
  };

  const addAiMessage = (text: string, marks?: number, subject?: string) => {
    setMessages(prev => {
      const last = prev[prev.length - 1];
      if (last?.type === "ai" && last.text === text) return prev;
      return [...prev, { id: Date.now().toString(), type: "ai", text, timestamp: new Date(), marks, subject }];
    });
  };

  const handleBackendMessage = (data: any) => {
    switch (data.type) {
      case "response":
        if (data.sender === "user") {
          setMessages(prev => [...prev, { id: Date.now().toString(), type: "user", text: data.content, timestamp: new Date() }]);
        }
        break;
      case "text":
        if (data.text) {
          addAiMessage(data.text, data.marks, data.subject);
          setCurrentMessage(data.text);
        }
        break;
      case "lipsync_start":
        setRobotState("speaking");
        break;
      case "lipsync_stop":
        setRobotState("idle");
        setRobotEmotion("neutral");
        break;
      case "voice_status":
        setIsListening(data.listening);
        setRobotState((prev) => {
          if (data.listening) return "listening";
          // If we finished listening but we are already processing the response, keep processing
          if (prev === "processing") return "processing";
          // Otherwise go to idle
          return "idle";
        });
        break;
      case "processing":
        setRobotState("processing");
        break;
      case "emotion_update":
        if (data.emotion) {
          setEmotionData(data.emotion);
          setActiveTab("emotion");
        }
        break;
      case "session_update":
        if (data.session) setSessionData(data.session);
        break;
      case "suggestion":
        setSessionData(s => ({ ...s, suggestion: data.message }));
        break;
      case "error":
        addSystemMessage("❌ Error: " + data.message);
        setRobotState("error");
        setTimeout(() => setRobotState("idle"), 3000);
        break;
    }
  };

  const handleSendMessage = (text: string, marks: number | null, subject: string) => {
    // ── 1. Mood from typing style ───────────────────────────────────────
    const mood = analyzeTextMood(text);
    setRobotEmotion(mood.robotEmotion);
    setEmotionData({
      emotion: mood.mood === "shy" ? "neutral" : mood.mood,
      intensity: mood.intensity,
      needs_intervention: mood.intensity > 0.75 &&
        ["angry", "confused", "sad"].includes(mood.mood),
    });
    if (mood.mood !== "neutral") setActiveTab("emotion");

    // Add user message immediately
    setMessages(prev => [...prev, { id: Date.now().toString(), type: "user", text, timestamp: new Date() }]);

    // ── 2. Compliment short-circuit — NO backend call ───────────────────
    if (isPraiseMessage(text)) {
      // Robot reacts: go shy + speaking state
      setRobotEmotion("shy");
      setRobotState("speaking");
      setEmotionData({ emotion: "neutral", intensity: 0.9, needs_intervention: false });
      setActiveTab("emotion");

      // Staggered: brief pause then reply (feels natural)
      setTimeout(() => {
        const reply = getComplimentResponse();
        setCurrentMessage(reply);
        setMessages(prev => [
          ...prev,
          { id: Date.now().toString(), type: "ai", text: reply, timestamp: new Date() },
        ]);
        speak(reply);  // 🔊 voice it through the browser speaker
      }, 350);

      // Return to idle after speaking
      setTimeout(() => {
        setRobotState("idle");
        setRobotEmotion("neutral");
        setCurrentMessage("");
      }, 3500);

      return; // ← skip backend entirely
    }
    // ───────────────────────────────────────────────────────────────────

    // ── 3. Normal message → send to backend ────────────────────────────
    if (isConnected && socketRef.current) {
      setRobotState("processing");
      socketRef.current.send(JSON.stringify({
        type: "command",
        content: text,
        marks: marks ?? 0,
        subject: subject !== "General" ? subject : undefined,
        mood: mood.mood,
      }));
      setSessionData(s => ({ ...s, current_topic: text.slice(0, 40) + (text.length > 40 ? "…" : "") }));
    } else {
      if (mood.mood !== "neutral") {
        setTimeout(() => addSystemMessage(`💭 ${mood.tip}`), 400);
      }
    }
  };

  const handleMicClick = () => {
    if (isConnected && socketRef.current) {
      socketRef.current.send(JSON.stringify({ type: "toggle_voice" }));
    }
  };

  const handleStopClick = () => {
    if (isConnected && socketRef.current) {
      socketRef.current.send(JSON.stringify({ type: "cancel" }));
      setRobotState("idle");
      setRobotEmotion("neutral");
      setIsListening(false);
    }
  };

  const handleCreateFlashcard = async () => {
    if (!newFlashcardName.trim()) return;
    setIsCreatingFlashcard(true);
    try {
      const protocol = window.location.protocol;
      const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
      const res = await fetch(`${protocol}//${host}/api/local-flashcards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newFlashcardName.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setFlashcards(data.flashcards);
        setNewFlashcardName("");
        addSystemMessage(`📁 Flashcard subject "${newFlashcardName}" created!`);
      } else {
        const errorData = await res.json().catch(() => ({}));
        const errorMessage = errorData.detail || "Failed to create flashcard subject.";
        alert(errorMessage);
      }
    } catch (e) {
      console.error(e);
      alert("Error creating flashcard subject.");
    } finally {
      setIsCreatingFlashcard(false);
    }
  };

  const handleUploadToSubject = async (subject: string, file: File) => {
    setUploadingToSubject(subject);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const protocol = window.location.protocol;
      const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
      const res = await fetch(`${protocol}//${host}/api/local-flashcards/${encodeURIComponent(subject)}/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        addSystemMessage(`📄 Material uploaded to ${subject}! You can now select this subject in chat.`);
        // Refresh materials for this subject if expanded
        if (expandedSubjects[subject]) {
          await toggleSubjectExpansion(subject);
        }
      } else {
        alert(`Failed to upload to ${subject}.`);
      }
    } catch (e) {
      console.error(e);
      alert(`Error uploading file to ${subject}.`);
    } finally {
      setUploadingToSubject(null);
      if (fileInputRefs.current[subject]) fileInputRefs.current[subject]!.value = "";
    }
  };

  const toggleSubjectExpansion = async (subject: string) => {
    if (expandedSubjects[subject]) {
      // Collapse
      setExpandedSubjects(prev => {
        const newState = { ...prev };
        delete newState[subject];
        return newState;
      });
    } else {
      // Expand and fetch materials
      try {
        const protocol = window.location.protocol;
        const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
        const res = await fetch(`${protocol}//${host}/api/local-flashcards/${encodeURIComponent(subject)}/materials`);
        if (res.ok) {
          const data = await res.json();
          setExpandedSubjects(prev => ({
            ...prev,
            [subject]: data.materials || []
          }));
        }
      } catch (e) {
        console.error("Failed to fetch materials", e);
      }
    }
  };

  const handleDeleteFlashcard = async (subject: string) => {
    if (!window.confirm(`Are you sure you want to delete the flashcard subject "${subject}" and all its materials?`)) return;
    try {
      const protocol = window.location.protocol;
      const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
      const res = await fetch(`${protocol}//${host}/api/local-flashcards/${encodeURIComponent(subject)}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setFlashcards(prev => prev.filter(f => f !== subject));
        setExpandedSubjects(prev => {
          const newState = { ...prev };
          delete newState[subject];
          return newState;
        });
        addSystemMessage(`🗑️ Deleted subject "${subject}"`);
      } else {
        alert("Failed to delete subject.");
      }
    } catch (e) {
      console.error(e);
      alert("Error deleting subject.");
    }
  };

  const handleDeleteMaterial = async (subject: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    try {
      const protocol = window.location.protocol;
      const host = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? "localhost:8000" : window.location.host;
      const res = await fetch(`${protocol}//${host}/api/local-flashcards/${encodeURIComponent(subject)}/materials/${encodeURIComponent(filename)}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setExpandedSubjects(prev => ({
          ...prev,
          [subject]: prev[subject]?.filter((m: any) => m.name !== filename) || []
        }));
        addSystemMessage(`🗑️ Deleted material "${filename}" from ${subject}`);
      } else {
        alert("Failed to delete material.");
      }
    } catch (e) {
      console.error(e);
      alert("Error deleting material.");
    }
  };

  const sidebarTabs: { id: SidebarTab; icon: React.ReactNode; label: string }[] = [
    { id: "dashboard", icon: <BarChart2 className="w-4 h-4" />, label: "Session" },
    { id: "emotion", icon: <Brain className="w-4 h-4" />, label: "Mindset" },
    { id: "flashcards", icon: <BookOpen className="w-4 h-4" />, label: "Flashcards" },
  ];

  return (
    <div className="relative min-h-screen w-full overflow-hidden flex" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* ── Background ── */}
      <div className="fixed inset-0 z-0 bg-[#050509]">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_60%_20%,rgba(0,100,160,0.08)_0%,transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_80%,rgba(80,0,160,0.06)_0%,transparent_60%)]" />
        {/* Grid */}
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.025) 1px,transparent 1px)`,
          backgroundSize: "48px 48px",
          transform: "perspective(600px) rotateX(55deg)",
          transformOrigin: "top",
          maskImage: "linear-gradient(to bottom,rgba(0,0,0,0.6) 0%,rgba(0,0,0,0) 70%)",
        }} />
        {/* Dust */}
        {[...Array(40)].map((_, i) => (
          <div key={i} className="absolute rounded-full bg-white/5 animate-float" style={{
            width: Math.random() * 2 + 1 + "px", height: Math.random() * 2 + 1 + "px",
            left: Math.random() * 100 + "%", top: Math.random() * 100 + "%",
            animationDelay: Math.random() * 8 + "s", animationDuration: Math.random() * 25 + 20 + "s",
          }} />
        ))}
      </div>

      {/* ── Left Sidebar ── */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
            transition={{ type: "spring", damping: 25 }}
            className="fixed left-0 top-0 h-full w-72 z-30 flex flex-col"
          >
            <div className="h-full bg-black/40 backdrop-blur-2xl border-r border-white/8 flex flex-col">
              {/* Logo */}
              <div className="p-5 border-b border-white/8">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center">
                    <GraduationCap className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white tracking-wide">J.A.R.V.I.S.</p>
                    <p className="text-[10px] text-white/30 tracking-widest uppercase">Academic Copilot</p>
                  </div>
                  <div className="ml-auto flex items-center gap-1.5">
                    {isConnected
                      ? <Wifi className="w-3.5 h-3.5 text-green-400" />
                      : <WifiOff className="w-3.5 h-3.5 text-red-400 animate-pulse" />}
                  </div>
                </div>
              </div>

              {/* Tab Nav */}
              <div className="flex gap-1 p-3 border-b border-white/8">
                {sidebarTabs.map(tab => (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 flex flex-col items-center gap-1 py-2 rounded-lg text-[10px] font-medium tracking-wider uppercase transition-all ${activeTab === tab.id ? "bg-white/10 text-cyan-400" : "text-white/30 hover:text-white/60 hover:bg-white/5"
                      }`}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <AnimatePresence mode="wait">
                  {activeTab === "dashboard" && (
                    <motion.div key="dash" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                      <StudyDashboard session={sessionData} />
                    </motion.div>
                  )}
                  {activeTab === "emotion" && (
                    <motion.div key="emo" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                      <h3 className="text-[10px] font-semibold text-white/40 uppercase tracking-widest mb-3">Emotional State</h3>
                      <EmotionPanel emotion={emotionData} />
                    </motion.div>
                  )}
                  {activeTab === "flashcards" && (
                    <motion.div key="flashcards" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                      <h3 className="text-[10px] font-semibold text-white/40 uppercase tracking-widest mb-3">Study Flashcards</h3>

                      {/* Create Flashcard */}
                      <div className="flex gap-2 mb-4">
                        <input
                          type="text"
                          value={newFlashcardName}
                          onChange={(e) => setNewFlashcardName(e.target.value)}
                          placeholder="New Subject..."
                          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50"
                          onKeyDown={(e) => e.key === 'Enter' && handleCreateFlashcard()}
                        />
                        <button
                          onClick={handleCreateFlashcard}
                          disabled={isCreatingFlashcard || !newFlashcardName.trim()}
                          className="w-8 h-8 flex items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-50"
                        >
                          {isCreatingFlashcard ? <Loader2 className="w-4 h-4 animate-spin" /> : <FolderPlus className="w-4 h-4" />}
                        </button>
                      </div>

                      {/* List Flashcards */}
                      <div className="space-y-2">
                        {flashcards.length > 0 ? (
                          flashcards.map((subject) => (
                            <div key={subject} className="border border-white/5 rounded-lg overflow-hidden">
                              {/* Subject Header */}
                              <div className="flex justify-between items-center bg-white/5 p-3">
                                <button
                                  onClick={() => toggleSubjectExpansion(subject)}
                                  className="flex items-center gap-2 text-white/80 text-sm font-medium hover:text-white transition-colors flex-1 text-left"
                                >
                                  <ChevronDown className={`w-4 h-4 transition-transform ${expandedSubjects[subject] ? 'rotate-180' : ''}`} />
                                  <BookOpen className="w-4 h-4 text-purple-400" />
                                  {subject}
                                  {expandedSubjects[subject] && (
                                    <span className="text-xs text-cyan-400 ml-2">
                                      ({expandedSubjects[subject].length} files)
                                    </span>
                                  )}
                                </button>
                                <div className="flex items-center gap-2">
                                  <input
                                    type="file"
                                    className="hidden"
                                    accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"
                                    ref={el => fileInputRefs.current[subject] = el}
                                    onChange={(e) => e.target.files?.[0] && handleUploadToSubject(subject, e.target.files[0])}
                                  />
                                  <button
                                    onClick={() => fileInputRefs.current[subject]?.click()}
                                    disabled={uploadingToSubject === subject}
                                    className="text-cyan-400 p-1.5 rounded bg-cyan-500/10 hover:bg-cyan-500/20 disabled:opacity-50"
                                    title="Upload Material"
                                  >
                                    {uploadingToSubject === subject ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                                  </button>
                                  <button
                                    onClick={() => handleDeleteFlashcard(subject)}
                                    className="text-red-400 p-1.5 rounded bg-red-500/10 hover:bg-red-500/20 transition-colors"
                                    title="Delete Subject"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                              
                              {/* Materials List */}
                              {expandedSubjects[subject] && (
                                <div className="bg-black/20 border-t border-white/5">
                                  {expandedSubjects[subject].length > 0 ? (
                                    <div className="p-3 space-y-2">
                                      {expandedSubjects[subject].map((material, idx) => (
                                        <div key={idx} className="flex items-center justify-between text-xs text-white/60 bg-white/5 rounded p-2 group">
                                          <div className="flex items-center gap-2 flex-1 min-w-0">
                                            <FileText className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                                            <span className="truncate">{material.name}</span>
                                          </div>
                                          <div className="flex items-center gap-3">
                                            <span className="text-white/40 flex-shrink-0">
                                              {(material.size / 1024).toFixed(1)} KB
                                            </span>
                                            <button
                                              onClick={() => handleDeleteMaterial(subject, material.name)}
                                              className="opacity-0 group-hover:opacity-100 text-red-400 p-1 rounded hover:bg-red-500/20 transition-all"
                                              title="Delete Material"
                                            >
                                              <Trash2 className="w-3 h-3" />
                                            </button>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <div className="p-3 text-center text-white/30 text-xs">
                                      No materials uploaded yet
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-6 text-white/20 text-xs">
                            <BookOpen className="w-6 h-6 mx-auto mb-2 opacity-30" />
                            No flashcards created yet.
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Status Row */}
              <div className="p-4 border-t border-white/8 flex gap-3">
                <StatusLED color="#00E5FF" active={isConnected} label="Core" size="sm" />
                <StatusLED color="#A855F7" active={robotState === "processing"} label="AI" size="sm" />
                <StatusLED color="#EF4444" active={robotState === "error"} label="Err" size="sm" />
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Sidebar Toggle */}
      <button
        onClick={() => setSidebarOpen(o => !o)}
        style={{ left: sidebarOpen ? "272px" : "0px" }}
        className="fixed top-1/2 -translate-y-1/2 z-40 w-5 h-12 bg-black/60 backdrop-blur-xl border border-white/10 rounded-r-xl flex items-center justify-center text-white/40 hover:text-white/80 transition-all"
      >
        {sidebarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
      </button>

      {/* ── Main content ── */}
      <div className={`flex-1 relative z-10 transition-all duration-300 ${sidebarOpen ? "ml-72" : "ml-0"}`}>
        {/* Top bar */}
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-20 pointer-events-none" style={{ left: sidebarOpen ? "calc(50% + 144px)" : "50%" }}>
          <div className="backdrop-blur-xl px-5 py-1.5 rounded-full border border-white/10 bg-white/5 shadow-lg">
            <div className="flex items-center gap-3 text-xs">
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-white/70 font-medium tracking-wider">{sessionData.current_topic}</span>
              <span className="text-white/20">|</span>
              <span className={`text-[11px] font-semibold tracking-wider ${isConnected ? "text-green-400/90" : "text-red-400/90"}`}>
                {isConnected ? "● ONLINE" : "○ OFFLINE"}
              </span>
            </div>
          </div>
        </div>

        {/* Robot – click to reposition */}
        <motion.div
          className="absolute bottom-[-60px] w-[420px] h-[500px] md:w-[750px] md:h-[750px] pointer-events-auto flex items-end justify-center cursor-pointer group"
          animate={{
            left: robotSide === "left" ? "5%" : robotSide === "right" ? "auto" : "50%",
            right: robotSide === "right" ? "5%" : "auto",
            x: robotSide === "center" ? "-50%" : "0%",
          }}
          transition={{ type: "spring", stiffness: 120, damping: 22 }}
          onClick={cycleRobotSide}
          title="Click to move the robot"
        >
          <Robot state={robotState} message={currentMessage} emotion={robotEmotion} />
          {/* Hover hint */}
          <div className="absolute top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
            <div className="bg-black/60 backdrop-blur-xl border border-white/10 rounded-full px-3 py-1 text-[10px] text-white/50 whitespace-nowrap flex items-center gap-1.5">
              <span>↔</span> Click to move
            </div>
          </div>
        </motion.div>

        {/* Chat - Bottom Right */}
        <div className="fixed bottom-6 right-6 z-20 w-[390px] md:w-[430px] h-[560px] pointer-events-auto">
          <div className="h-full rounded-3xl overflow-hidden bg-black/25 backdrop-blur-3xl border border-white/10 shadow-2xl flex flex-col">
            {/* Chat Header */}
            <div className="px-4 py-3 border-b border-white/8 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[11px] font-semibold text-white/60 tracking-widest uppercase">Academic Chat</span>
              <div className="ml-auto flex items-center gap-2">
                <Clock className="w-3 h-3 text-white/20" />
                <span className="text-[10px] text-white/20">{sessionData.duration_mins}m</span>
              </div>
            </div>
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              onMicClick={handleMicClick}
              onStopClick={handleStopClick}
              isListening={isListening}
              isProcessing={robotState === "processing"}
              isSpeaking={robotState === "speaking"}
            />
          </div>
        </div>
      </div>

      {/* Custom keyframes */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) translateX(0); }
          33%       { transform: translateY(-18px) translateX(8px); }
          66%       { transform: translateY(-28px) translateX(-10px); }
        }
        .animate-float { animation: float 20s ease-in-out infinite; }

        .scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }

        code.math { font-family: 'JetBrains Mono', monospace; background: rgba(0,229,255,0.07); color: #67e8f9; padding: 0 4px; border-radius: 4px; }
        pre { background: rgba(0,0,0,0.5); border-radius: 8px; padding: 10px 12px; overflow-x: auto; font-size: 12px; color: #d1d5db; margin: 6px 0; }
        pre code { all: unset; font-family: 'JetBrains Mono', monospace; }
      `}</style>
    </div>
  );
}