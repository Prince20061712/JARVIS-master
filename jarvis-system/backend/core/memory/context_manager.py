from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory
import threading

class ContextManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ContextManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        # Initialize Memory Backends
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        
        self.mode: str = "friend" 
        self.user_preferences: Dict[str, Any] = {}
        self.active_app: str = None
        self._initialized = True
        self.state_lock = threading.Lock()

    def add_turn(self, user_input: str, system_response: str, intent: str):
        """
        Thread-safe addition to interaction history using DB.
        """
        with self.state_lock:
            # Store User Input
            self.ltm.store_conversation(
                role="user", 
                content=user_input, 
                metadata={"intent": intent, "mode": self.mode}
            )
            # Store System Response
            self.ltm.store_conversation(
                role="system", 
                content=system_response,
                metadata={"intent": intent, "mode": self.mode}
            )

    def get_recent_history(self, limit: int = 5) -> List[Dict]:
        """
        Retrieve recent context from DB.
        """
        with self.state_lock:
            return self.stm.get_recent_messages(limit)

    def set_mode(self, mode: str):
        with self.state_lock:
            if mode in ["executor", "teacher", "friend"]:
                self.mode = mode
            else:
                raise ValueError(f"Invalid mode: {mode}")

    def get_mode(self) -> str:
        with self.state_lock:
            return self.mode
