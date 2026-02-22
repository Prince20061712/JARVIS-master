from pipeline import (
    ReactiveLayer, CognitiveLayer, MetacognitiveLayer, 
    ProactiveLayer, CreativeLayer, CognitiveContext,
    ResponseFormat, AcademicStyle
)
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class JarvisFiveLayerEngine:
    """
    Orchestrates the 5 layers of the JARVIS Engineering Academic Copilot.
    1. Reactive: Instant command handling
    2. Cognitive: RAG & Knowledge processing
    3. Metacognitive: Emotional & Self-awareness
    4. Proactive: Learning pattern analysis
    5. Creative: Generation & Formatting
    """
    def __init__(self, config: dict = None, user_id: str = "default_student"):
        self.config = config or {}
        self.user_id = user_id
        
        # Initialize the 5 layers
        self.reactive = ReactiveLayer(self.config.get('reactive'))
        self.cognitive = CognitiveLayer(self.config.get('cognitive'))
        self.metacognitive = MetacognitiveLayer(self.config.get('metacognitive'))
        self.proactive = ProactiveLayer(self.config.get('proactive'))
        self.creative = CreativeLayer(self.config.get('creative'))
        
        logger.info("JarvisFiveLayerEngine initialized with all 5 enhanced layers.")
        
    async def process_student_query_async(self, query: str, subject: str = None, session_id: str = "default_session") -> dict:
        """
        Asynchronously process a student query through the 5-layer pipeline.
        """
        context = {
            "subject": subject,
            "user_id": self.user_id,
            "session_id": session_id,
            "timestamp": asyncio.get_event_loop().time()
        }

        # Layer 1: Reactive (Instant command processing)
        reactive_response = await self.reactive.process(query, context=context, session_id=session_id)
        if reactive_response.executed and reactive_response.command_type != None:
            return {
                "final_response": reactive_response.message,
                "layer": "Reactive",
                "metadata": reactive_response.metadata
            }

        # Layer 3: Metacognitive (Emotional State & Persona Adaptation)
        metacognitive_insight = await self.metacognitive.process(query, session_id=session_id, context=context)
        detected_emotion = metacognitive_insight.detected_state
        persona_adjustments = metacognitive_insight.suggested_persona_adjustments

        # Layer 4: Proactive (Pattern Detection & Suggestions)
        # We pass recent interactions (simplified here as just the current one for now)
        proactive_suggestions = await self.proactive.process(
            user_id=self.user_id,
            recent_interactions=[{"input": query, "emotion": detected_emotion.value}],
            context=context
        )

        # Layer 2: Cognitive (Knowledge Retrieval / RAG)
        cognitive_context = CognitiveContext(
            query=query,
            domain=subject,
            user_id=self.user_id,
            session_id=session_id
        )
        rag_result = await self.cognitive.process(cognitive_context)
        
        # Layer 5: Creative (Response Generation & Academic Styling)
        # We use the RAG context window as the base content for the creative layer
        creative_context = {
            **context,
            "emotion": detected_emotion.value,
            "persona_adjustments": {k.value: v for k, v in persona_adjustments.items()},
            "suggestions": [s.message for s in proactive_suggestions]
        }
        
        # Determine recommended style and format
        target_style = self.creative.get_style_recommendation(
            user_level="intermediate", 
            purpose="learning", 
            emotional_state=detected_emotion.value
        )
        
        creative_output = await self.creative.process(
            content=rag_result.context_window,
            context=creative_context,
            target_format=ResponseFormat.MARKDOWN,
            target_style=target_style
        )

        return {
            "final_response": creative_output.content,
            "detected_emotion": detected_emotion.value,
            "confidence": metacognitive_insight.confidence,
            "proactive_suggestions": [s.message for s in proactive_suggestions],
            "academic_metrics": {
                "word_count": creative_output.word_count,
                "reading_time": creative_output.reading_time_minutes,
                "has_math": creative_output.has_math,
                "has_code": creative_output.has_code
            },
            "layer_metadata": {
                "reactive": reactive_response.metadata,
                "cognitive": rag_result.metadata,
                "metacognitive": {
                    "reasoning": metacognitive_insight.reasoning,
                    "persona_adjustments": {k.value: v for k, v in persona_adjustments.items()}
                }
            }
        }

    def process_student_query(self, query: str, subject: str = None) -> dict:
        """Synchronous wrapper for processing student queries."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.process_student_query_async(query, subject))

if __name__ == "__main__":
    # Test the pipeline
    engine = JarvisFiveLayerEngine()
    print(json.dumps(engine.process_student_query("I don't understand how to derive the Maxwell equations, I'm stuck!", "Electromagnetics"), indent=2))
