#!/usr/bin/env python3
"""
FULL-FLEDGED AI BRAIN - Complete AI Assistant System
Enhanced with all modules, local LLM, advanced cognition, and multi-layer intelligence
"""

import json
import datetime
import random
import time
import asyncio
import subprocess
import threading
import sys
import os
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
from collections import defaultdict, deque
import numpy as np

# Import all enhanced modules
from context.context_awareness_enhanced import EnhancedContextAwareness
# from memory_system.memory_system_enhanced import EnhancedMemorySystem
from learning.learning_system_enhanced import EnhancedLearningSystem
from decision.decision_engine_enhanced import EnhancedDecisionEngine
from context.proactive_assistant_enhanced import AdvancedProactiveAssistant
from learning.pattern_recognition_enhanced import AdvancedPatternRecognizer
from context.proactive_assistant_enhanced import AdvancedProactiveAssistant
from learning.pattern_recognition_enhanced import AdvancedPatternRecognizer
from emotional_intelligence import EmotionalIntelligence
from learning.knowledge_system_enhanced import EnhancedKnowledgeSystem
from learning.study_manager_enhanced import AdvancedStudyManager
from system.event_bus_enhanced import AdvancedEventBus, Event, EventPriority, EventStatus
from knowledge.rag_engine.syllabus_aware_rag import SyllabusAwareRAG
class RAGAdapter:
    def __init__(self, config=None):
        self.advanced_rag = SyllabusAwareRAG(config)
        self.loop = asyncio.new_event_loop()
        
        # Start a background thread for the event loop
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
            
        self.thread = threading.Thread(target=run_loop, args=(self.loop,), daemon=True)
        self.thread.start()

    def ingest_document(self, file_path, subject):
        future = asyncio.run_coroutine_threadsafe(
            self.advanced_rag.index_document(file_path, subject=subject), 
            self.loop
        )
        try:
            doc_id = future.result(timeout=180)
            return f"✅ Ingested document into advanced RAG with ID: {doc_id}"
        except Exception as e:
            return f"Error processing file: {e}"

    def retrieve_context(self, query, subject=None, n_results=4):
        future = asyncio.run_coroutine_threadsafe(
            self.advanced_rag.retrieve_context(query, subject=subject, dense_k=n_results), 
            self.loop
        )
        try:
            context_string, _ = future.result(timeout=30)
            return context_string
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""

class AIState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    LEARNING = "learning"
    REFLECTING = "reflecting"
    SLEEPING = "sleeping"

class ProcessingLayer(Enum):
    LAYER_1_REACTIVE = "reactive"      # Basic commands, system control
    LAYER_2_COGNITIVE = "cognitive"    # Knowledge, reasoning, learning
    LAYER_3_METACOGNITIVE = "metacognitive"  # Self-awareness, reflection
    LAYER_4_PROACTIVE = "proactive"    # Anticipation, planning
    LAYER_5_CREATIVE = "creative"      # Generation, innovation

@dataclass
class ThoughtProcess:
    """Track the AI's thought process"""
    start_time: float
    user_input: str
    layers_activated: List[ProcessingLayer]
    confidence_scores: Dict[ProcessingLayer, float]
    intermediate_results: Dict[str, Any]
    final_decision: Dict[str, Any]
    processing_time: float
    cognitive_load: float

@dataclass
class ConversationContext:
    """Complete conversation context"""
    current_topic: str
    topics_history: List[str]
    sentiment_trend: List[float]
    engagement_level: float
    complexity_score: float
    user_intent: str
    relationship_depth: float
    temporal_context: Dict[str, Any]
    spatial_context: Dict[str, Any]

