import numpy as np
from typing import List, Dict, Any
from utils.logger import logger

class PerformancePredictor:
    """
    Predicts exam scores and performance trends based on preparation data.
    Uses basic linear regression or weighted averages if ML libraries aren't ready.
    """
    def __init__(self):
        # preparation_score vs exam_score samples for training
        self.history_X = [] 
        self.history_y = []

    def predict_performance(self, prep_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Input: {'mastery': 0.8, 'consistency': 0.9, 'hours_spent': 50}
        Output: Predicted score and risk factors.
        """
        # Linear weighted model: (Mastery * 0.6) + (Consistency * 0.2) + (Hours * 0.2)
        score_base = (prep_metrics.get('mastery', 0.5) * 60) + \
                     (prep_metrics.get('consistency', 0.5) * 20) + \
                     (min(prep_metrics.get('hours_spent', 0), 100) / 100 * 20)
        
        prediction = round(score_base, 2)
        risk_factors = []
        if prep_metrics.get('consistency', 0) < 0.4:
            risk_factors.append("Low consistency may lead to knowledge loss.")
        if prep_metrics.get('mastery', 0) < 0.3:
            risk_factors.append("Insufficient topic mastery.")

        return {
            "predicted_score": prediction,
            "confidence_interval": [prediction - 5, prediction + 5],
            "risk_factors": risk_factors
        }

    def identify_risk_factors(self, student_state: Dict) -> List[str]:
        """Analyzes broad state for immediate intervention triggers."""
        risks = []
        if student_state.get('stress_level', 0) > 0.8:
            risks.append("High burnout risk detected.")
        if student_state.get('uncovered_topics', 0) > 10:
            risks.append("Critical syllabus coverage gap.")
        return risks

    def generate_forecast(self, mastery_trend: List[float]) -> Dict[str, Any]:
        """Predicts future mastery based on recent trend."""
        if len(mastery_trend) < 3:
            return {"forecast": "stable", "projected_mastery": mastery_trend[-1]}
            
        diffs = np.diff(mastery_trend)
        avg_diff = np.mean(diffs)
        
        forecast = "improving" if avg_diff > 0 else "declining"
        projected = min(1.0, mastery_trend[-1] + avg_diff * 5) # Forecast 5 sessions ahead
        
        return {
            "trend": forecast,
            "projected_mastery": round(float(projected), 2)
        }
