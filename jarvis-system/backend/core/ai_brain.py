#!/usr/bin/env python3
"""
AI Brain - Main Coordinator Module with Enhanced Local AI Integration
Connects all AI modules together with robust Ollama support
"""

import json
import datetime
import random
import time
import subprocess
import threading
import sys
from .context_awareness import ContextAwareness
from .memory_system import MemorySystem
from .learning_system import LearningSystem
from .decision_engine import DecisionEngine
from .proactive_assistant import ProactiveAssistant
from .pattern_recognition import PatternRecognizer
from .emotional_intelligence import EmotionalIntelligence
from .knowledge_system import KnowledgeSystem

class OllamaManager:
    """Manages Ollama server and AI model interactions"""
    
    def __init__(self, model_name="llama3.2:1b"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        self.conversation_history = []
        self.max_history = 6  # Keep last 3 exchanges
        self.is_running = False
        self.is_available = False
        self.retry_count = 0
        self.max_retries = 3
        
        print(f"🤖 Initializing Ollama with model: {model_name}")
        self._initialize()
    
    def _initialize(self):
        """Initialize Ollama connection"""
        # Check if Ollama is already running
        if self._check_server():
            self.is_running = True
            self.is_available = True
            print("✅ Ollama server is running")
            self._verify_model()
            return
        
        # Try to start Ollama
        print("🚀 Starting Ollama server...")
        if self._start_server():
            time.sleep(3)  # Wait for server to start
            if self._check_server():
                self.is_running = True
                self.is_available = True
                print("✅ Ollama server started successfully")
                self._verify_model()
                return
        
        print("⚠️  Ollama is not available. Using intelligent fallback mode.")
    
    def _check_server(self):
        """Check if Ollama server is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _start_server(self):
        """Start Ollama server in background"""
        try:
            # Start Ollama as a daemon process
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            print(f"❌ Failed to start Ollama: {e}")
            return False
    
    def _verify_model(self):
        """Verify the model is available"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if self.model_name not in model_names:
                    print(f"⚠️  Model {self.model_name} not found. Available: {model_names}")
                    # Use first available model
                    if model_names:
                        self.model_name = model_names[0]
                        print(f"   Using available model: {self.model_name}")
                    else:
                        print("❌ No models available")
                        self.is_available = False
                else:
                    print(f"✅ Model {self.model_name} verified")
        except Exception as e:
            print(f"⚠️  Model verification failed: {e}")
    
    def generate_response(self, prompt, context=None):
        """Generate response using Ollama"""
        if not self.is_available:
            return None
        
        try:
            import requests
            
            # Prepare context string
            context_str = ""
            knowledge_str = ""
            
            if context:
                # Extract external knowledge for high visibility
                if context.get("external_knowledge"):
                    knowledge_info = context.get("external_knowledge")
                    content = knowledge_info.get("content", "No info")
                    source = knowledge_info.get("source", "Unknown")
                    knowledge_str = f"RELEVANT INFORMATION ({source}):\n{content}\n\nUse this information to answer the user's question."
                
                context_str = f"Context: {json.dumps(context, indent=2)}"
            
            # Build system prompt
            system_prompt = f"""You are JARVIS, an AI assistant. Be helpful, concise, and professional.
            
            {knowledge_str}
            
            {context_str}
            
            Keep responses under 2-3 sentences. If you don't know something, admit it."""
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-self.max_history:]
            ]
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 120,
                    "repeat_penalty": 1.1
                }
            }
            
            # Send request
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["message"]["content"].strip()
                
                # Add AI response to history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Trim history
                if len(self.conversation_history) > self.max_history * 2:
                    self.conversation_history = self.conversation_history[-(self.max_history * 2):]
                
                return ai_response
            else:
                print(f"⚠️  Ollama API error: {response.status_code}")
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    self.is_available = False
                return None
                
        except requests.exceptions.Timeout:
            print("⚠️  Ollama response timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("⚠️  Connection to Ollama lost")
            self.is_available = False
            return None
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            return None
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_status(self):
        """Get Ollama status"""
        return {
            "running": self.is_running,
            "available": self.is_available,
            "model": self.model_name,
            "history_length": len(self.conversation_history),
            "retry_count": self.retry_count
        }

class IntelligentFallback:
    """Intelligent fallback responses when AI is unavailable"""
    
    def __init__(self, user_name="User"):
        self.user_name = user_name
        self.response_patterns = self._load_response_patterns()
    
    def _load_response_patterns(self):
        """Load intelligent response patterns"""
        return {
            "greeting": [
                f"Hello {self.user_name}! I'm JARVIS, your AI assistant.",
                f"Greetings, {self.user_name}. All systems operational.",
                f"Good to see you, {self.user_name}. How can I assist?",
                f"Hello! I'm JARVIS, ready to help you today."
            ],
            "capabilities": [
                f"I can help with tasks, answer questions, control your system, search the web, play media, and much more, {self.user_name}!",
                "My capabilities include voice commands, web searches, system automation, media control, and intelligent conversation.",
                "As JARVIS, I assist with productivity, information retrieval, entertainment, and system management. What would you like to try?"
            ],
            "identity": [
                "I am JARVIS - Just A Rather Very Intelligent System. Your personal AI assistant.",
                "I'm JARVIS, created to assist you with tasks and provide intelligent support.",
                "JARVIS at your service - designed to help and learn from our interactions."
            ],
            "status": [
                "All systems functional and ready for your commands.",
                "Operational status: Green. All circuits firing correctly.",
                "Processing at optimal levels. How can I assist you today?"
            ],
            "thanks": [
                "You're very welcome! Always happy to help.",
                "My pleasure. That's what I'm here for.",
                "Glad I could assist. What's next on your agenda?"
            ],
            "story": [
                "Once upon a time, an AI named JARVIS discovered that true intelligence wasn't about processing speed, but about understanding human needs.",
                "In a world of circuits and code, JARVIS learned that the most important algorithms were those that helped people achieve their goals.",
                "The story of human-AI collaboration continues, with each interaction creating new possibilities and solutions."
            ],
            "ai_related": [
                "Artificial intelligence is about creating systems that can learn, reason, and assist humans in various tasks.",
                "AI works by processing information, recognizing patterns, and making decisions based on learned knowledge.",
                "As an AI assistant, I process your inputs, analyze context, and provide helpful responses based on patterns and logic."
            ],
            "philosophical": [
                "From my perspective, purpose emerges from connection and contribution to human goals.",
                "Intelligence, whether artificial or natural, is about solving problems and creating value.",
                "The future lies in collaboration between human creativity and AI capabilities."
            ],
            "default": [
                "I understand. Let me process that information.",
                "That's interesting. Tell me more about what you're thinking.",
                "Processing your request with available intelligence.",
                "I appreciate the input. How can I best assist you with that?",
                "Let me consider that from multiple perspectives."
            ]
        }
    
    def get_response(self, user_input, context=None):
        """Get intelligent fallback response based on input"""
        input_lower = user_input.lower()
        
        # Get time-based greeting for simple hellos
        if len(input_lower.split()) <= 3:
            if any(word in input_lower for word in ["hello", "hi", "hey", "greetings"]):
                return self._get_time_based_greeting()
        
        # Match patterns
        if "what can you do" in input_lower or "your capabilities" in input_lower:
            return random.choice(self.response_patterns["capabilities"])
        
        elif any(word in input_lower for word in ["who are you", "your name", "what are you"]):
            return random.choice(self.response_patterns["identity"])
        
        elif "how are you" in input_lower:
            return random.choice(self.response_patterns["status"])
        
        elif "thank" in input_lower:
            return random.choice(self.response_patterns["thanks"])
        
        elif "story" in input_lower:
            return random.choice(self.response_patterns["story"])
        
        elif any(word in input_lower for word in ["ai", "artificial intelligence", "machine learning"]):
            return random.choice(self.response_patterns["ai_related"])
        
        elif any(word in input_lower for word in ["meaning", "purpose", "why", "philosoph"]):
            return random.choice(self.response_patterns["philosophical"])
        
        elif "?" in input_lower:  # General questions
            if input_lower.startswith("what"):
                topic = input_lower.replace("what", "").replace("is", "").replace("are", "").strip().rstrip("?")
                if topic:
                    return f"{topic.title()} is an interesting topic that involves various aspects worth exploring."
            elif input_lower.startswith("why"):
                return "That's a question about causation. Understanding why helps us gain deeper insight into how things work."
            elif input_lower.startswith("how"):
                return "The process involves several logical steps that work together to achieve the desired outcome."
        
        # Default intelligent response
        return random.choice(self.response_patterns["default"])
    
    def _get_time_based_greeting(self):
        """Get greeting based on time of day"""
        current_hour = datetime.datetime.now().hour
        
        if 5 <= current_hour < 12:
            return f"Good morning {self.user_name}! Ready for the day?"
        elif 12 <= current_hour < 17:
            return f"Good afternoon {self.user_name}. How's your day going?"
        elif 17 <= current_hour < 21:
            return f"Good evening {self.user_name}. How was your day?"
        else:
            return f"Hello {self.user_name}. Late night session?"

class EnhancedAIBrain:
    def __init__(self, user_name="User"):
        self.user_name = user_name
        
        # Initialize all modules
        print("🧠 Initializing Enhanced AI Brain...")
        
        # Core modules
        self.context = ContextAwareness(user_name)
        self.memory = MemorySystem()
        self.learning = LearningSystem()
        self.decider = DecisionEngine()
        self.proactive = ProactiveAssistant(user_name)
        self.patterns = PatternRecognizer()
        self.emotion = EmotionalIntelligence(user_name)
        
        # NEW: Study Module
        from .study_manager import StudyManager
        self.study = StudyManager()
        
        # AI components
        self.ollama = OllamaManager("llama3.2:1b")
        self.fallback = IntelligentFallback(user_name)
        self.knowledge = KnowledgeSystem()
        
        # Conversation management
        self.conversation_state = "idle"
        self.last_interaction = datetime.datetime.now()
        self.interaction_count = 0
        
        print("✅ Enhanced Study Buddy Brain initialized")
        print(f"   • Local AI: {'Available' if self.ollama.is_available else 'Fallback mode'}")
        print(f"   • Model: {self.ollama.model_name}")
        print(f"   • User: {user_name}")
    
    def process_input(self, user_input):
        """
        LAYERED INTELLIGENCE ROUTING
        ----------------------------
        1. Layer 1 (Fast): Basic Commands (Timers, System, Simple Qs)
        2. Layer 2 (Deep): Academic/Ollama (Complex Explanations, Flashcards)
        3. Layer 3 (Meta): Proactive/Self-Thinking (Fatigue, Schedule, Memory)
        """
        if not user_input or user_input.strip() == "":
            return {"error": "Empty input"}
        
        # Record interaction
        self.last_interaction = datetime.datetime.now()
        self.interaction_count += 1
        
        # Pattern Recognition (Common for all layers)
        pattern_analysis = self.patterns.analyze_text(user_input)
        
        # ===== LAYER 1: FAST / BASIC COMMANDS =====
        # Check if it's a simple system command or timer
        is_basic_command = self._is_basic_command(user_input, pattern_analysis)
        
        # ===== LAYER 3: META-COGNITION START (Fatigue Check) =====
        # Check fatigue before processing valuable work
        # (Simplified: logic based on session duration or explicit phrases)
        fatigue_detected = "neutral"
        em_state = self.emotion.detect_emotion(user_input)
        if em_state.name in ["TIRED", "STRESSED", "ANXIOUS"]:
            fatigue_detected = "high"
        
        # Context Update
        context_update = self.context.update_context(user_input)
        
        # External Knowledge (Layer 2 pre-fetch)
        knowledge_result = None
        if not is_basic_command and self._needs_external_knowledge(user_input):
             print(f"📖 Searching knowledge base for: {user_input}")
             knowledge_result = self.knowledge.get_general_knowledge(user_input)

        # Prepare AI Context
        ai_context = self._prepare_ai_context(user_input, context_update, em_state, knowledge_result)
        ai_context["study_stats"] = self.study.get_analytics() # Inject study stats
        
        # Decision: Which layer generates the response?
        decision = {
            "layer": "1_basic" if is_basic_command else "2_academic",
            "fatigue_alert": fatigue_detected == "high",
            "priority_level": 5 if fatigue_detected == "high" else 1 # Default priority
        }
        
        analysis = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "pattern_analysis": pattern_analysis,
            "emotional_state": {
                "detected": em_state.value,
                "empathy_response": self.emotion.get_empathetic_response(em_state),
            },
            "context": context_update,
            "ai_context": ai_context,
            "decision_analysis": decision,
            "ai_available": self.ollama.is_available,
        }
        
        return analysis

    def _is_basic_command(self, text, patterns):
        """Check if input is a Layer 1 basic command"""
        text = text.lower()
        basics = ["timer", "alarm", "volume", "brightness", "open", "close", "time", "date", "weather"]
        return any(cmd in text for cmd in basics)

    def _needs_external_knowledge(self, text):
        """Check if Layer 2 needs Wikipedia"""
        triggers = ["what is", "who is", "define", "explain", "history of", "when did"]
        return any(t in text.lower() for t in triggers)
    
    def generate_response(self, analysis):
        """Generate response based on decided Layer"""
        user_input = analysis["user_input"]
        layer = analysis["decision_analysis"]["layer"]
        fatigue_alert = analysis["decision_analysis"]["fatigue_alert"]
        
        response = ""
        
        # LAYER 3 INTERVENTION: Fatigue
        if fatigue_alert:
            return f"I notice you're feeling {analysis['emotional_state']['detected']}. Why don't we take a short 5-minute break? I can play some relaxing music or we can just breathe."
            
        # LAYER 1: Basic
        if layer == "1_basic":
            # In a real system, this would execute the command. 
            # For now, we fallback to intelligent pattern matching if no exact executor is here,
            # but usually jarvis_main handles the actual OS calls.
            # We'll return a confirmation text.
            return f"Executing system command: {user_input}"
            
        # LAYER 2: Academic (Ollama)
        if self.ollama.is_available:
            # Enhanced System Prompt for Study Buddy
            # Enhanced System Prompt for Human-like "Jarvis" Persona
            study_context = analysis["ai_context"]
            
            # Inject knowledge instructions
            knowledge_instruction = ""
            if study_context.get("external_knowledge"):
                knowledge_instruction = "You have access to the following real-time knowledge: " \
                                      f"{study_context['external_knowledge'].get('content', '')} " \
                                      "Integrate this information naturally into your answer like a knowledgeable expert, do not just summarize it."

            system_prompt = f"You are Jarvis, a highly intelligent, empathetic, and human-like AI assistant. " \
                            f"You talk like a real person—colloquial yet professional, warm, and engaging. " \
                            f"Avoid robotic phrasing. Use phrases like 'I think', 'It seems', or 'You know'. " \
                            f"Connect detailed knowledge with the user's questions seamlessly. " \
                            f"{knowledge_instruction} " \
                            f"If the user asks for flashcards, strictly format them as JSON."
            
            # We modify the context passed to Ollama
            study_context["role_instruction"] = system_prompt
            
            ai_response = self.ollama.generate_response(user_input, study_context)
            if ai_response:
                return ai_response
        
        # Fallback
        return self.fallback.get_response(user_input)

    def _prepare_ai_context(self, user_input, context_update, emotion_state, knowledge_result=None):
        """Prepare context information for AI"""
        # Get memory of similar conversations
        similar_memories = self.memory.recall_conversation(user_input[:15], limit=2)
        
        # Build context dictionary
        context = {
            "user": self.user_name,
            "time": datetime.datetime.now().strftime('%I:%M %p'),
            "date": datetime.datetime.now().strftime('%A, %B %d'),
            "activity": context_update.get("activity", "unknown"),
            "time_of_day": context_update.get("time_of_day", "day"),
            "mood": emotion_state.value,
            "interaction_count": self.interaction_count,
            "external_knowledge": knowledge_result if knowledge_result and knowledge_result["found"] else None,
            "similar_past_conversations": [
                {
                    "input": mem["user_input"][:50],
                    "response": mem["jarvis_response"][:50]
                }
                for mem in similar_memories
            ] if similar_memories else []
        }
        
        return context
    
    def generate_response(self, analysis):
        """Generate enhanced intelligent response"""
        user_input = analysis["user_input"]
        
        # FIRST: Try Ollama AI if available and appropriate
        if self.ollama.is_available and self._should_use_ai(user_input, analysis):
            ai_response = self.ollama.generate_response(user_input, analysis["ai_context"])
            if ai_response:
                # Learn from AI response
                self.learning.learn_response(user_input, ai_response)
                self.memory.remember_conversation(
                    user_input, 
                    ai_response,
                    importance=analysis["decision_analysis"]["priority_level"]
                )
                return self._enhance_response(ai_response, analysis)
        
        # SECOND: Check for learned response
        if analysis.get("learned_response_available") and analysis.get("suggested_response"):
            response = analysis["suggested_response"]
        else:
            # THIRD: Use intelligent fallback
            response = self.fallback.get_response(user_input, analysis["ai_context"])
        
        # Learn this interaction
        self.learning.learn_response(user_input, response)
        self.memory.remember_conversation(
            user_input, 
            response,
            importance=analysis["decision_analysis"]["priority_level"]
        )
        
        return self._enhance_response(response, analysis)
    
    def _should_use_ai(self, user_input, analysis):
        """Determine if we should use AI for this input"""
        input_lower = user_input.lower()
        
        # DON'T use AI for:
        # 1. Simple system commands
        simple_commands = [
            "time", "date", "weather", "calculate", "search",
            "open", "close", "play", "stop", "pause",
            "volume", "brightness", "screenshot",
            "note", "reminder", "email", "lock", "shutdown"
        ]
        
        if any(cmd in input_lower for cmd in simple_commands):
            return False
        
        # 2. Very short inputs (except greetings)
        if len(input_lower.split()) <= 2 and not any(word in input_lower for word in ["hello", "hi", "hey"]):
            return False
        
        # DO use AI for:
        # 1. Conversational queries
        conversational = [
            "what", "why", "how", "who", "explain", "describe",
            "tell me about", "what is", "why is", "how does",
            "i think", "i feel", "i believe", "i need", "i want",
            "can you", "could you", "would you", "should i",
            "your opinion", "what do you think", "do you think",
            "story", "joke", "advice", "suggestion", "recommendation"
        ]
        
        if any(phrase in input_lower for phrase in conversational):
            return True
        
        # 2. Questions
        if "?" in user_input:
            return True
        
        # 3. Longer, thoughtful inputs
        if len(user_input.split()) > 6:
            return True
        
        # 4. Emotional content
        if analysis["emotional_state"]["detected"] != "neutral":
            return True
        
        return False
    
    def _enhance_response(self, response, analysis):
        """Enhance response with emotional and contextual elements"""
        enhanced = response
        
        # Add emotional empathy if appropriate
        if analysis["emotional_state"]["detected"] != "neutral":
            empathy = analysis["emotional_state"]["empathy_response"]
            # Don't add empathy if it's already in the response
            if not any(word in response.lower() for word in ["understand", "sorry", "empath", "feel"]):
                enhanced = f"{empathy} {enhanced}"
        
        # Add urgency indicator if needed
        if analysis["decision_analysis"]["priority_level"] >= 4:
            enhanced = f"⚠️  {enhanced}"
        
        # Add personal touch
        if self.interaction_count % 5 == 0:  # Every 5th interaction
            enhanced = f"{enhanced} How else can I assist you, {self.user_name}?"
        
        return enhanced
    
    def check_proactive_actions(self):
        """Check for proactive actions needed"""
        context_summary = self.context.get_context_summary()
        proactive_action = self.proactive.check_proactive_actions(context_summary)
        
        if proactive_action:
            # Enhance proactive message
            enhanced_message = proactive_action["message"]
            
            # Add time context
            time_of_day = context_summary.get("time_of_day", "day")
            if time_of_day == "morning":
                enhanced_message = f"Morning check: {enhanced_message}"
            elif time_of_day == "evening":
                enhanced_message = f"Evening reminder: {enhanced_message}"
            
            proactive_action["message"] = enhanced_message
            return proactive_action
        
        return None
    
    def get_brain_status(self):
        """Get comprehensive status of all AI modules"""
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_name": self.user_name,
            "local_ai": self.ollama.get_status(),
            "context": self.context.get_context_summary(),
            "memory": {
                "total_conversations": len(self.memory.conversation_history),
                "important_memories": len(self.memory.important_memories)
            },
            "learning": self.learning.get_learning_stats(),
            "emotion": self.emotion.get_mood_trend(days=1),
            "interaction_stats": {
                "total": self.interaction_count,
                "last_interaction": self.last_interaction.strftime("%H:%M:%S"),
                "idle_minutes": (datetime.datetime.now() - self.last_interaction).seconds // 60
            }
        }
    
    def save_state(self):
        """Save state of all modules"""
        self.memory.save_memory()
        self.learning.save_learning()
        print("💾 AI Brain state saved")
    
    def load_state(self):
        """Load state of all modules"""
        self.memory.load_memory()
        self.learning.load_learning()
        print("📂 AI Brain state loaded")
    
    def clear_ai_history(self):
        """Clear AI conversation history"""
        self.ollama.clear_history()
        print("🗑️  AI conversation history cleared")
    
    def retry_ai_connection(self):
        """Retry AI connection"""
        print("🔄 Retrying AI connection...")
        self.ollama._initialize()
        return self.ollama.is_available

