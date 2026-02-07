import logging
import os
from ai.llm_client import LLMClient
from ai.emotion_detector import EmotionDetector
from core.memory.context_manager import ContextManager

logger = logging.getLogger("ConversationHandler")

class ConversationHandler:
    def __init__(self):
        self.llm = LLMClient()
        self.context_manager = ContextManager()
        self.emotion_detector = EmotionDetector()
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")

    async def generate_response(self, text: str, user_name: str = "User") -> str:
        """
        Generates a persona-aware response using LLM.
        """
        # 1. Detect User Emotion (for context)
        emotion_data = self.emotion_detector.detect(text)
        logger.info(f"User emotion: {emotion_data.primary_emotion} ({emotion_data.sentiment_score})")

        # 2. Get Current Persona/Mode
        mode = self.context_manager.get_mode()
        
        # 3. Load System Prompt
        prompt_file = os.path.join(self.prompts_dir, "system_default.txt")
        # You could have mode-specific files like system_teacher.txt
        if os.path.exists(os.path.join(self.prompts_dir, f"system_{mode.lower()}.txt")):
             prompt_file = os.path.join(self.prompts_dir, f"system_{mode.lower()}.txt")
        
        try:
            with open(prompt_file, "r") as f:
                system_prompt_template = f.read()
        except FileNotFoundError:
             system_prompt_template = "You are a helpful assistant."

        # 4. Fill Template
        # Recent conversation history is managed by context_manager, 
        # but for LLM we need to construct the message list.
        # Here we get a short history summary or last few turns.
        history_summary = "No previous context." # Placeholder for RAG summary
        
        system_prompt = system_prompt_template.format(
            mode=mode,
            context=history_summary
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        # 5. Call LLM
        response = await self.llm.chat(messages)
        return response