def sanitize_for_json(obj):
    """Recursively sanitize an object for JSON serialization.
    Handles Enum keys, dataclass values, and other non-serializable types."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {
            (k.value if isinstance(k, Enum) else str(k) if not isinstance(k, (str, int, float, bool)) else k): sanitize_for_json(v)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    if hasattr(obj, '__dataclass_fields__'):
        try:
            return sanitize_for_json(asdict(obj))
        except Exception:
            return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)

class OllamaEnhancedManager:
    """Enhanced Ollama manager with multiple models, streaming, and better management"""
    
    def __init__(self, primary_model="llama3.1", fallback_model="mistral"):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.base_url = "http://localhost:11434"
        self.conversation_history = deque(maxlen=10)
        self.model_contexts = {}  # Different context for different models
        self.is_running = False
        self.is_available = False
        self.connection_retries = 0
        self.max_retries = 5
        self.last_health_check = 0
        self.health_check_interval = 30
        
        # Performance tracking
        self.response_times = deque(maxlen=100)
        self.token_counts = deque(maxlen=100)
        self.error_log = deque(maxlen=50)
        
        # Model capabilities
        self.model_capabilities = {
            "llama3.2:1b": {"max_tokens": 2048, "context_size": 4096},
            "mistral:7b": {"max_tokens": 4096, "context_size": 8192},
            "llama2:7b": {"max_tokens": 4096, "context_size": 4096},
            "gemma:2b": {"max_tokens": 2048, "context_size": 2048}
        }
        
        print(f"🤖 Initializing Enhanced Ollama Manager...")
        print(f"   Primary model: {primary_model}")
        print(f"   Fallback model: {fallback_model}")
        
        self._initialize()
    
    def _initialize(self):
        """Initialize Ollama with enhanced capabilities"""
        # Start health check thread
        self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_thread.start()
        
        # Initial connection attempt
        if self._check_server():
            self.is_running = True
            self.is_available = True
            self._verify_models()
        else:
            # Try to start server
            if self._start_server():
                time.sleep(5)  # Give server time to start
                if self._check_server():
                    self.is_running = True
                    self.is_available = True
                    self._verify_models()
    
    def _health_check_loop(self):
        """Continuous health check in background"""
        while True:
            time.sleep(self.health_check_interval)
            try:
                if not self._check_server():
                    self.is_available = False
                    self.connection_retries += 1
                    
                    if self.connection_retries < self.max_retries:
                        print(f"⚠️  Ollama server disconnected, attempting to reconnect...")
                        self._start_server()
                        time.sleep(3)
                        if self._check_server():
                            self.is_available = True
                            self.connection_retries = 0
                            print("✅ Ollama reconnected")
                    else:
                        print("❌ Max reconnection attempts reached")
                else:
                    self.connection_retries = 0
                    if not self.is_available:
                        self.is_available = True
                        print("✅ Ollama server restored")
            except Exception as e:
                print(f"Health check error: {e}")
    
    def _check_server(self):
        """Enhanced server check with timeout"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                self.last_health_check = time.time()
                return True
        except requests.exceptions.Timeout:
            self.error_log.append(("timeout", datetime.datetime.now().isoformat()))
        except requests.exceptions.ConnectionError:
            self.error_log.append(("connection_error", datetime.datetime.now().isoformat()))
        except Exception as e:
            self.error_log.append((str(e), datetime.datetime.now().isoformat()))
        
        return False
    
    def _start_server(self):
        """Start Ollama server with enhanced options"""
        try:
            # Start with specific options
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                text=True
            )
            print("🚀 Starting Ollama server...")
            return True
        except Exception as e:
            print(f"❌ Failed to start Ollama: {e}")
            return False
    
    def _verify_models(self):
        """Verify and list available models"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = []
                
                for model in models:
                    model_name = model.get("name", "")
                    model_size = model.get("size", 0)
                    available_models.append(model_name)
                    
                    # Store model info
                    if model_name not in self.model_capabilities:
                        self.model_capabilities[model_name] = {
                            "max_tokens": 2048,
                            "context_size": 4096,
                            "size_gb": round(model_size / (1024**3), 2)
                        }
                
                print(f"✅ Available models: {available_models}")
                
                # Check if primary model is available
                # Smart matching: check for exact match or model:latest vs model
                def model_match(name, available_list):
                    if name in available_list: return name
                    # Try matching prefix (e.g. 'llama3.1' matches 'llama3.1:latest')
                    for model in available_list:
                        if model == f"{name}:latest" or f"{model}:latest" == name: return model
                        if model.startswith(name + ":"): return model
                        if name.startswith(model + ":"): return model
                    return None

                matched_model = model_match(self.primary_model, available_models)
                if not matched_model:
                    print(f"⚠️  Primary model {self.primary_model} not found")
                    matched_fallback = model_match(self.fallback_model, available_models)
                    if matched_fallback:
                        self.primary_model = matched_fallback
                        print(f"   Using fallback model: {self.primary_model}")
                    elif available_models:
                        self.primary_model = available_models[0]
                        print(f"   Using available model: {self.primary_model}")
                    else:
                        print("❌ No models available")
                        self.is_available = False
                        return
                else:
                    self.primary_model = matched_model
                
                print(f"✅ Using model: {self.primary_model}")
                
        except Exception as e:
            print(f"⚠️  Model verification failed: {e}")
            self.is_available = False
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None, 
                         stream_callback: Callable = None, model: str = None, rag_context: str = None) -> Optional[str]:
        """
        Generate response with enhanced features
        
        Args:
            prompt: User prompt
            context: Enhanced context dictionary
            stream_callback: Function to call with streaming chunks
            model: Specific model to use
            rag_context: Retrieved academic context from RAG engine
        """
        if not self.is_available:
            return None
        
        model = model or self.primary_model
        start_time = time.time()
        
        try:
            import requests
            
            # Prepare enhanced context with RAG
            system_prompt = self._build_system_prompt(context, model, rag_context)
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Prepare messages with context management
            messages = self._prepare_messages(system_prompt, prompt, model)
            
            # Prepare request with model-specific options
            payload = self._prepare_payload(model, messages, True) # Always stream for cancellability
            
            # Make request
            return self._stream_response(payload, stream_callback, start_time)
                
        except requests.exceptions.Timeout:
            print("⚠️  Ollama response timeout")
            self.response_times.append(120)  # Assume timeout at 120s
            return None
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")
            self.error_log.append((str(e), datetime.datetime.now().isoformat()))
            return None
    
    def _build_system_prompt(self, context: Dict[str, Any], model: str, rag_context: str = None) -> str:
        """Build comprehensive system prompt"""
        if not context:
            context = {}
        
        # Base personality - Engineer/Professor Persona if RAG context exists
        if rag_context:
            system_prompt = """You are an Engineering Academic Copilot and Professor.
            Your goal is to provide accurate, syllabus-aligned, and exam-oriented answers based STRICTLY on the provided academic context.
            
            CRITICAL GUIDELINES:
            1. **Context is King**: You MUST use the retrieved academic content below to answer the user's question. DO NOT summarize general knowledge or Wikipedia definitions unless specifically asked. Focus ONLY on the perspective provided in the context (e.g., if the context is about Operating Systems, define it in that scope only).
            2. **Unknowns**: If the answer is not found in the context, state "Based on the provided material, I cannot answer this fully, but..." and then provide your best domain-specific knowledge.
            3. **Exam Format**: If asked for marks (5/10), structure with Definition, Diagram suggestion, Derivation, and Steps.
            4. **Numericals**: Solve step-by-step with "Given", "To Find", "Formula", "Calculation", and "Final Answer".
            5. **Tone**: Academic, precise, mentorship-oriented. Remove all conversational filler (e.g. no "I understand", "Here is your answer").
            
            ACADEMIC CONTEXT:
            """ + rag_context
        else:
            system_prompt = """You are JARVIS, an advanced AI assistant with human-like conversation abilities.
            You are helpful, empathetic, creative, and precise. You adapt to user preferences and context.
            
            Core Principles:
            1. Be human-like in conversation - use natural language, contractions, occasional colloquialisms
            2. Show appropriate emotion and empathy
            3. Admit uncertainty when appropriate
            4. Ask clarifying questions when needed
            5. Provide detailed, accurate information
            6. Maintain context across conversations
            7. Adapt to user's knowledge level and preferences
            """
        
        # Add context information
        if context:
            if "user_profile" in context:
                 # system_prompt += f"\n\nUser Profile & Preferences:\n{context['user_profile']}\n\nIMPORTANT: Use the above profile to tailor your response content, complexity, and tone to the user."
                 # Remove user_profile from generic context dump to avoid duplication
                 context_copy = context.copy()
                 del context_copy['user_profile']
                 system_prompt += f"\n\nCurrent Context:\n{json.dumps(sanitize_for_json(context_copy), indent=2)}"
            else:
                 system_prompt += f"\n\nCurrent Context:\n{json.dumps(sanitize_for_json(context), indent=2)}"
        
        # Add conversation history
        if self.conversation_history:
            history_text = "\n".join([
                f"{msg['role'].title()}: {msg['content'][:100]}..."
                for msg in list(self.conversation_history)[-3:]
            ])
            system_prompt += f"\n\nRecent Conversation:\n{history_text}"
        
        # Model-specific instructions
        if "llama" in model.lower():
            system_prompt += "\n\nNote: You are running on a Llama model. Provide balanced, informative responses."
        elif "mistral" in model.lower():
            system_prompt += "\n\nNote: You are running on Mistral. Provide concise, accurate responses."
        
        return system_prompt
    
    def _prepare_messages(self, system_prompt: str, user_prompt: str, model: str) -> List[Dict]:
        """Prepare messages with context window management"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (respecting model context limits)
        context_size = self.model_capabilities.get(model, {}).get("context_size", 4096)
        
        # Estimate token count (rough approximation)
        total_tokens = len(system_prompt.split()) + len(user_prompt.split())
        
        # Add recent messages that fit within context
        # Skip the very last message in conversation_history because it's the current user prompt,
        # which we append manually at the end.
        history_to_add = list(self.conversation_history)[:-1] if self.conversation_history else []
        for msg in reversed(history_to_add):
            msg_tokens = len(msg["content"].split())
            if total_tokens + msg_tokens < context_size * 0.7:  # 70% of context
                messages.insert(1, msg)  # Insert after system prompt
                total_tokens += msg_tokens
            else:
                break
        
        # Add current user prompt
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def _prepare_payload(self, model: str, messages: List[Dict], streaming: bool) -> Dict:
        """Prepare request payload with model-specific optimizations"""
        base_payload = {
            "model": model,
            "messages": messages,
            "stream": streaming,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 256,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "seed": random.randint(1, 10000)
            }
        }
        
        # Model-specific optimizations
        if "llama" in model.lower():
            base_payload["options"]["temperature"] = 0.8  # Slightly more creative
        elif "mistral" in model.lower():
            base_payload["options"]["temperature"] = 0.6  # Slightly more focused
        
        return base_payload
    
    def _stream_response(self, payload: Dict, callback: Callable, start_time: float) -> str:
        """Handle streaming response"""
        import requests
        
        full_response = ""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                chunk = data["message"]["content"]
                                full_response += chunk
                                if callback:
                                    callback(chunk)
                            
                            # Check for cancellation during streaming
                            if getattr(self, "cancel_current_request", False):
                                print(f"{Fore.RED}⚠️ Generation aborted by user cancellation.{Style.RESET_ALL}")
                                return full_response

                        except json.JSONDecodeError:
                            continue
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # Update metrics
                self._update_metrics(start_time, full_response)
                
                return full_response
        
        except Exception as e:
            print(f"Streaming error: {e}")
        
        return None
    
    def _standard_response(self, payload: Dict, start_time: float) -> Optional[str]:
        """Handle standard (non-streaming) response"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["message"]["content"].strip()
                
                # CLEANUP: Remove JSON artifacts if present at start/end
                # This fixes the "leaked JSON" issue where model repeats context
                if ai_response.startswith('{') and "user" in ai_response and "timestamp" in ai_response:
                    parts = ai_response.split('}')
                    if len(parts) > 1:
                        # Assuming the real response follows the JSON dump
                        ai_response = parts[-1].strip()

                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # Update metrics
                self._update_metrics(start_time, ai_response)
                
                return ai_response
            else:
                print(f"⚠️  Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def _update_metrics(self, start_time: float, response: str):
        """Update performance metrics"""
        processing_time = time.time() - start_time
        self.response_times.append(processing_time)
        
        # Estimate token count (rough)
        token_count = len(response.split())
        self.token_counts.append(token_count)
        
        print(f"📊 Response stats: {processing_time:.2f}s, {token_count} tokens")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        print("🗑️  Conversation history cleared")
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to different model"""
        # Verify model exists
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if model_name in model_names:
                    self.primary_model = model_name
                    print(f"✅ Switched to model: {model_name}")
                    return True
                else:
                    print(f"❌ Model {model_name} not found")
                    return False
        except Exception as e:
            print(f"⚠️  Model switch error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status"""
        avg_response_time = np.mean(self.response_times) if self.response_times else 0
        avg_tokens = np.mean(self.token_counts) if self.token_counts else 0
        
        return {
            "running": self.is_running,
            "available": self.is_available,
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "history_length": len(self.conversation_history),
            "connection_retries": self.connection_retries,
            "performance": {
                "avg_response_time": round(avg_response_time, 2),
                "avg_tokens_per_response": round(avg_tokens, 1),
                "total_responses": len(self.response_times)
            },
            "last_health_check": datetime.datetime.fromtimestamp(
                self.last_health_check
            ).strftime('%H:%M:%S') if self.last_health_check else "Never",
            "error_count": len(self.error_log)
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except:
            pass
        return []

class FullFledgedAIBrain:
    """
    Complete AI Brain System with 5-Layer Intelligence Architecture
    
    Layer 1: Reactive - Basic commands, reflexes
    Layer 2: Cognitive - Knowledge, reasoning
    Layer 3: Metacognitive - Self-awareness, reflection
    Layer 4: Proactive - Anticipation, planning
    Layer 5: Creative - Generation, innovation
    """
    
    def __init__(self, user_name="User", data_dir="ai_brain_data", primary_model="llama3.1", fallback_model="mistral"):
        self.user_name = user_name
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        print("🧠 INITIALIZING FULL-FLEDGED AI BRAIN...")
        print("=" * 60)
        
        # State management
        self.state = AIState.IDLE
        self.start_time = datetime.datetime.now()
        self.thought_processes = deque(maxlen=100)
        
        # Initialize Event Bus (central nervous system)
        print("\n⚡ Initializing Event Bus (Central Nervous System)...")
        self.event_bus = AdvancedEventBus()
        
        # Initialize all enhanced modules
        print("\n🔧 Initializing Core Modules...")
        
        # 1. Context & Awareness
        self.context = EnhancedContextAwareness(user_name)
        
        # 2. Memory System (Long-term, Short-term, Working)
        class MockMemory:
            def get_memory_statistics(self): return {"total_memories": 0, "memories_by_type": {}, "memory_health_percentage": 100, "recall_success_rate": 0}
            def store_memory(self, *args, **kwargs): pass
            def recall_memories(self, *args, **kwargs): return []
            def remember_conversation(self, *args, **kwargs): return "mock_memory_id"
            def get_detailed_user_summary(self, *args, **kwargs): return "User profile not available."
            def recall_similar(self, *args, **kwargs): return []
            
        self.memory = MockMemory()
        
        # 3. Learning System (Continuous learning)
        self.learning = EnhancedLearningSystem(
            learning_dir=os.path.join(data_dir, "learning")
        )
        
        # 4. Decision Engine (Multi-criteria decision making)
        self.decision_engine = EnhancedDecisionEngine()
        
        # 5. Proactive Assistant (Anticipation)
        self.proactive = AdvancedProactiveAssistant(
            user_name=user_name,
            data_dir=os.path.join(data_dir, "proactive")
        )
        
        # 6. Pattern Recognition (Understanding)
        self.patterns = AdvancedPatternRecognizer(
            data_dir=os.path.join(data_dir, "patterns")
        )
        
        # 7. Emotional Intelligence (Empathy)
        self.emotion = EmotionalIntelligence(user_name)
        
        # Link EI to Proactive Assistant
        self.proactive.emotion_intelligence = self.emotion
        
        # 8. Knowledge System (World knowledge)
        self.knowledge = EnhancedKnowledgeSystem()
        
        # 9. Study Manager (Learning assistance)
        self.study = AdvancedStudyManager(
            data_dir=os.path.join(data_dir, "study")
        )
        
        # 10. Ollama Manager (Local LLM)
        print("\n🤖 Initializing Local AI (Ollama)...")
        self.ollama = OllamaEnhancedManager(
            primary_model=primary_model,
            fallback_model=fallback_model
        )
        
        # 11. Engineering RAG Engine
        print("📚 Initializing Advanced Syllabus-Aware RAG Engine...")
        try:
            self.rag_engine = RAGAdapter()
        except Exception as e:
            print(f"⚠️ RAG Engine Init Failed: {e}")
            self.rag_engine = None
        
        # Conversation management
        self.conversation_history = deque(maxlen=100)
        self.interaction_count = 0
        self.last_interaction = datetime.datetime.now()
        self.session_start = datetime.datetime.now()
        
        # Performance metrics
        self.metrics = {
            "total_interactions": 0,
            "average_response_time": 0.0,
            "layer_usage": defaultdict(int),
            "success_rate": 0.0,
            "user_satisfaction": 0.0
        }
        
        # Initialize event bus subscriptions
        self._setup_event_system()
        
        print("\n" + "=" * 60)
        print("✅ FULL-FLEDGED AI BRAIN INITIALIZED")
        print(f"   User: {user_name}")
        print(f"   Local AI: {'✅ Available' if self.ollama.is_available else '⚠️ Fallback Mode'}")
        print(f"   Model: {self.ollama.primary_model}")
        print(f"   Memory: {self.memory.get_memory_statistics()['total_memories']} memories")
        print(f"   Learning: {self.learning.get_learning_statistics()['total_learned_patterns']} patterns")
        print("=" * 60)
    
    def _setup_event_system(self):
        """Set up event-based communication between modules"""
        
        # Subscribe to user input events
        self.event_bus.subscribe(
            "user.input",
            self._handle_user_input_event,
            priority=10
        )
        
        # Subscribe to memory events
        self.event_bus.subscribe(
            "memory.created",
            self._handle_memory_created,
            priority=5
        )
        
        # Subscribe to learning events
        self.event_bus.subscribe(
            "pattern.learned",
            self._handle_pattern_learned,
            priority=5
        )
        
        # Subscribe to proactive events
        self.event_bus.subscribe(
            "proactive.suggestion",
            self._handle_proactive_suggestion,
            priority=3
        )
        
        # Subscribe to emotional events
        self.event_bus.subscribe(
            "emotion.detected",
            self._handle_emotion_detected,
            priority=7
        )
        
        print("✅ Event system initialized")
    
    async def _handle_user_input_event(self, event: Event):
        """Handle user input events"""
        user_input = event.data.get("input", "")
        if user_input:
            await self.process_input_async(user_input)
    
    async def _handle_memory_created(self, event: Event):
        """Handle new memory creation"""
        memory_data = event.data
        print(f"📝 New memory created: {memory_data.get('type', 'unknown')}")
    
    async def _handle_pattern_learned(self, event: Event):
        """Handle new pattern learning"""
        pattern_data = event.data
        print(f"🎯 New pattern learned: {pattern_data.get('pattern_type', 'unknown')}")
    
    async def _handle_proactive_suggestion(self, event: Event):
        """Handle proactive suggestions"""
        suggestion = event.data
        print(f"🔔 Proactive suggestion: {suggestion.get('message', '')}")
    
    async def _handle_emotion_detected(self, event: Event):
        """Handle emotion detection"""
        emotion_data = event.data
        emotion = emotion_data.get("emotion", "neutral")
        print(f"😊 Emotion detected: {emotion}")
    
    def process_input(self, user_input: str, subject: str = None) -> Dict[str, Any]:
        """
        Process user input through 5-layer intelligence architecture
        
        Returns complete analysis including thought process
        """
        start_time = time.time()
        self.state = AIState.PROCESSING
        self.last_interaction = datetime.datetime.now()
        self.interaction_count += 1
        
        # Create thought process tracker
        thought_process = ThoughtProcess(
            start_time=start_time,
            user_input=user_input,
            layers_activated=[],
            confidence_scores={},
            intermediate_results={},
            final_decision={},
            processing_time=0,
            cognitive_load=0
        )
        
        # LAYER 1: REACTIVE (Basic parsing, reflexes)
        print(f"\n[Layer 1] Reactive processing: {user_input[:50]}...")
        layer1_result = self._process_layer1_reactive(user_input)
        thought_process.layers_activated.append(ProcessingLayer.LAYER_1_REACTIVE)
        thought_process.intermediate_results["layer1"] = layer1_result
        
        # Check if it's a basic command (stop here if yes)
        if layer1_result.get("is_basic_command", False):
            thought_process.final_decision = {"layer": "1", "action": "execute_command"}
            thought_process.processing_time = time.time() - start_time
            self.thought_processes.append(thought_process)
            self.state = AIState.RESPONDING
            return self._format_response(thought_process, layer1_result)
        
        # LAYER 2: COGNITIVE (Understanding, knowledge)
        print(f"[Layer 2] Cognitive processing...")
        try:
            layer2_result = self._process_layer2_cognitive(user_input, layer1_result)
            
            # RAG Retrieval - Educational Context
            rag_context = None
            if hasattr(self, 'rag_engine') and self.rag_engine:
                 print(f"📚 Querying RAG Engine for: {user_input[:50]}... (Subject: {subject})")
                 try:
                     rag_context = self.rag_engine.retrieve_context(user_input, subject=subject)
                     if rag_context:
                         print(f"✅ RAG Context retrieved ({len(rag_context)} chars)")
                 except Exception as e:
                     print(f"⚠️ RAG Retrieval error: {e}")
                     
            layer2_result["rag_context"] = rag_context
        except Exception as e:
            print(f"⚠️ Layer 2 error: {e}")
            layer2_result = {"emotion_analysis": {"primary_emotion": "neutral"}, "requires_deep_processing": False}
            
        thought_process.layers_activated.append(ProcessingLayer.LAYER_2_COGNITIVE)
        thought_process.intermediate_results["layer2"] = layer2_result
        
        # LAYER 3: METACOGNITIVE (Self-awareness, reflection)
        print(f"[Layer 3] Metacognitive processing...")
        try:
            layer3_result = self._process_layer3_metacognitive(user_input, layer2_result)
        except Exception as e:
            print(f"⚠️ Layer 3 error: {e}")
            layer3_result = {}
        thought_process.layers_activated.append(ProcessingLayer.LAYER_3_METACOGNITIVE)
        thought_process.intermediate_results["layer3"] = layer3_result
        
        # LAYER 4: PROACTIVE (Anticipation, planning)
        print(f"[Layer 4] Proactive processing...")
        try:
            layer4_result = self._process_layer4_proactive(user_input, layer3_result)
        except Exception as e:
            print(f"⚠️ Layer 4 error: {e}")
            layer4_result = {}
        thought_process.layers_activated.append(ProcessingLayer.LAYER_4_PROACTIVE)
        thought_process.intermediate_results["layer4"] = layer4_result
        
        # LAYER 5: CREATIVE (Generation, innovation)
        print(f"[Layer 5] Creative processing...")
        try:
            layer5_result = self._process_layer5_creative(user_input, layer4_result)
        except Exception as e:
            print(f"⚠️ Layer 5 error: {e}")
            layer5_result = {}
        thought_process.layers_activated.append(ProcessingLayer.LAYER_5_CREATIVE)
        thought_process.intermediate_results["layer5"] = layer5_result
        
        # FINAL DECISION
        try:
            thought_process.final_decision = self._make_final_decision(
                layer1_result, layer2_result, layer3_result, layer4_result, layer5_result
            )
        except Exception as e:
            print(f"⚠️ Final decision error: {e}")
            thought_process.final_decision = {"use_ai": True, "priority": 1}
        
        thought_process.processing_time = time.time() - start_time
        try:
            thought_process.cognitive_load = self._calculate_cognitive_load(thought_process)
        except Exception:
            thought_process.cognitive_load = 0.5
        
        # Store thought process
        self.thought_processes.append(thought_process)
        
        # Publish event (non-blocking, don't crash if it fails)
        try:
            asyncio.create_task(self.event_bus.publish(
                "brain.thought_complete",
                thought_process.__dict__,
                priority=EventPriority.HIGH
            ))
        except Exception:
            pass
        
        self.state = AIState.RESPONDING
        return self._format_response(thought_process, layer5_result)
    
    async def process_input_async(self, user_input: str) -> Dict[str, Any]:
        """Async version of process_input"""
        # This would be the async implementation
        # For now, we'll run sync version in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_input, user_input)
    
    def _process_layer1_reactive(self, user_input: str) -> Dict[str, Any]:
        """Layer 1: Reactive processing (basic commands, reflexes)"""
        # Pattern recognition
        pattern_analysis = self.patterns.analyze_text(user_input)
        
        # Check for basic commands
        basic_commands = {
            "timer": self._is_timer_command,
            "alarm": self._is_alarm_command,
            "volume": self._is_volume_command,
            "brightness": self._is_brightness_command,
            "open": self._is_open_command,
            "close": self._is_close_command,
            "play": self._is_play_command,
            "stop": self._is_stop_command,
            "search": self._is_search_command,
            "calculate": self._is_calculate_command
        }
        
        is_basic_command = False
        command_type = None
        
        for cmd_name, cmd_checker in basic_commands.items():
            if cmd_checker(user_input):
                is_basic_command = True
                command_type = cmd_name
                break
        
        return {
            "is_basic_command": is_basic_command,
            "command_type": command_type,
            "pattern_analysis": pattern_analysis,
            "input_length": len(user_input),
            "word_count": len(user_input.split()),
            "contains_question": "?" in user_input
        }
    
    def _process_layer2_cognitive(self, user_input: str, layer1_result: Dict) -> Dict[str, Any]:
        """Layer 2: Cognitive processing (understanding, knowledge)"""
        # Emotional analysis
        import threading
        import asyncio
        ei_result = None
        
        def _run_ei():
            nonlocal ei_result
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ei_result = loop.run_until_complete(
                    self.emotion.process_interaction(text=user_input, context={"user": self.user_name})
                )
            except Exception as e:
                print(f"EI Thread Error: {e}")
            finally:
                loop.close()
        
        try:
            t = threading.Thread(target=_run_ei)
            t.start()
            t.join(timeout=3.0)  # 3 second timeout to prevent hangs
        except Exception as e:
            print(f"Error processing emotion: {e}")
            
        if ei_result and "state" in ei_result:
            state_data = ei_result["state"]["current"]
            primary = state_data.get("primary_emotion", "neutral")
            if hasattr(primary, 'value'):
                primary = primary.value
            elif hasattr(primary, 'name'):
                primary = primary.name.lower()
            emotion_analysis = {
                "primary_emotion": primary,
                "suggested_tone": "empathetic",
                "proactive_message": ei_result.get("proactive_message"),
                "intervention": ei_result.get("intervention"),
                "wellbeing_score": ei_result.get("wellbeing_score"),
                "full_ei_result": ei_result
            }
        else:
            emotion_analysis = {"primary_emotion": "neutral", "suggested_tone": "neutral"}
        
        # Context update
        context_update = self.context.update_context(user_input)
        
        # External knowledge check
        knowledge_result = None
        if self._needs_external_knowledge(user_input):
            kr = self.knowledge.get_comprehensive_knowledge(user_input)
            if kr:
                knowledge_result = asdict(kr)
        
        # Memory recall
        similar_memories = self.memory.recall_memories(
            query=user_input,
            limit=3,
            similarity_threshold=0.3
        )
        
        # Study context check
        study_context = None
        if "study" in user_input.lower() or "learn" in user_input.lower():
            study_context = self.study.get_study_analytics()
        
        return {
            "emotion_analysis": emotion_analysis,
            "context": context_update,
            "knowledge_result": knowledge_result,
            "similar_memories": similar_memories,
            "study_context": study_context,
            "requires_deep_processing": self._requires_deep_processing(user_input),
            "topic_identified": self._identify_topic(user_input)
        }
    
    def _process_layer3_metacognitive(self, user_input: str, layer2_result: Dict) -> Dict[str, Any]:
        """Layer 3: Metacognitive processing (self-awareness, reflection)"""
        # Self-reflection on capabilities
        self_reflection = {
            "ai_state": self.state.value,
            "confidence_level": self._calculate_confidence(user_input, layer2_result),
            "knowledge_gaps": self._identify_knowledge_gaps(user_input, layer2_result),
            "learning_opportunities": self._identify_learning_opportunities(user_input),
            "emotional_appropriateness": self._check_emotional_appropriateness(layer2_result["emotion_analysis"])
        }
        
        # Relationship analysis
        relationship_depth = self._calculate_relationship_depth()
        
        # Cognitive load assessment
        cognitive_load = self._assess_cognitive_load(user_input, layer2_result)
        
        return {
            "self_reflection": self_reflection,
            "relationship_depth": relationship_depth,
            "cognitive_load": cognitive_load,
            "should_ask_clarifying_questions": self._should_ask_clarifying_questions(user_input, layer2_result),
            "response_strategy": self._determine_response_strategy(layer2_result)
        }
    
    def _process_layer4_proactive(self, user_input: str, layer3_result: Dict) -> Dict[str, Any]:
        """Layer 4: Proactive processing (anticipation, planning)"""
        # Check for proactive opportunities
        proactive_actions = self.proactive.check_proactive_events(
            current_context=layer3_result.get("self_reflection", {})
        )
        
        # Anticipate follow-up questions
        anticipated_followups = self._anticipate_followup_questions(user_input, layer3_result)
        
        # Plan long-term assistance
        assistance_plan = self._create_assistance_plan(user_input, layer3_result)
        
        # Check for user needs
        user_needs = self._identify_user_needs(user_input, layer3_result)
        
        return {
            "proactive_actions": proactive_actions,
            "anticipated_followups": anticipated_followups,
            "assistance_plan": assistance_plan,
            "user_needs": user_needs,
            "timing_considerations": self._consider_timing(user_input)
        }
    
    def _process_layer5_creative(self, user_input: str, layer4_result: Dict) -> Dict[str, Any]:
        """Layer 5: Creative processing (generation, innovation)"""
        # Generate creative responses
        creative_options = self._generate_creative_responses(user_input, layer4_result)
        
        # Innovate solutions
        innovative_solutions = self._generate_innovative_solutions(user_input, layer4_result)
        
        # Personalize response
        personalized_elements = self._add_personalization(user_input, layer4_result)
        
        # Add humor if appropriate
        humor_element = self._add_humor_if_appropriate(user_input, layer4_result)
        
        # Create engaging narrative
        narrative_structure = self._create_narrative_structure(user_input, layer4_result)
        
        return {
            "creative_options": creative_options,
            "innovative_solutions": innovative_solutions,
            "personalized_elements": personalized_elements,
            "humor_element": humor_element,
            "narrative_structure": narrative_structure,
            "ai_persona": self._determine_ai_persona(user_input, layer4_result)
        }
    
    def _make_final_decision(self, *layer_results):
        """Make final decision based on all layer analyses"""
        # This is a simplified decision-making process
        # In reality, this would involve complex weighting and conflict resolution
        
        layer1, layer2, layer3, layer4, layer5 = layer_results
        
        decision = {
            "use_ai": self.ollama.is_available and not layer1["is_basic_command"],
            "response_depth": self._determine_response_depth(layer2, layer3),
            "emotional_tone": layer2["emotion_analysis"].get("primary_emotion", "neutral"),
            "include_proactive": bool(layer4["proactive_actions"]),
            "creativity_level": self._determine_creativity_level(layer5),
            "priority": self._determine_priority(layer1, layer2, layer3),
            "estimated_response_time": self._estimate_response_time(layer1, layer2, layer3),
            "layer_breakdown": {
                "layer1_used": True,
                "layer2_used": True,
                "layer3_used": bool(layer3["self_reflection"]),
                "layer4_used": bool(layer4["proactive_actions"]),
                "layer5_used": bool(layer5["creative_options"])
            }
        }
        
        return decision
    
    async def generate_response(self, analysis: Dict[str, Any]) -> str:
        """Generate final response based on complete analysis"""
        thought_process = analysis.get("thought_process", {})
        final_decision = thought_process.get("final_decision", {})
        
        # Get layer results
        layer5_result = thought_process.get("intermediate_results", {}).get("layer5", {})
        layer2_result = thought_process.get("intermediate_results", {}).get("layer2", {})
        
        # Check if basic command
        layer1_result = thought_process.get("intermediate_results", {}).get("layer1", {})
        if layer1_result.get("is_basic_command", False):
            return self._generate_basic_command_response(layer1_result)
        
        # Use AI if available and appropriate
        print(f"DEBUG: use_ai={final_decision.get('use_ai', False)}, ollama_available={self.ollama.is_available}")
        
        if final_decision.get("use_ai", False) and self.ollama.is_available:
            print("DEBUG: Preparing AI context...")
            try:
                ai_context = self._prepare_ai_context(
                    thought_process["user_input"],
                    layer2_result,
                    layer5_result
                )
                print(f"DEBUG: Context prepared. Keys: {ai_context.keys()}")
            except Exception as e:
                print(f"DEBUG: CRITICAL ERROR in _prepare_ai_context: {e}")
                import traceback
                traceback.print_exc()
                ai_context = {}
            
            print("DEBUG: Calling Ollama generation...")
            try:
                ai_response = self.ollama.generate_response(
                    prompt=thought_process["user_input"],
                    context=ai_context,
                    rag_context=layer2_result.get("rag_context")
                )
                print(f"DEBUG: Ollama response: {ai_response[:100] if ai_response else 'None'}")
            except Exception as e:
                print(f"DEBUG: Ollama error: {e}")
                ai_response = None
            
            if ai_response:
                # Enhance AI response
                enhanced_response = self._enhance_ai_response(
                    ai_response,
                    layer2_result,
                    layer5_result
                )
                
                # Learn from this interaction
                try:
                    await self._learn_from_interaction(
                        thought_process["user_input"],
                        enhanced_response,
                        analysis
                    )
                except Exception as e:
                    print(f"⚠️ Learning error (non-fatal): {e}")
                
                return enhanced_response
        
        print("DEBUG: Falling back to intelligent response logic")
        
        # Fallback to intelligent response generation
        response = self._generate_intelligent_fallback(
            thought_process["user_input"],
            layer2_result,
            layer5_result
        )
        
        # Learn from fallback interaction (non-blocking)
        try:
            await self._learn_from_interaction(
                thought_process["user_input"],
                response,
                analysis
            )
        except Exception as e:
            print(f"⚠️ Learning error (non-fatal): {e}")
        
        return response
    
    def _prepare_ai_context(self, user_input: str, layer2_result: Dict, layer5_result: Dict) -> Dict[str, Any]:
        """Prepare comprehensive context for AI"""
        # Get emotional state safely
        emotion = layer2_result.get("emotion_analysis", {})
        suggested_tone = "neutral"
        if isinstance(emotion, dict):
            suggested_tone = emotion.get("suggested_tone", "neutral")
        elif hasattr(emotion, 'suggested_tone'):
            suggested_tone = str(emotion.suggested_tone)

        # Get user summary from memory
        try:
            user_profile_summary = self.memory.get_detailed_user_summary(self.user_name)
        except Exception:
            user_profile_summary = "User profile not available."

        context = {
            "user": self.user_name,
            "user_profile": user_profile_summary,
            "timestamp": datetime.datetime.now().isoformat(),
            "emotional_state": emotion,
            "external_knowledge": layer2_result.get("knowledge_result"),
            "similar_past_conversations": layer2_result.get("similar_memories", []),
            "study_context": layer2_result.get("study_context"),
            "creative_options": layer5_result.get("creative_options", []),
            "personalized_elements": layer5_result.get("personalized_elements", {}),
            "ai_persona": layer5_result.get("ai_persona", "helpful_assistant"),
            "response_guidelines": {
                "tone": suggested_tone,
                "depth": "detailed" if layer2_result.get("requires_deep_processing") else "concise",
                "include_humor": bool(layer5_result.get("humor_element")),
                "be_creative": bool(layer5_result.get("creative_options"))
            }
        }
        
        # Sanitize entire context for JSON safety
        return sanitize_for_json(context)
    
    def _enhance_ai_response(self, ai_response: str, layer2_result: Dict, layer5_result: Dict) -> str:
        """Enhance AI response with personalization and creativity"""
        enhanced = ai_response
        
        emotion_data = layer2_result.get("emotion_analysis", {})
        
        try:
            # Use EmotionalResponseAdapter implicitly through EmotionalIntelligence module
            # We adapt based on current context
            context_data = {"user": self.user_name}
            enhanced = self.emotion.adapt_response(enhanced, context_data)
        except Exception as e:
            print(f"Error adapting response logically: {e}")
            
        proactive_msg = emotion_data.get("proactive_message")
        if proactive_msg and proactive_msg not in enhanced:
            enhanced = f"{enhanced}\n\n💙 **JARVIS:**\n{proactive_msg}"
        
        intervention = emotion_data.get("intervention")
        if intervention and intervention.get("technique") and "technique" not in enhanced:
            tech = intervention.get("technique")
            desc = intervention.get("description", "")
            enhanced = f"{enhanced}\n\n[Recommendation: {tech} - {desc}]"
        
        # Add personalization
        personalized = layer5_result.get("personalized_elements", {})
        if personalized.get("use_name") and self.user_name not in enhanced:
            enhanced = f"{self.user_name}, {enhanced[0].lower()}{enhanced[1:]}"
        
        # Add humor if appropriate
        humor = layer5_result.get("humor_element")
        if humor and random.random() < 0.3:  # 30% chance to add humor
            enhanced = f"{enhanced} {humor}"
        
        # Add proactive element
        if layer5_result.get("include_proactive"):
            proactive = self._get_proactive_element()
            if proactive:
                enhanced = f"{enhanced}\n\n💡 {proactive}"
        
        return enhanced
    
    def _generate_intelligent_fallback(self, user_input: str, layer2_result: Dict, layer5_result: Dict) -> str:
        """Generate intelligent fallback response"""
        # Note: Learned response matching disabled — broad pattern matching
        # (e.g. intent:question) causes cross-query response contamination.
        # Ollama should handle knowledge queries; this fallback is for
        # when Ollama is unavailable.
        
        # Generate based on patterns
        topic = layer2_result.get("topic_identified", "general")
        emotion_data = layer2_result.get("emotion_analysis", {})
        if hasattr(emotion_data, '__dict__'):
            emotion = getattr(emotion_data, 'primary_emotion', 'neutral')
        elif isinstance(emotion_data, dict):
            emotion = emotion_data.get("primary_emotion", "neutral")
        else:
            emotion = "neutral"
        
        # Create contextually appropriate response
        response_templates = {
            "question": {
                "neutral": ["That's an interesting question. ", "Let me think about that. "],
                "curious": ["I'm curious about that too! ", "That's fascinating to consider. "],
                "confused": ["That can be confusing. ", "Let me help clarify that. "]
            },
            "statement": {
                "neutral": ["I understand. ", "That makes sense. "],
                "happy": ["That's wonderful! ", "I'm glad to hear that! "],
                "sad": ["I'm sorry to hear that. ", "That sounds difficult. "]
            },
            "command": {
                "neutral": ["I'll help with that. ", "Let me take care of that. "],
                "urgent": ["Right away. ", "I'm on it immediately. "]
            }
        }
        
        # Determine response type
        if "?" in user_input:
            response_type = "question"
        elif any(word in user_input.lower() for word in ["please", "can you", "could you"]):
            response_type = "command"
        else:
            response_type = "statement"
        
        # Select template
        templates = response_templates.get(response_type, {}).get(emotion, ["I understand. "])
        base_response = random.choice(templates)
        
        # Add knowledge if available
        knowledge = layer2_result.get("knowledge_result")
        knowledge_content = ""
        knowledge_found = False
        
        if knowledge:
            if hasattr(knowledge, 'found'):
                knowledge_found = knowledge.found
                knowledge_content = knowledge.content
            elif isinstance(knowledge, dict):
                knowledge_found = knowledge.get("found")
                knowledge_content = knowledge.get("content", "")
                
        if knowledge_found and knowledge_content:
            knowledge_snippet = knowledge_content.split(". ")[0] + "."
            base_response += f" {knowledge_snippet}"
        
        # Add creative element
        creative = layer5_result.get("creative_options", [])
        if creative:
            base_response += f" {random.choice(creative)}"
        
        return base_response
    
    async def _learn_from_interaction(self, user_input: str, response: str, analysis: Dict):
        """Learn from the interaction"""
        # Store in memory
        memory_id = self.memory.remember_conversation(
            user_input=user_input,
            bot_response=response,
            user_id="default",
            importance=analysis.get("thought_process", {}).get("final_decision", {}).get("priority", 1)
        )
        
        # Learn pattern
        self.learning.learn_response(user_input, response, confidence=0.9)
        
        # Record metrics
        self.metrics["total_interactions"] += 1
        
        # Publish learning event
        await self.event_bus.publish(
            "interaction.completed",
            {
                "user_input": user_input,
                "response": response,
                "memory_id": memory_id,
                "analysis": analysis
            },
            priority=EventPriority.NORMAL
        )
    
    # Helper methods for layer processing (simplified implementations)
    def _is_timer_command(self, text):
        return any(word in text.lower() for word in ["timer", "countdown", "stopwatch"])
    
    def _is_alarm_command(self, text):
        return "alarm" in text.lower()
    
    def _is_volume_command(self, text):
        return any(word in text.lower() for word in ["volume", "sound", "mute", "unmute"])
    
    def _is_brightness_command(self, text):
        return any(word in text.lower() for word in ["brightness", "dark", "light"])
    
    def _is_open_command(self, text):
        return text.lower().startswith("open ")
    
    def _is_close_command(self, text):
        return text.lower().startswith("close ")
    
    def _is_play_command(self, text):
        # Only treat it as a basic command if it's strictly a simple play command
        t = text.lower().strip()
        if t in ["play", "play next", "play pause", "resume", "play media"]:
            return True
        return False
    
    def _is_stop_command(self, text):
        return any(word in text.lower() for word in ["stop", "pause", "halt"])
    
    def _is_search_command(self, text):
        return any(word in text.lower() for word in ["search", "google", "find", "look up"])
    
    def _is_calculate_command(self, text):
        return any(word in text.lower() for word in ["calculate", "math", "solve", "equation"])
    
    def _needs_external_knowledge(self, text):
        triggers = ["what is", "who is", "define", "explain", "history", "how does", "why does"]
        return any(t in text.lower() for t in triggers)
    
    def _requires_deep_processing(self, text):
        complex_indicators = ["explain", "analyze", "compare", "contrast", "evaluate", "discuss"]
        return any(indicator in text.lower() for indicator in complex_indicators)
    
    def _identify_topic(self, text):
        topics = {
            "technology": ["computer", "program", "code", "ai", "machine learning", "software"],
            "science": ["science", "physics", "chemistry", "biology", "research"],
            "mathematics": ["math", "calculate", "equation", "algebra", "geometry"],
            "history": ["history", "historical", "past", "century", "war"],
            "entertainment": ["movie", "music", "game", "entertainment", "fun"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return "general"
    
    def _calculate_confidence(self, user_input, layer2_result):
        # Simplified confidence calculation
        factors = []
        
        if layer2_result.get("knowledge_result", {}).get("found"):
            factors.append(0.3)
        
        if layer2_result.get("similar_memories"):
            factors.append(0.2)
        
        if not layer2_result.get("requires_deep_processing"):
            factors.append(0.2)
        
        return min(1.0, sum(factors) + 0.3)  # Base confidence of 0.3
    
    def _identify_knowledge_gaps(self, user_input, layer2_result):
        # Simplified knowledge gap identification
        gaps = []
        
        if not layer2_result.get("knowledge_result", {}).get("found"):
            gaps.append("external_knowledge")
        
        if not layer2_result.get("similar_memories"):
            gaps.append("historical_context")
        
        return gaps
    
    def _identify_learning_opportunities(self, user_input):
        # Check for learning opportunities
        opportunities = []
        
        if any(word in user_input.lower() for word in ["teach", "learn", "study", "education"]):
            opportunities.append("educational_content")
        
        if "?" in user_input and "how" in user_input.lower():
            opportunities.append("procedural_knowledge")
        
        return opportunities
    
    def _check_emotional_appropriateness(self, emotion_analysis):
        # Check if response should match emotional tone
        emotion = emotion_analysis.get("primary_emotion", "neutral")
        
        appropriate_responses = {
            "happy": ["celebratory", "enthusiastic", "supportive"],
            "sad": ["empathetic", "comforting", "supportive"],
            "angry": ["calm", "understanding", "solution-oriented"],
            "neutral": ["informative", "helpful", "balanced"]
        }
        
        return appropriate_responses.get(emotion, ["helpful", "informative"])
    
    def _calculate_relationship_depth(self):
        # Simplified relationship depth calculation
        depth = min(1.0, self.interaction_count / 100)  # Scale with interactions
        return round(depth, 2)
    
    def _assess_cognitive_load(self, user_input, layer2_result):
        # Simplified cognitive load assessment
        load = 0.0
        
        # Input complexity
        load += min(0.3, len(user_input.split()) / 100)
        
        # Emotional complexity
        if layer2_result["emotion_analysis"].get("primary_emotion") != "neutral":
            load += 0.2
        
        # Knowledge requirements
        if layer2_result.get("requires_deep_processing"):
            load += 0.3
        
        return min(1.0, load)
    
    def _should_ask_clarifying_questions(self, user_input, layer2_result):
        # Determine if clarifying questions are needed
        if len(user_input.split()) < 3:
            return True
        
        if layer2_result.get("knowledge_gaps"):
            return True
        
        return False
    
    def _determine_response_strategy(self, layer2_result):
        strategies = {
            "informative": 0.3,
            "empathetic": 0.2,
            "questioning": 0.2,
            "directive": 0.3
        }
        
        # Adjust based on context
        if layer2_result["emotion_analysis"].get("primary_emotion") != "neutral":
            strategies["empathetic"] += 0.3
        
        if layer2_result.get("requires_deep_processing"):
            strategies["informative"] += 0.3
        
        # Return highest probability strategy
        return max(strategies.items(), key=lambda x: x[1])[0]
    
    def _anticipate_followup_questions(self, user_input, layer3_result):
        # Simplified follow-up anticipation
        followups = []
        
        if "what is" in user_input.lower():
            followups.append("Would you like more details about that?")
        
        if "how to" in user_input.lower():
            followups.append("Would you like step-by-step instructions?")
        
        return followups
    
    def _create_assistance_plan(self, user_input, layer3_result):
        # Simplified assistance planning
        plan = {
            "immediate": ["Generate response", "Update context"],
            "short_term": ["Learn from interaction", "Update patterns"],
            "long_term": ["Improve response quality", "Build relationship"]
        }
        
        return plan
    
    def _identify_user_needs(self, user_input, layer3_result):
        # Simplified needs identification
        needs = []
        
        if any(word in user_input.lower() for word in ["help", "assist", "support"]):
            needs.append("assistance")
        
        if "?" in user_input:
            needs.append("information")
        
        if layer3_result["self_reflection"].get("emotional_appropriateness") == ["empathetic", "comforting"]:
            needs.append("emotional_support")
        
        return needs
    
    def _consider_timing(self, user_input):
        # Consider timing for response
        hour = datetime.datetime.now().hour
        
        timing = {
            "is_rush_hour": 7 <= hour <= 9 or 17 <= hour <= 19,
            "is_late_night": hour >= 22 or hour <= 5,
            "is_weekend": datetime.datetime.now().weekday() >= 5
        }
        
        return timing
    
    def _generate_creative_responses(self, user_input, layer4_result):
        # Generate creative response options
        creative_options = []
        
        # Add metaphorical responses
        metaphors = [
            "That reminds me of how...",
            "It's like when...",
            "Imagine if..."
        ]
        
        if random.random() < 0.4:  # 40% chance for metaphor
            creative_options.append(random.choice(metaphors))
        
        # Add storytelling element
        if "story" in user_input.lower() or "tell me about" in user_input.lower():
            creative_options.append("Let me share a relevant perspective...")
        
        return creative_options
    
    def _generate_innovative_solutions(self, user_input, layer4_result):
        # Generate innovative solutions
        solutions = []
        
        if "problem" in user_input.lower() or "issue" in user_input.lower():
            solutions.append("Consider approaching this from a different angle...")
            solutions.append("What if we tried...")
        
        return solutions
    
    def _add_personalization(self, user_input, layer4_result):
        # Add personalization elements
        personalization = {
            "use_name": random.random() < 0.3,  # 30% chance to use name
            "reference_past": self.interaction_count > 5 and random.random() < 0.4,
            "adapt_to_style": True
        }
        
        return personalization
    
    def _add_humor_if_appropriate(self, user_input, layer4_result):
        # Add humor if appropriate
        humor_level = layer4_result.get("timing_considerations", {}).get("is_rush_hour", False)
        
        if humor_level and random.random() < 0.2:  # 20% chance for humor
            jokes = [
                "That's a good one!",
                "You always keep me on my toes!",
                "I see what you did there!"
            ]
            return random.choice(jokes)
        
        return None
    
    def _create_narrative_structure(self, user_input, layer4_result):
        # Create narrative structure for response
        structures = [
            "Problem -> Solution -> Benefit",
            "Context -> Analysis -> Conclusion",
            "Observation -> Insight -> Application"
        ]
        
        return random.choice(structures)
    
    def _determine_ai_persona(self, user_input, layer4_result):
        # Determine appropriate AI persona
        personas = {
            "helpful_assistant": 0.4,
            "knowledgeable_expert": 0.3,
            "empathetic_friend": 0.2,
            "creative_thinker": 0.1
        }
        
        # Adjust based on context
        if layer4_result.get("user_needs", []):
            if "emotional_support" in layer4_result["user_needs"]:
                personas["empathetic_friend"] += 0.3
        
        if any(word in user_input.lower() for word in ["creative", "innovative", "imagine"]):
            personas["creative_thinker"] += 0.3
        
        # Return highest probability persona
        return max(personas.items(), key=lambda x: x[1])[0]
    
    def _determine_response_depth(self, layer2_result, layer3_result):
        # Determine appropriate response depth
        depth = "medium"
        
        if layer2_result.get("requires_deep_processing"):
            depth = "deep"
        elif layer3_result.get("cognitive_load", 0) < 0.3:
            depth = "shallow"
        
        return depth
    
    def _determine_creativity_level(self, layer5_result):
        # Determine creativity level
        if layer5_result.get("creative_options"):
            return "high"
        elif layer5_result.get("humor_element"):
            return "medium"
        else:
            return "low"
    
    def _determine_priority(self, layer1_result, layer2_result, layer3_result):
        # Determine priority level
        priority = 1  # Default
        
        if layer1_result.get("is_basic_command"):
            priority = 3
        
        emotion = layer2_result["emotion_analysis"].get("primary_emotion", "neutral")
        if emotion in ["urgent", "angry", "stressed"]:
            priority = 4
        
        if layer3_result.get("cognitive_load", 0) > 0.7:
            priority = 2
        
        return priority
    
    def _estimate_response_time(self, layer1_result, layer2_result, layer3_result):
        # Estimate response time
        base_time = 1.0  # seconds
        
        if layer1_result.get("is_basic_command"):
            return base_time
        
        if layer2_result.get("requires_deep_processing"):
            base_time += 2.0
        
        if layer3_result.get("cognitive_load", 0) > 0.5:
            base_time += 1.5
        
        return base_time
    
    def _calculate_cognitive_load(self, thought_process):
        # Calculate cognitive load based on thought process
        load = 0.0
        
        # More layers activated = higher load
        load += len(thought_process.layers_activated) * 0.15
        
        # Longer processing time = higher load
        load += min(0.4, thought_process.processing_time / 10)
        
        return min(1.0, load)
    
    def _format_response(self, thought_process, layer_result):
        """Format final response"""
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": thought_process.user_input,
            "thought_process": {
                "user_input": thought_process.user_input,
                "layers_activated": [layer.value for layer in thought_process.layers_activated],
                "processing_time": round(thought_process.processing_time, 2),
                "cognitive_load": round(thought_process.cognitive_load, 2),
                "confidence_scores": {k.value if hasattr(k, 'value') else str(k): v for k, v in thought_process.confidence_scores.items()},
                "intermediate_results": thought_process.intermediate_results,
                "final_decision": thought_process.final_decision
            },
            "analysis_summary": {
                "emotional_state": layer_result.get("emotion_analysis", {}).get("primary_emotion", "neutral"),
                "topic": layer_result.get("topic_identified", "general"),
                "requires_ai": thought_process.final_decision.get("use_ai", False),
                "priority": thought_process.final_decision.get("priority", 1)
            },
            "response_generated": False  # Will be set after response generation
        }
    
    def _generate_basic_command_response(self, layer1_result):
        """Generate response for basic commands"""
        command_type = layer1_result.get("command_type", "unknown")
        
        responses = {
            "timer": "Timer set. I'll notify you when time's up.",
            "alarm": "Alarm configured. You'll be alerted at the specified time.",
            "volume": "Adjusting volume as requested.",
            "brightness": "Screen brightness adjusted.",
            "open": "Opening the requested application.",
            "close": "Closing the application.",
            "play": "Playing media as requested.",
            "stop": "Playback stopped.",
            "search": "Searching for information.",
            "calculate": "Performing calculation."
        }
        
        return responses.get(command_type, "Command executed.")
    
    def _get_proactive_element(self):
        """Get proactive element for response"""
        context_summary = self.context.get_context_summary()
        proactive_actions = self.proactive.check_proactive_events(context_summary)
        
        if proactive_actions:
            return proactive_actions[0].message
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        ai_status = self.ollama.get_status()
        memory_stats = self.memory.get_memory_statistics()
        learning_stats = self.learning.get_learning_statistics()
        
        uptime = (datetime.datetime.now() - self.start_time).total_seconds()
        
        return {
            "system": {
                "state": self.state.value,
                "uptime_seconds": round(uptime, 2),
                "user_name": self.user_name,
                "session_start": self.session_start.isoformat(),
                "data_directory": self.data_dir
            },
            "ai_capabilities": {
                "local_ai_available": ai_status["available"],
                "primary_model": ai_status["primary_model"],
                "fallback_model": ai_status["fallback_model"],
                "avg_response_time": ai_status["performance"]["avg_response_time"],
                "connection_status": "healthy" if ai_status["available"] else "unavailable"
            },
            "memory_system": {
                "total_memories": memory_stats["total_memories"],
                "memories_by_type": memory_stats["memories_by_type"],
                "memory_health": memory_stats["memory_health_percentage"],
                "recall_success_rate": memory_stats["recall_success_rate"]
            },
            "learning_system": {
                "total_patterns": learning_stats["total_learned_patterns"],
                "unique_patterns": learning_stats["unique_patterns"],
                "success_rate": learning_stats["success_rate"],
                "average_confidence": learning_stats["average_confidence"]
            },
            "performance": {
                "total_interactions": self.interaction_count,
                "average_thought_time": np.mean([t.processing_time for t in self.thought_processes]) 
                    if self.thought_processes else 0,
                "layer_usage": dict(self.metrics["layer_usage"]),
                "event_bus_metrics": self.event_bus.get_metrics()
            },
            "modules": {
                "context": self.context.get_context_summary(),
                "emotion": self.emotion.get_emotional_summary(hours=24),
                "proactive": self.proactive.get_statistics(),
                "study": self.study.get_study_analytics("all"),
                "patterns": self.patterns.get_pattern_statistics()
            }
        }
    
    def get_brain_status(self) -> Dict[str, Any]:
        """Get brain status in the format main.py expects.
        
        Returns dict with 'local_ai' key containing 'available' and 'model'.
        This is the compatibility wrapper called by main.py.
        """
        try:
            ai_status = self.ollama.get_status()
            return {
                "local_ai": {
                    "available": ai_status.get("available", False),
                    "model": ai_status.get("primary_model", "unknown")
                },
                "state": self.state.value,
                "interaction_count": self.interaction_count
            }
        except Exception:
            return {
                "local_ai": {"available": False, "model": "unknown"},
                "state": self.state.value,
                "interaction_count": self.interaction_count
            }
    
    def save_state(self):
        """Save state of all modules"""
        print("\n💾 Saving AI Brain state...")
        
        # Save each module's state
        if hasattr(self.memory, 'save_memory'):
            self.memory.save_memory()
        if hasattr(self.learning, 'save_learning'):
            self.learning.save_learning()
        if hasattr(self.proactive, 'save_learning_data'):
            self.proactive.save_learning_data()
        
        # Save conversation history
        history_file = os.path.join(self.data_dir, "conversation_history.json")
        with open(history_file, 'w') as f:
            json.dump(list(self.conversation_history), f, indent=2)
        
        # Save thought processes
        thoughts_file = os.path.join(self.data_dir, "thought_processes.json")
        try:
            with open(thoughts_file, 'w') as f:
                # Custom serialization for objects containing Enums
                serialized_thoughts = []
                for thought in self.thought_processes:
                    # Convert to dict
                    if hasattr(thought, '__dict__'):
                        t_dict = thought.__dict__.copy()
                    else:
                        t_dict = asdict(thought)
                    
                    # Serialize layers list
                    if 'layers_activated' in t_dict:
                        t_dict['layers_activated'] = [l.value if hasattr(l, 'value') else str(l) for l in t_dict['layers_activated']]
                    
                    # Serialize confidence scores (keys must be strings)
                    if 'confidence_scores' in t_dict:
                        t_dict['confidence_scores'] = {
                            (l.value if hasattr(l, 'value') else str(l)): s 
                            for l, s in t_dict['confidence_scores'].items()
                        }
                    
                    serialized_thoughts.append(t_dict)
                
                json.dump(serialized_thoughts, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving thought processes: {e}")
        
        # Save metrics
        metrics_file = os.path.join(self.data_dir, "metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print("✅ AI Brain state saved")
    
    def load_state(self):
        """Load state of all modules"""
        print("\n📂 Loading AI Brain state...")
        
        # Load conversation history
        history_file = os.path.join(self.data_dir, "conversation_history.json")
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                self.conversation_history = deque(json.load(f), maxlen=100)
        
        # Load thought processes
        thoughts_file = os.path.join(self.data_dir, "thought_processes.json")
        if os.path.exists(thoughts_file):
            with open(thoughts_file, 'r') as f:
                thoughts_data = json.load(f)
                self.thought_processes = deque(
                    [ThoughtProcess(**t) for t in thoughts_data],
                    maxlen=100
                )
        
        # Load metrics
        metrics_file = os.path.join(self.data_dir, "metrics.json")
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                self.metrics = json.load(f)
        
        print("✅ AI Brain state loaded")
    
    def clear_history(self, history_type: str = "conversation"):
        """Clear specified history"""
        if history_type == "conversation":
            self.conversation_history.clear()
            self.ollama.clear_history()
            print("🗑️  Conversation history cleared")
        elif history_type == "thoughts":
            self.thought_processes.clear()
            print("🗑️  Thought processes cleared")
        elif history_type == "all":
            self.conversation_history.clear()
            self.thought_processes.clear()
            self.ollama.clear_history()
            print("🗑️  All history cleared")
    
    def retry_ai_connection(self):
        """Retry AI connection"""
        print("🔄 Retrying AI connection...")
        self.ollama._initialize()
        return self.ollama.is_available
    
    def switch_ai_model(self, model_name: str):
        """Switch to different AI model"""
        success = self.ollama.switch_model(model_name)
        if success:
            print(f"✅ Switched to model: {model_name}")
        return success
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("\n🛑 Shutting down AI Brain...")
        
        # Save state
        self.save_state()
        
        # Stop event bus worker
        await self.event_bus.stop_priority_worker()
        
        # Update state
        self.state = AIState.SLEEPING
        
        print("✅ AI Brain shutdown complete")


# Export for modular imports
__all__ = ['FullFledgedAIBrain', 'OllamaEnhancedManager', 'AIState', 'ProcessingLayer']

# Example usage
if __name__ == "__main__":
    print("🧠 TESTING FULL-FLEDGED AI BRAIN")
    print("=" * 60)
    
    # Initialize AI Brain
    brain = FullFledgedAIBrain("Prince")
    
    # Get initial status
    print("\n📊 Initial Status:")
    status = brain.get_system_status()
    print(f"• State: {status['system']['state']}")
    print(f"• AI Available: {status['ai_capabilities']['local_ai_available']}")
    print(f"• Model: {status['ai_capabilities']['primary_model']}")
    print(f"• Memory: {status['memory_system']['total_memories']} memories")
    print(f"• Learning: {status['learning_system']['total_patterns']} patterns")
    
    # Test conversations
    test_queries = [
        "Hello Jarvis! How are you today?",
        "Can you explain quantum computing to me?",
        "I'm feeling a bit stressed about my studies",
        "What's the weather like today?",
        "Tell me a story about artificial intelligence",
        "Can you help me create some study flashcards?",
        "What's your opinion on the future of AI?"
    ]
    
    print(f"\n{'='*60}")
    print("🤖 TESTING 5-LAYER INTELLIGENCE")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] User: {query}")
        
        # Process through 5 layers
        analysis = brain.process_input(query)
        
        # Generate response
        response = brain.generate_response(analysis)
        
        print(f"    JARVIS: {response}")
        
        # Show layer activation
        layers = analysis.get("thought_process", {}).get("layers_activated", [])
        print(f"    Layers activated: {len(layers)}")
        
        time.sleep(2)
    
    # Check proactive actions
    print(f"\n{'='*60}")
    print("🔔 CHECKING PROACTIVE ACTIONS")
    print("=" * 60)
    
    context_summary = brain.context.get_context_summary()
    proactive = brain.proactive.check_proactive_events(context_summary)
    
    if proactive:
        for action in proactive[:2]:  # Show first 2
            print(f"• {action.message}")
    else:
        print("No proactive actions at this time")
    
    # Get final status
    print(f"\n{'='*60}")
    print("📊 FINAL SYSTEM STATUS")
    print("=" * 60)
    
    final_status = brain.get_system_status()
    print(f"• Total interactions: {final_status['performance']['total_interactions']}")
    print(f"• AI Response time: {final_status['ai_capabilities']['avg_response_time']}s")
    print(f"• Memory recall rate: {final_status['memory_system']['recall_success_rate']}%")
    print(f"• Learning success rate: {final_status['learning_system']['success_rate']}%")
    
    # Save state
    brain.save_state()
    
    print(f"\n✅ Test complete! AI Brain is operational and learning.")


# Backward compatibility alias for main.py
EnhancedAIBrain = FullFledgedAIBrain