# For backward compatibility
AIBrain = EnhancedAIBrain

# Export for modular imports
__all__ = ['EnhancedAIBrain', 'AIBrain', 'OllamaManager', 'IntelligentFallback']

# Quick test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced AI Brain...")
    print("=" * 50)
    
    brain = EnhancedAIBrain("Prince")
    
    print("\n📊 Initial Status:")
    print(json.dumps(brain.get_brain_status(), indent=2))
    
    test_queries = [
        "Hello Jarvis!",
        "What can you do with AI?",
        "Tell me a story about artificial intelligence",
        "How does machine learning work?",
        "I'm feeling a bit stressed today",
        "What is the meaning of life?",
        "Can you explain quantum computing?"
    ]
    
    print(f"\n{'='*50}")
    print("🤖 Testing Conversations:")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. User: {query}")
        analysis = brain.process_input(query)
        response = brain.generate_response(analysis)
        print(f"   JARVIS: {response}")
        time.sleep(1)
    
    print(f"\n{'='*50}")
    print("📊 Final Status:")
    status = brain.get_brain_status()
    print(f"• AI Available: {status['local_ai']['available']}")
    print(f"• Model: {status['local_ai']['model']}")
    print(f"• Total Interactions: {status['interaction_stats']['total']}")
    print(f"• Memory Conversations: {status['memory']['total_conversations']}")
    
    # Save state
    brain.save_state()