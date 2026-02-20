from typing import Dict, Any, List, Optional
import copy
from utils.logger import logger

class WorkingMemory:
    """
    Scratchpad for temporary problem-solving states and derivations.
    Supports state transitions, rollbacks, and partial solutions.
    """
    def __init__(self):
        self.state_stack: List[Dict[str, Any]] = []
        self.current_state: Dict[str, Any] = {
            "current_problem": None,
            "steps_taken": [],
            "partial_solutions": {},
            "workspace_vars": {}
        }

    def push_state(self):
        """Saves the current state to the stack (checkpoint)."""
        self.state_stack.append(copy.deepcopy(self.current_state))
        logger.debug(f"State pushed. Stack size: {len(self.state_stack)}")

    def pop_state(self) -> bool:
        """Rolls back to the previous state."""
        if not self.state_stack:
            logger.warning("Attempted to pop from empty working memory stack.")
            return False
        self.current_state = self.state_stack.pop()
        logger.debug("Rolled back to previous state.")
        return True

    def peek_state(self) -> Optional[Dict[str, Any]]:
        """Views the last pushed state without removing it."""
        if not self.state_stack:
            return None
        return copy.deepcopy(self.state_stack[-1])

    def set_problem(self, problem: str):
        """Sets the current problem being solved."""
        self.current_state["current_problem"] = problem
        self.current_state["steps_taken"].clear()
        self.current_state["partial_solutions"].clear()
        
    def add_step(self, step_description: str, intermediate_result: Any = None):
        """Records a step taken towards solving the problem."""
        self.current_state["steps_taken"].append({
            "step": step_description,
            "result": intermediate_result
        })

    def workspace_set(self, key: str, value: Any):
        """Stores temporary calculations or variables."""
        self.current_state["workspace_vars"][key] = value

    def workspace_get(self, key: str, default: Any = None) -> Any:
        return self.current_state["workspace_vars"].get(key, default)

    def clear(self):
        """Clears the working memory entirely."""
        self.state_stack.clear()
        self.current_state = {
            "current_problem": None,
            "steps_taken": [],
            "partial_solutions": {},
            "workspace_vars": {}
        }
