#!/usr/bin/env python3
"""
Decision Engine Module
Analyzes urgency and importance of requests
"""

import datetime
from enum import Enum

class PriorityLevel(Enum):
    CRITICAL = 5
    URGENT = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

class DecisionEngine:
    def __init__(self):
        self.priority_keywords = {
            PriorityLevel.CRITICAL: ["emergency", "urgent", "immediately", "now", 
                                    "critical", "asap", "right away", "stat"],
            PriorityLevel.URGENT: ["important", "need", "must", "essential", 
                                  "vital", "crucial", "priority"],
            PriorityLevel.HIGH: ["should", "better", "soon", "quick", "fast"],
            PriorityLevel.MEDIUM: ["can", "could", "when you can", "later"],
            PriorityLevel.LOW: ["sometime", "whenever", "no rush", "leisure", 
                              "casual", "when free"]
        }
        
        self.impact_assessment = {
            "system": 3,       # System operations
            "security": 4,     # Security-related
            "communication": 2, # Communication
            "entertainment": 1, # Entertainment
            "information": 2,   # Information retrieval
            "productivity": 3   # Productivity
        }
    
    def analyze_priority(self, user_input, context=None):
        """Analyze priority level of request"""
        input_lower = user_input.lower()
        
        # Check for priority keywords
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return priority
        
        # Default to medium priority
        return PriorityLevel.MEDIUM
    
    def assess_impact(self, user_input):
        """Assess potential impact of the request"""
        input_lower = user_input.lower()
        
        impact_score = 1  # Default
        
        # Check for impact areas
        if any(word in input_lower for word in ["shutdown", "restart", "format", "delete"]):
            return self.impact_assessment.get("system", 3)
        elif any(word in input_lower for word in ["password", "security", "lock", "encrypt"]):
            return self.impact_assessment.get("security", 4)
        elif any(word in input_lower for word in ["email", "message", "call", "send"]):
            return self.impact_assessment.get("communication", 2)
        elif any(word in input_lower for word in ["play", "music", "video", "game"]):
            return self.impact_assessment.get("entertainment", 1)
        elif any(word in input_lower for word in ["search", "find", "information", "data"]):
            return self.impact_assessment.get("information", 2)
        elif any(word in input_lower for word in ["work", "task", "project", "schedule"]):
            return self.impact_assessment.get("productivity", 3)
        
        return impact_score
    
    def make_decision(self, user_input, context=None):
        """Make decision about how to handle request"""
        priority = self.analyze_priority(user_input, context)
        impact = self.assess_impact(user_input)
        
        # Calculate decision score
        decision_score = priority.value * impact
        
        decisions = {
            "priority_level": priority.value,
            "priority_name": priority.name,
            "impact_score": impact,
            "decision_score": decision_score,
            "requires_confirmation": decision_score >= 12,  # Critical+High impact
            "should_queue": priority.value <= 2,  # Low/Medium priority
            "immediate_execution": priority.value >= 4,  # Urgent/Critical
            "suggested_action_time": self._suggest_action_time(priority),
            "risk_level": self._calculate_risk(priority, impact)
        }
        
        return decisions
    
    def _suggest_action_time(self, priority):
        """Suggest when to take action"""
        time_suggestions = {
            PriorityLevel.CRITICAL: "Immediately",
            PriorityLevel.URGENT: "Within 5 minutes",
            PriorityLevel.HIGH: "Within 30 minutes",
            PriorityLevel.MEDIUM: "Within 2 hours",
            PriorityLevel.LOW: "When convenient"
        }
        return time_suggestions.get(priority, "When convenient")
    
    def _calculate_risk(self, priority, impact):
        """Calculate risk level"""
        risk_score = priority.value * impact
        
        if risk_score >= 15:
            return "High Risk"
        elif risk_score >= 10:
            return "Medium Risk"
        elif risk_score >= 5:
            return "Low Risk"
        else:
            return "Minimal Risk"
    
    def get_decision_summary(self, user_input):
        """Get human-readable decision summary"""
        decision = self.make_decision(user_input)
        
        summary = f"""
        Decision Analysis:
        • Priority: {decision['priority_name']} (Level {decision['priority_level']})
        • Impact Score: {decision['impact_score']}/5
        • Risk Level: {decision['risk_level']}
        • Action Timeline: {decision['suggested_action_time']}
        {'⚠️  Requires confirmation' if decision['requires_confirmation'] else '✓  Can proceed'}
        """
        
        return summary.strip()