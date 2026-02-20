from emotional_intelligence import EmotionalIntelligence
import json
import asyncio

class MockLearningPatternTracker:
    def log_interaction(self, subject, is_frustrated):
        pass
    def analyze_patterns(self):
        return {"recommendations": ["Review basic concepts."]}

class MockAcademicResponseFormatter:
    def format_for_marks(self, raw_response, estimated_marks):
        return raw_response

class MockSyllabusAwareRAG:
    def __init__(self, base_rag_engine=None, semester=1, branch="CS"):
        pass
    def get_context_with_syllabus(self, query, subject):
        return {
            "raw_context": "Maxwell's equations are a set of coupled partial differential equations...",
            "estimated_marks": 10,
            "question_type": "Derivation"
        }

class JarvisFiveLayerEngine:
    """
    Orchestrates the 5 layers of the JARVIS Engineering Academic Copilot.
    1. Reactive: Instant command handling
    2. Cognitive: RAG & Knowledge processing
    3. Metacognitive: Emotional & Self-awareness
    4. Proactive: Learning pattern analysis
    5. Creative: Generation & Formatting
    """
    def __init__(self, base_rag_engine=None, user_id="default_student"):
        self.rag = MockSyllabusAwareRAG(base_rag_engine, semester=1, branch="CS")
        self.emotional_intelligence = EmotionalIntelligence(user_id)
        self.learning_tracker = MockLearningPatternTracker()
        self.formatter = MockAcademicResponseFormatter()
        
    def process_student_query(self, query: str, subject: str = None) -> dict:
        # Layer 1: Reactive (Is this a basic system command?)
        if query.lower() in ["help", "stop", "clear"]:
            return {"final_response": "Reactive command executed.", "layer": "Reactive"}

        # Layer 3: Metacognitive (Emotional State Detection)
        # We use asyncio.run because process_interaction is async, while process_student_query is sync
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        ei_result = loop.run_until_complete(
            self.emotional_intelligence.process_interaction(text=query, context={"subject": subject})
        )
        detected_emotion = ei_result["state"]["current"]["primary_emotion"]
        is_frustrated = detected_emotion in ["frustration", "anxiety", "overwhelmed", "burnout"]

        # Layer 4 (Pre-process): Proactive (Log Interaction & Get Recommendations)
        self.learning_tracker.log_interaction(subject or "General Engineering", is_frustrated)
        proactive_insights = self.learning_tracker.analyze_patterns()

        # Layer 2: Cognitive (Syllabus-Aware Knowledge Retrieval)
        rag_payload = self.rag.get_context_with_syllabus(query, subject)
        
        # Layer 5: Creative (Generate raw LLM Response using RAG Context and format it)
        raw_llm_response = f"Based on the context:\n{rag_payload['raw_context'][:100]}...\nThis answers the {rag_payload['question_type']} requirement."
        
        # Apply strict Academic Formatting (Marks allocator)
        formatted_response = self.formatter.format_for_marks(raw_llm_response, rag_payload["estimated_marks"])
        
        # Apply Mentorship/Emotional Wrap if needed
        # We adapt response based on the detected emotional state
        formatted_response = self.emotional_intelligence.adapt_response(
            formatted_response, context={"subject": subject}
        )
            
        # Append Proactive Interventions (if any)
        if proactive_insights["recommendations"]:
            formatted_response += "\n\n🔔 **Proactive Suggestion:**\n" + proactive_insights["recommendations"][-1]
            
        # Append Proactive Emotional Message (if any)
        if ei_result.get("proactive_message"):
            formatted_response += "\n\n💙 **JARVIS:**\n" + ei_result["proactive_message"]

        return {
            "final_response": formatted_response,
            "detected_emotion": detected_emotion,
            "wellbeing_score": ei_result["wellbeing_score"],
            "estimated_marks": rag_payload["estimated_marks"],
            "question_type": rag_payload["question_type"],
            "proactive_interventions": proactive_insights["recommendations"]
        }

if __name__ == "__main__":
    # Test the pipeline
    engine = JarvisFiveLayerEngine()
    print(json.dumps(engine.process_student_query("I don't understand how to derive the Maxwell equations, I'm stuck!", "Electromagnetics"), indent=2))
