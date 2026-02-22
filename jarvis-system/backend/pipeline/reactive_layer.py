"""
Reactive Layer - Handles immediate, reflex-like commands and system operations
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of reactive commands supported by the system"""
    SYSTEM = "system"
    NAVIGATION = "navigation"
    CLEAR = "clear"
    HELP = "help"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    REPEAT = "repeat"
    VOLUME = "volume"
    SCREEN = "screen"
    EMERGENCY = "emergency"


@dataclass
class ReactiveResponse:
    """Structured response from reactive layer"""
    command_type: CommandType
    executed: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    requires_confirmation: bool = False
    suggestions: List[str] = field(default_factory=list)


class ReactiveLayer:
    """
    Handles instant, reflex-like commands without complex reasoning.
    Implements command patterns, keyboard shortcuts, and emergency protocols.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.command_handlers: Dict[CommandType, List[Callable]] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.emergency_protocols = self._init_emergency_protocols()
        self.command_patterns = self._init_command_patterns()
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("Reactive Layer initialized with %d command types", len(CommandType))
    
    def _init_emergency_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emergency response protocols"""
        return {
            'distress': {
                'keywords': ['help', 'emergency', 'urgent', 'danger'],
                'priority': 1,
                'actions': ['pause_all', 'notify_admin', 'log_incident'],
                'response_template': "Emergency protocol activated. How can I assist you immediately?"
            },
            'frustration': {
                'keywords': ['too hard', 'confusing', 'don\'t understand', 'frustrated'],
                'priority': 2,
                'actions': ['simplify', 'offer_help', 'suggest_break'],
                'response_template': "I notice you might be struggling. Would you like me to explain differently?"
            },
            'technical': {
                'keywords': ['broken', 'not working', 'error', 'bug'],
                'priority': 3,
                'actions': ['diagnose', 'offer_alternatives', 'log_technical'],
                'response_template': "Let me help resolve this technical issue."
            }
        }
    
    def _init_command_patterns(self) -> Dict[str, CommandType]:
        """Initialize regex patterns for command detection"""
        return {
            r'^(stop|exit|quit|end)\s*$': CommandType.STOP,
            r'^(clear|clean|erase)\s*$': CommandType.CLEAR,
            r'^(help|what can you do|commands?)\s*$': CommandType.HELP,
            r'^(pause|wait|hold on)\s*$': CommandType.PAUSE,
            r'^(resume|continue|go on)\s*$': CommandType.RESUME,
            r'^(repeat|say that again|what did you say)\s*$': CommandType.REPEAT,
            r'^(volume|turn (up|down) volume)\s+(up|down|\d+)\s*$': CommandType.VOLUME,
            r'^(go to|navigate|open|show)\s+(\w+)\s*$': CommandType.NAVIGATION,
        }
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        self.register_handler(CommandType.STOP, self._handle_stop)
        self.register_handler(CommandType.CLEAR, self._handle_clear)
        self.register_handler(CommandType.HELP, self._handle_help)
        self.register_handler(CommandType.PAUSE, self._handle_pause)
        self.register_handler(CommandType.RESUME, self._handle_resume)
        self.register_handler(CommandType.REPEAT, self._handle_repeat)
        self.register_handler(CommandType.NAVIGATION, self._handle_navigation)
        self.register_handler(CommandType.EMERGENCY, self._handle_emergency)
    
    async def process(self, 
                     user_input: str, 
                     context: Optional[Dict[str, Any]] = None,
                     session_id: Optional[str] = None) -> ReactiveResponse:
        """
        Process user input for reactive commands
        
        Args:
            user_input: Raw user input string
            context: Additional context information
            session_id: Current session identifier
            
        Returns:
            ReactiveResponse with command execution result
        """
        start_time = datetime.now()
        context = context or {}
        
        try:
            # Normalize input
            normalized_input = self._normalize_input(user_input)
            
            # Check for emergency commands first (highest priority)
            emergency_response = await self._check_emergency(normalized_input, session_id)
            if emergency_response:
                return emergency_response
            
            # Detect command type
            command_type = self._detect_command_type(normalized_input)
            
            if not command_type:
                # Not a reactive command, pass through
                return ReactiveResponse(
                    command_type=CommandType.SYSTEM,
                    executed=False,
                    message="No reactive command detected",
                    metadata={"input": user_input, "passed_through": True},
                    execution_time_ms=self._calculate_elapsed_ms(start_time)
                )
            
            # Execute command handlers
            result = await self._execute_command(command_type, normalized_input, context, session_id)
            
            # Log to history
            self._log_command(command_type, user_input, result, session_id)
            
            # Calculate execution time
            execution_time = self._calculate_elapsed_ms(start_time)
            result.execution_time_ms = execution_time
            
            logger.info(f"Reactive command '{command_type.value}' executed in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error processing reactive command: {str(e)}", exc_info=True)
            return ReactiveResponse(
                command_type=CommandType.SYSTEM,
                executed=False,
                message=f"Error processing command: {str(e)}",
                metadata={"error": str(e), "input": user_input},
                execution_time_ms=self._calculate_elapsed_ms(start_time)
            )
    
    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for consistent processing"""
        # Convert to lowercase
        normalized = user_input.lower().strip()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove punctuation for matching
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    def _detect_command_type(self, normalized_input: str) -> Optional[CommandType]:
        """Detect command type from normalized input"""
        for pattern, command_type in self.command_patterns.items():
            if re.match(pattern, normalized_input, re.IGNORECASE):
                return command_type
        return None
    
    async def _check_emergency(self, 
                              normalized_input: str, 
                              session_id: Optional[str]) -> Optional[ReactiveResponse]:
        """Check for emergency situations"""
        for protocol_name, protocol in self.emergency_protocols.items():
            if any(keyword in normalized_input for keyword in protocol['keywords']):
                return await self._handle_emergency(
                    protocol_name, 
                    protocol, 
                    normalized_input, 
                    session_id
                )
        return None
    
    async def _execute_command(self,
                              command_type: CommandType,
                              normalized_input: str,
                              context: Dict[str, Any],
                              session_id: Optional[str]) -> ReactiveResponse:
        """Execute registered handlers for a command type"""
        handlers = self.command_handlers.get(command_type, [])
        
        if not handlers:
            return ReactiveResponse(
                command_type=command_type,
                executed=False,
                message=f"No handler registered for command: {command_type.value}",
                metadata={"available_handlers": list(self.command_handlers.keys())}
            )
        
        # Execute first handler (can be extended for multiple handlers)
        handler = handlers[0]
        return await handler(normalized_input, context, session_id)
    
    def register_handler(self, command_type: CommandType, handler: Callable):
        """Register a handler for a command type"""
        if command_type not in self.command_handlers:
            self.command_handlers[command_type] = []
        self.command_handlers[command_type].append(handler)
        logger.debug(f"Registered handler for {command_type.value}")
    
    # Default Handlers
    async def _handle_stop(self, 
                          normalized_input: str, 
                          context: Dict[str, Any],
                          session_id: Optional[str]) -> ReactiveResponse:
        """Handle stop/exit commands"""
        # Clean up session if exists
        if session_id and session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return ReactiveResponse(
            command_type=CommandType.STOP,
            executed=True,
            message="Stopping current operation. Goodbye!",
            metadata={"cleaned_up": bool(session_id)},
            requires_confirmation=False,
            suggestions=["Would you like to start a new session?", "View your learning progress?"]
        )
    
    async def _handle_clear(self,
                           normalized_input: str,
                           context: Dict[str, Any],
                           session_id: Optional[str]) -> ReactiveResponse:
        """Handle clear commands"""
        return ReactiveResponse(
            command_type=CommandType.CLEAR,
            executed=True,
            message="Clearing screen and resetting view...",
            metadata={"clear_type": "full" if "all" in normalized_input else "screen"},
            suggestions=["Type 'help' for available commands"]
        )
    
    async def _handle_help(self,
                          normalized_input: str,
                          context: Dict[str, Any],
                          session_id: Optional[str]) -> ReactiveResponse:
        """Handle help commands"""
        help_text = self._generate_help_text(normalized_input)
        
        return ReactiveResponse(
            command_type=CommandType.HELP,
            executed=True,
            message=help_text,
            metadata={
                "available_commands": [cmd.value for cmd in CommandType],
                "help_topic": context.get('topic', 'general')
            },
            suggestions=["Try 'help commands' for list", "Ask about a specific feature"]
        )
    
    async def _handle_pause(self,
                           normalized_input: str,
                           context: Dict[str, Any],
                           session_id: Optional[str]) -> ReactiveResponse:
        """Handle pause commands"""
        if session_id:
            self.active_sessions[session_id] = {'status': 'paused', 'paused_at': datetime.now()}
        
        return ReactiveResponse(
            command_type=CommandType.PAUSE,
            executed=True,
            message="Session paused. Say 'resume' to continue.",
            metadata={"session_id": session_id, "paused": True}
        )
    
    async def _handle_resume(self,
                            normalized_input: str,
                            context: Dict[str, Any],
                            session_id: Optional[str]) -> ReactiveResponse:
        """Handle resume commands"""
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id]['status'] = 'active'
        
        return ReactiveResponse(
            command_type=CommandType.RESUME,
            executed=True,
            message="Resuming session...",
            metadata={"session_id": session_id, "resumed": True}
        )
    
    async def _handle_repeat(self,
                            normalized_input: str,
                            context: Dict[str, Any],
                            session_id: Optional[str]) -> ReactiveResponse:
        """Handle repeat commands"""
        last_command = self.command_history[-1] if self.command_history else None
        
        if last_command:
            return ReactiveResponse(
                command_type=CommandType.REPEAT,
                executed=True,
                message=f"Repeating last command: {last_command['input']}",
                metadata={"last_command": last_command}
            )
        else:
            return ReactiveResponse(
                command_type=CommandType.REPEAT,
                executed=False,
                message="No previous command to repeat",
                metadata={"history_empty": True}
            )
    
    async def _handle_navigation(self,
                                normalized_input: str,
                                context: Dict[str, Any],
                                session_id: Optional[str]) -> ReactiveResponse:
        """Handle navigation commands"""
        # Extract destination
        match = re.search(r'(?:go to|navigate|open|show)\s+(\w+)', normalized_input)
        destination = match.group(1) if match else "unknown"
        
        return ReactiveResponse(
            command_type=CommandType.NAVIGATION,
            executed=True,
            message=f"Navigating to {destination}...",
            metadata={"destination": destination, "valid": destination != "unknown"},
            suggestions=["Try 'help navigation' for available destinations"]
        )
    
    async def _handle_emergency(self,
                               protocol_name: str,
                               protocol: Dict[str, Any],
                               normalized_input: str,
                               session_id: Optional[str]) -> ReactiveResponse:
        """Handle emergency protocols"""
        logger.warning(f"Emergency protocol triggered: {protocol_name}")
        
        return ReactiveResponse(
            command_type=CommandType.EMERGENCY,
            executed=True,
            message=protocol['response_template'],
            metadata={
                "protocol": protocol_name,
                "priority": protocol['priority'],
                "actions_taken": protocol['actions']
            },
            requires_confirmation=True,
            suggestions=["Would you like to speak with a human?", "Take a break?"]
        )
    
    def _generate_help_text(self, query: str) -> str:
        """Generate contextual help text"""
        if "command" in query:
            return "Available commands: stop, clear, help, pause, resume, repeat, volume, navigate"
        elif "feature" in query:
            return "Features: AI tutoring, concept explanations, practice problems, progress tracking"
        else:
            return "I'm JARVIS, your AI learning assistant. How can I help you today?"
    
    def _log_command(self, 
                     command_type: CommandType, 
                     user_input: str, 
                     response: ReactiveResponse,
                     session_id: Optional[str]):
        """Log command to history"""
        self.command_history.append({
            'timestamp': datetime.now(),
            'command_type': command_type.value,
            'input': user_input,
            'response': response.message,
            'executed': response.executed,
            'session_id': session_id
        })
        
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
    
    def _calculate_elapsed_ms(self, start_time: datetime) -> float:
        """Calculate elapsed time in milliseconds"""
        elapsed = datetime.now() - start_time
        return elapsed.total_seconds() * 1000
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific session"""
        return self.active_sessions.get(session_id)
    
    def get_command_statistics(self) -> Dict[str, Any]:
        """Get statistics about command usage"""
        if not self.command_history:
            return {"total_commands": 0}
        
        command_counts = {}
        for entry in self.command_history:
            cmd_type = entry['command_type']
            command_counts[cmd_type] = command_counts.get(cmd_type, 0) + 1
        
        return {
            "total_commands": len(self.command_history),
            "command_breakdown": command_counts,
            "success_rate": sum(1 for e in self.command_history if e['executed']) / len(self.command_history),
            "last_command": self.command_history[-1] if self.command_history else None
        }