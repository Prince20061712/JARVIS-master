from intents.detector import IntentDetector, Intent
from intents.system_commands import SystemCommandExecutor
from intents.knowledge_qa import KnowledgeQA
from intents.conversation import ConversationHandler

from ai.emotion_detector import EmotionDetector
from core.memory.context_manager import ContextManager
from core.event_bus import event_bus
import logging
from emotions.engine import EmotionEngine

logger = logging.getLogger("AssistantRobot")

class CommandRouter:
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.emotion_detector = EmotionDetector()
        self.emotion_engine = EmotionEngine()
        self.context = ContextManager()
        
        self.system_executor = SystemCommandExecutor()
        self.qa_system = KnowledgeQA()
        self.conversation_handler = ConversationHandler()

    async def process(self, text: str) -> dict:
        """
        Main entry point. Returns Dict with 'text', 'ui', 'robot_emotion'.
        """
        logger.info(f"Processing input: {text}")
        
        # 1. Analysis: Intent & Emotion
        intent = self.intent_detector.detect(text)
        user_emotion = self.emotion_detector.detect(text)
        
        logger.info(f"Detected intent: {intent.type} ({intent.name})")
        logger.info(f"Detected emotion: {user_emotion.primary_emotion}")

        # Publish events
        await event_bus.publish("intent.classified", intent)
        await event_bus.publish("emotion.detected", user_emotion)

        # 2. Routing / Execution
        raw_response = ""
        try:
            handler_type = intent.suggested_handler
            
            if handler_type == "system":
                raw_response = await self.system_executor.execute(intent)
                await event_bus.publish("command.executed", {"command": intent.name, "response": raw_response})
                
            elif handler_type == "knowledge":
                raw_response = await self.qa_system.answer(intent)
                
            else: # Chat
                # ConversationHandler can use the emotion data too if passed, but for now we rely on its internal or just text
                raw_response = await self.conversation_handler.generate_response(text)
                
        except Exception as e:
            logger.error(f"Error handling intent: {e}")
            raw_response = "I encountered an error."
            await event_bus.publish("error.occurred", {"error": str(e), "context": "router"})

        # 3. Post-Processing (Emotion Engine)
        # This adds UI parameters and modifies text based on empathy
        processed_response = self.emotion_engine.process_response(raw_response, user_emotion)
        
        # 4. Context Update
        self.context.add_turn(text, processed_response["text"], intent.name)
        
        return processed_response





    def set_mode(self, mode: str):
        self.context.set_mode(mode)
        return f"Switched to {mode} mode."
