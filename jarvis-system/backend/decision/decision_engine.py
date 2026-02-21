#!/usr/bin/env python3
"""
Enhanced Human-Centric Decision Engine
Analyzes urgency, importance, and human context with emotional intelligence
"""

import datetime
import re
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import json

class PriorityLevel(Enum):
    CRITICAL = 5    # Life/safety, immediate threats
    URGENT = 4      # Time-sensitive critical matters
    HIGH = 3        # Important with deadlines
    MEDIUM = 2      # Normal priority
    LOW = 1         # Can be deferred
    PASSIVE = 0     # No action needed, just information

class EmotionalContext(Enum):
    STRESSED = "stressed"
    ANXIOUS = "anxious" 
    CALM = "calm"
    HURRIED = "hurried"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    EXCITED = "excited"

class DecisionEngine:
    def __init__(self):
        # Enhanced priority detection with context awareness
        self.priority_patterns = {
            PriorityLevel.CRITICAL: {
                'patterns': [
                    r'emergency|urgent.*now|immediate.*danger|911',
                    r'stop.*now|cease.*immediate|shut.*down.*now',
                    r'safety.*issue|security.*breach|intruder',
                    r'heart.*attack|stroke|bleeding.*badly|can.*t.*breathe',
                    r'fire|flood|earthquake|tornado.*warning'
                ],
                'context_cues': ['voice_raised', 'repetition', 'panicked_tone'],
                'time_window': '0-2 minutes'
            },
            PriorityLevel.URGENT: {
                'patterns': [
                    r'need.*now|must.*today|deadline.*today',
                    r'important.*meeting|appointment.*miss',
                    r'lost.*keys|locked.*out|car.*broken',
                    r'child.*sick|pet.*emergency|family.*crisis'
                ],
                'context_cues': ['time_mention', 'consequences_mentioned'],
                'time_window': '2-30 minutes'
            },
            PriorityLevel.HIGH: {
                'patterns': [
                    r'should.*today|better.*soon|priority.*task',
                    r'work.*deadline|project.*due|assignment.*submit',
                    r'doctor.*appointment|interview.*tomorrow',
                    r'bill.*due|payment.*overdue'
                ],
                'time_window': '30 minutes - 2 hours'
            },
            PriorityLevel.MEDIUM: {
                'patterns': [
                    r'can.*you|when.*you.*have.*time',
                    r'not.*urgent|no.*rush|sometime.*today',
                    r'planning.*for|thinking.*about|considering'
                ],
                'time_window': '2-24 hours'
            },
            PriorityLevel.LOW: {
                'patterns': [
                    r'whenever.*free|someday|no.*hurry',
                    r'just.*curious|wondering.*about',
                    r'if.*possible|if.*not.*too.*much.*trouble'
                ],
                'time_window': '1-7 days'
            },
            PriorityLevel.PASSIVE: {
                'patterns': [
                    r'just.*saying|sharing|thinking.*aloud',
                    r'info.*only|for.*your.*information',
                    r'not.*asking.*for.*anything|no.*action.*needed'
                ],
                'time_window': 'No timeline'
            }
        }
        
        # Human context patterns
        self.emotional_cues = {
            EmotionalContext.STRESSED: [
                'overwhelmed', 'too much', 'can\'t handle', 'stressed out',
                'pressure', 'deadline closing', 'multiple deadlines'
            ],
            EmotionalContext.ANXIOUS: [
                'worried', 'concerned', 'nervous', 'anxious',
                'what if', 'afraid that', 'scared about'
            ],
            EmotionalContext.HURRIED: [
                'quick', 'fast', 'hurry', 'rush',
                'no time', 'running late', 'behind schedule'
            ],
            EmotionalContext.FRUSTRATED: [
                'frustrated', 'annoyed', 'angry', 'fed up',
                'not working', 'broken', 'failed', 'error'
            ],
            EmotionalContext.CONFUSED: [
                'confused', 'don\'t understand', 'not sure',
                'how does', 'what is', 'can you explain'
            ],
            EmotionalContext.EXCITED: [
                'excited', 'happy about', 'looking forward',
                'great news', 'wonderful', 'awesome'
            ]
        }
        
        # Human values and relationship context
        self.value_weighting = {
            'health_safety': 10,
            'family_relationships': 9,
            'work_responsibility': 8,
            'financial': 7,
            'education': 6,
            'social': 5,
            'personal_growth': 4,
            'entertainment': 3,
            'curiosity': 2,
            'trivial': 1
        }
        
        # Decision maturity levels
        self.decision_maturity = {
            'automatic': {
                'description': 'Routine, low-risk decisions',
                'characteristics': ['repetitive', 'low_impact', 'predefined_rules']
            },
            'informed': {
                'description': 'Decisions requiring basic information',
                'characteristics': ['moderate_impact', 'clear_options', 'data_needed']
            },
            'deliberative': {
                'description': 'Decisions requiring careful thought',
                'characteristics': ['high_impact', 'multiple_factors', 'human_values']
            },
            'collaborative': {
                'description': 'Decisions requiring human input',
                'characteristics': ['relationship_impact', 'emotional_weight', 'shared_responsibility']
            },
            'ethical': {
                'description': 'Decisions with moral implications',
                'characteristics': ['moral_dilemma', 'value_conflict', 'long_term_consequences']
            }
        }
    
    def detect_emotional_context(self, user_input: str, metadata: Dict = None) -> Dict:
        """
        Detect emotional state and human context
        """
        input_lower = user_input.lower()
        
        emotional_state = EmotionalContext.NEUTRAL
        emotional_intensity = 0
        detected_emotions = []
        
        # Check for emotional cues
        for emotion, cues in self.emotional_cues.items():
            for cue in cues:
                if cue in input_lower:
                    detected_emotions.append(emotion.value)
                    if emotional_state == EmotionalContext.NEUTRAL:
                        emotional_state = emotion
                    emotional_intensity += 1
        
        # Detect urgency patterns
        time_pressure = self._detect_time_pressure(input_lower)
        
        # Detect relationship context
        relationship_context = self._detect_relationship_context(input_lower)
        
        # Detect value domain
        value_domain = self._detect_value_domain(input_lower)
        
        return {
            'emotional_state': emotional_state.value,
            'emotional_intensity': min(emotional_intensity, 5),  # Scale 1-5
            'detected_emotions': detected_emotions,
            'time_pressure': time_pressure,
            'relationship_context': relationship_context,
            'value_domain': value_domain,
            'requires_empathy': emotional_intensity > 0
        }
    
    def _detect_time_pressure(self, text: str) -> Dict:
        """Detect time-related pressure"""
        time_patterns = {
            'immediate': r'now|right away|immediate|this second|right now',
            'minutes': r'in \d+ minutes?|within minutes|few minutes',
            'hours': r'in \d+ hours?|within hours|couple hours',
            'today': r'today|this afternoon|tonight',
            'tomorrow': r'tomorrow|next day',
            'week': r'this week|by friday|weekend',
            'flexible': r'whenever|sometime|no rush|not urgent'
        }
        
        for time_frame, pattern in time_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    'time_frame': time_frame,
                    'pressure_level': self._calculate_time_pressure(time_frame)
                }
        
        return {'time_frame': 'unspecified', 'pressure_level': 2}
    
    def _calculate_time_pressure(self, time_frame: str) -> int:
        """Calculate time pressure level (1-5)"""
        pressure_map = {
            'immediate': 5,
            'minutes': 4,
            'hours': 3,
            'today': 3,
            'tomorrow': 2,
            'week': 2,
            'flexible': 1,
            'unspecified': 2
        }
        return pressure_map.get(time_frame, 2)
    
    def _detect_relationship_context(self, text: str) -> str:
        """Detect if request involves relationships"""
        relationship_cues = {
            'family': r'my (wife|husband|child|son|daughter|parent|mother|father|family)',
            'friend': r'my friend|buddy|pal|colleague',
            'professional': r'my boss|manager|client|customer|team',
            'self': r'i |me |my own|myself',
            'general': r'someone|anyone|people'
        }
        
        for context, pattern in relationship_cues.items():
            if re.search(pattern, text, re.IGNORECASE):
                return context
        
        return 'unspecified'
    
    def _detect_value_domain(self, text: str) -> Tuple[str, int]:
        """Detect the primary human value domain"""
        value_domains = {
            'health_safety': [
                'health', 'doctor', 'hospital', 'sick', 'pain', 'emergency',
                'safe', 'danger', 'risk', 'accident', 'injury'
            ],
            'family_relationships': [
                'family', 'spouse', 'child', 'parent', 'relative',
                'relationship', 'marriage', 'friend', 'love'
            ],
            'work_responsibility': [
                'work', 'job', 'career', 'project', 'deadline',
                'responsibility', 'duty', 'obligation', 'task'
            ],
            'financial': [
                'money', 'bank', 'payment', 'bill', 'debt',
                'financial', 'cost', 'price', 'budget'
            ],
            'education': [
                'learn', 'study', 'school', 'university', 'course',
                'education', 'knowledge', 'skill'
            ]
        }
        
        for domain, keywords in value_domains.items():
            if any(keyword in text for keyword in keywords):
                weight = self.value_weighting.get(domain, 5)
                return domain, weight
        
        return 'general', 3
    
    def analyze_priority(self, user_input: str, context: Dict = None) -> PriorityLevel:
        """Analyze priority with human context understanding"""
        input_lower = user_input.lower()
        
        # Check for critical safety issues first
        if self._is_critical_safety_issue(input_lower):
            return PriorityLevel.CRITICAL
        
        # Check patterns for each priority level
        for priority_level, pattern_data in self.priority_patterns.items():
            for pattern in pattern_data['patterns']:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    # Validate with context if available
                    if context and 'emotional_context' in context:
                        emotional_intensity = context['emotional_context']['emotional_intensity']
                        # Adjust priority based on emotional intensity
                        if emotional_intensity >= 4 and priority_level.value < PriorityLevel.URGENT.value:
                            return PriorityLevel.URGENT
                    
                    return priority_level
        
        # Consider time of day for default priority
        current_hour = datetime.datetime.now().hour
        if 22 <= current_hour or current_hour <= 6:  # Late night/early morning
            return PriorityLevel.LOW  # Lower priority for non-urgent night requests
        
        return PriorityLevel.MEDIUM
    
    def _is_critical_safety_issue(self, text: str) -> bool:
        """Check for life-threatening situations"""
        safety_patterns = [
            r'heart attack|stroke|seizure',
            r'can\'t breathe|choking|suffocating',
            r'bleeding.*badly|serious.*injury',
            r'fire.*burning|smoke.*inhalation',
            r'911|emergency.*services'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in safety_patterns)
    
    def assess_decision_maturity(self, priority: PriorityLevel, 
                                impact: int, 
                                emotional_context: Dict) -> str:
        """Determine appropriate decision-making maturity level"""
        
        # High priority + high emotional intensity = collaborative decision
        if (priority.value >= PriorityLevel.URGENT.value and 
            emotional_context['emotional_intensity'] >= 3):
            return 'collaborative'
        
        # Ethical considerations
        if self._has_ethical_considerations(emotional_context):
            return 'ethical'
        
        # High impact decisions
        if impact >= 4:
            return 'deliberative'
        
        # Moderate impact with emotional context
        if impact >= 3 and emotional_context['requires_empathy']:
            return 'informed'
        
        return 'automatic'
    
    def _has_ethical_considerations(self, emotional_context: Dict) -> bool:
        """Check for ethical dimensions"""
        ethical_emotions = [
            EmotionalContext.CONFUSED.value,
            EmotionalContext.FRUSTRATED.value
        ]
        
        ethical_domains = ['family_relationships', 'health_safety']
        
        return (emotional_context['emotional_state'] in ethical_emotions or
                emotional_context['value_domain'][0] in ethical_domains)
    
    def make_decision(self, user_input: str, context: Dict = None) -> Dict:
        """Make human-centric decision with full context analysis"""
        
        # Analyze emotional context
        emotional_context = self.detect_emotional_context(user_input, context)
        
        # Analyze priority
        priority = self.analyze_priority(user_input, {
            'emotional_context': emotional_context
        })
        
        # Assess impact
        impact = self._assess_comprehensive_impact(user_input, emotional_context)
        
        # Determine decision maturity
        decision_maturity = self.assess_decision_maturity(priority, impact, emotional_context)
        
        # Calculate nuanced decision score
        decision_score = self._calculate_nuanced_score(priority, impact, emotional_context)
        
        # Generate human-centric recommendations
        recommendations = self._generate_recommendations(
            priority, impact, emotional_context, decision_maturity
        )
        
        # Build comprehensive decision response
        decision = {
            # Core assessment
            'priority': {
                'level': priority.value,
                'name': priority.name,
                'description': self._get_priority_description(priority, emotional_context)
            },
            
            # Human context
            'human_context': emotional_context,
            
            # Impact assessment
            'impact': {
                'score': impact,
                'domain': emotional_context['value_domain'][0],
                'domain_weight': emotional_context['value_domain'][1],
                'description': self._get_impact_description(impact)
            },
            
            # Decision framework
            'decision_framework': {
                'maturity_level': decision_maturity,
                'maturity_description': self.decision_maturity[decision_maturity]['description'],
                'requires_human_input': decision_maturity in ['collaborative', 'ethical'],
                'suggested_approach': self._get_suggested_approach(decision_maturity)
            },
            
            # Action plan
            'action_plan': {
                'timing': self._determine_action_timing(priority, emotional_context),
                'pace': self._determine_action_pace(emotional_context),
                'communication_style': self._determine_communication_style(emotional_context),
                'confirmation_needed': self._needs_confirmation(priority, impact, emotional_context)
            },
            
            # Recommendations
            'recommendations': recommendations,
            
            # Meta information
            'meta': {
                'confidence_score': self._calculate_confidence(priority, emotional_context),
                'risk_assessment': self._assess_risk(priority, impact, emotional_context),
                'sensitivity_level': self._determine_sensitivity(emotional_context),
                'processing_time_estimate': self._estimate_processing_time(decision_maturity)
            }
        }
        
        return decision
    
    def _assess_comprehensive_impact(self, user_input: str, emotional_context: Dict) -> int:
        """Assess impact with human factors"""
        base_impact = 2  # Default
        
        # Adjust based on value domain weight
        domain_weight = emotional_context['value_domain'][1]
        base_impact = max(base_impact, min(domain_weight // 2, 5))
        
        # Adjust for emotional intensity
        emotional_intensity = emotional_context['emotional_intensity']
        base_impact = min(5, base_impact + (emotional_intensity // 2))
        
        # Adjust for time pressure
        time_pressure = emotional_context['time_pressure']['pressure_level']
        if time_pressure >= 4:
            base_impact += 1
        
        # Check for critical words
        critical_words = ['emergency', 'crisis', 'urgent', 'critical', 'vital']
        if any(word in user_input.lower() for word in critical_words):
            base_impact = min(5, base_impact + 2)
        
        return min(max(base_impact, 1), 5)  # Ensure between 1-5
    
    def _calculate_nuanced_score(self, priority: PriorityLevel, 
                                impact: int, 
                                emotional_context: Dict) -> float:
        """Calculate nuanced decision score (0-100)"""
        
        base_score = priority.value * impact * 2
        
        # Adjust for emotional context
        emotional_modifier = 1.0
        
        if emotional_context['requires_empathy']:
            emotional_modifier += 0.3
        
        if emotional_context['emotional_intensity'] >= 3:
            emotional_modifier += 0.2
        
        # Adjust for relationship context
        relationship_modifier = 1.0
        if emotional_context['relationship_context'] in ['family', 'friend']:
            relationship_modifier += 0.2
        
        # Adjust for time pressure
        time_modifier = 1.0
        if emotional_context['time_pressure']['pressure_level'] >= 4:
            time_modifier += 0.3
        
        final_score = base_score * emotional_modifier * relationship_modifier * time_modifier
        
        return min(final_score, 100)
    
    def _generate_recommendations(self, priority: PriorityLevel, 
                                 impact: int, 
                                 emotional_context: Dict,
                                 decision_maturity: str) -> List[Dict]:
        """Generate human-centric recommendations"""
        
        recommendations = []
        
        # Emotional support recommendations
        if emotional_context['requires_empathy']:
            recommendations.append({
                'type': 'emotional_support',
                'suggestion': self._get_emotional_support_suggestion(emotional_context),
                'priority': 'high' if emotional_context['emotional_intensity'] >= 3 else 'medium'
            })
        
        # Timing recommendations
        recommendations.append({
            'type': 'timing',
            'suggestion': self._get_timing_suggestion(priority, emotional_context),
            'priority': 'high' if priority.value >= PriorityLevel.URGENT.value else 'medium'
        })
        
        # Communication recommendations
        recommendations.append({
            'type': 'communication',
            'suggestion': self._get_communication_suggestion(emotional_context),
            'priority': 'medium'
        })
        
        # Decision process recommendations
        if decision_maturity in ['collaborative', 'ethical']:
            recommendations.append({
                'type': 'process',
                'suggestion': self._get_process_suggestion(decision_maturity),
                'priority': 'high'
            })
        
        return recommendations
    
    def _get_emotional_support_suggestion(self, emotional_context: Dict) -> str:
        """Get appropriate emotional support suggestion"""
        
        emotion = emotional_context['emotional_state']
        intensity = emotional_context['emotional_intensity']
        
        suggestions = {
            EmotionalContext.STRESSED.value: [
                "I understand this feels overwhelming. Let's tackle one thing at a time.",
                "It sounds like there's a lot going on. Would it help to prioritize together?"
            ],
            EmotionalContext.ANXIOUS.value: [
                "I hear your concern. Let's gather more information to reduce uncertainty.",
                "It's normal to feel anxious about this. We can work through it step by step."
            ],
            EmotionalContext.FRUSTRATED.value: [
                "That sounds frustrating. Let's figure out what's not working and find a solution.",
                "I understand your frustration. Sometimes taking a systematic approach helps."
            ],
            EmotionalContext.CONFUSED.value: [
                "It's completely understandable to feel confused. Let me clarify what I understand.",
                "I can see how this might be confusing. Would it help if I break it down?"
            ],
            EmotionalContext.EXCITED.value: [
                "That's wonderful news! I'm excited for you.",
                "How fantastic! Let me help you make the most of this opportunity."
            ]
        }
        
        default = "I understand. Let me help you work through this."
        
        if emotion in suggestions:
            # Choose suggestion based on intensity
            if intensity >= 4:
                return suggestions[emotion][0]  # More empathetic
            else:
                return suggestions[emotion][1]  # More practical
        
        return default
    
    def _get_timing_suggestion(self, priority: PriorityLevel, emotional_context: Dict) -> str:
        """Get timing suggestion based on human factors"""
        
        time_pressure = emotional_context['time_pressure']['pressure_level']
        
        if priority == PriorityLevel.CRITICAL:
            return "This requires immediate attention. I'll prioritize this above everything else."
        elif priority == PriorityLevel.URGENT and time_pressure >= 4:
            return "This is time-sensitive. Let's address this right away."
        elif emotional_context['emotional_intensity'] >= 3:
            return "I sense this is important to you. I'll give this my focused attention now."
        else:
            return "I'll handle this in an appropriate timeframe that respects your needs."
    
    def _determine_action_pace(self, emotional_context: Dict) -> str:
        """Determine appropriate pace for action"""
        
        if emotional_context['time_pressure']['pressure_level'] >= 4:
            return "deliberate_haste"  # Quick but careful
        elif emotional_context['emotional_intensity'] >= 3:
            return "methodical_care"  # Careful and considerate
        else:
            return "normal_pace"
    
    def _determine_communication_style(self, emotional_context: Dict) -> str:
        """Determine appropriate communication style"""
        
        emotion = emotional_context['emotional_state']
        
        styles = {
            EmotionalContext.STRESSED.value: "calm_reassuring",
            EmotionalContext.ANXIOUS.value: "clear_reassuring",
            EmotionalContext.FRUSTRATED.value: "patient_problem_solving",
            EmotionalContext.CONFUSED.value: "clear_simple",
            EmotionalContext.EXCITED.value: "enthusiastic_engaging"
        }
        
        return styles.get(emotion, "clear_respectful")
    
    def get_enhanced_decision_summary(self, user_input: str) -> str:
        """Get comprehensive human-readable decision summary"""
        
        decision = self.make_decision(user_input)
        
        summary = f"""
        🤔 HUMAN-CENTRIC DECISION ANALYSIS
        {'='*50}
        
        📊 CORE ASSESSMENT
        • Priority: {decision['priority']['name']} (Level {decision['priority']['level']})
        • {decision['priority']['description']}
        
        ❤️  HUMAN CONTEXT
        • Emotional State: {decision['human_context']['emotional_state'].title()}
        • Intensity: {'▮' * decision['human_context']['emotional_intensity']}{'▯' * (5 - decision['human_context']['emotional_intensity'])} ({decision['human_context']['emotional_intensity']}/5)
        • Relationship: {decision['human_context']['relationship_context'].title()}
        • Value Domain: {decision['human_context']['value_domain'][0].replace('_', ' ').title()}
        
        ⚖️  IMPACT & RISK
        • Impact Score: {decision['impact']['score']}/5
        • Risk Level: {decision['meta']['risk_assessment']}
        • Sensitivity: {decision['meta']['sensitivity_level'].title()}
        
        🎯 DECISION FRAMEWORK
        • Maturity Level: {decision['decision_framework']['maturity_level'].title()}
        • Approach: {decision['decision_framework']['suggested_approach']}
        • {'🤝 Requires Human Collaboration' if decision['decision_framework']['requires_human_input'] else '✅ Can Proceed Autonomously'}
        
        📅 ACTION PLAN
        • Timing: {decision['action_plan']['timing']}
        • Pace: {decision['action_plan']['pace'].replace('_', ' ').title()}
        • Communication Style: {decision['action_plan']['communication_style'].replace('_', ' ').title()}
        • {'🔔 Requires Confirmation' if decision['action_plan']['confirmation_needed'] else '🟢 Can Proceed'}
        
        💡 RECOMMENDATIONS
        """
        
        for rec in decision['recommendations']:
            emoji = {
                'emotional_support': '❤️',
                'timing': '⏰',
                'communication': '💬',
                'process': '🔄'
            }.get(rec['type'], '•')
            
            summary += f"    {emoji} {rec['suggestion']}\n"
        
        summary += f"""
        🔍 META INFORMATION
        • Confidence: {decision['meta']['confidence_score']}%
        • Processing Time: {decision['meta']['processing_time_estimate']}
        
        {'='*50}
        Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return summary.strip()

    # Helper methods for the decision components
    def _get_priority_description(self, priority: PriorityLevel, emotional_context: Dict) -> str:
        descriptions = {
            PriorityLevel.CRITICAL: "Immediate attention required for safety or critical function",
            PriorityLevel.URGENT: "Time-sensitive matter requiring prompt response",
            PriorityLevel.HIGH: "Important task with significant consequences",
            PriorityLevel.MEDIUM: "Standard priority with normal response time",
            PriorityLevel.LOW: "Can be deferred without significant impact",
            PriorityLevel.PASSIVE: "Information only, no action needed"
        }
        
        base_desc = descriptions.get(priority, "Standard priority")
        
        # Add human context note if relevant
        if emotional_context['requires_empathy']:
            base_desc += " (Emotional sensitivity detected)"
        
        return base_desc
    
    def _get_impact_description(self, impact: int) -> str:
        descriptions = {
            5: "Critical impact on safety, relationships, or major life areas",
            4: "High impact on important aspects of life or work",
            3: "Moderate impact with noticeable consequences",
            2: "Low impact with minimal consequences",
            1: "Negligible impact"
        }
        return descriptions.get(impact, "Standard impact")
    
    def _get_suggested_approach(self, maturity_level: str) -> str:
        approaches = {
            'automatic': "Follow standard procedures with routine checks",
            'informed': "Gather basic information before proceeding",
            'deliberative': "Consider multiple factors and potential outcomes",
            'collaborative': "Engage human input and discussion",
            'ethical': "Consider moral implications and values"
        }
        return approaches.get(maturity_level, "Standard approach")
    
    def _determine_action_timing(self, priority: PriorityLevel, emotional_context: Dict) -> str:
        time_suggestions = {
            PriorityLevel.CRITICAL: "Immediately",
            PriorityLevel.URGENT: "Within 5 minutes",
            PriorityLevel.HIGH: "Within 30 minutes",
            PriorityLevel.MEDIUM: "Within 2 hours",
            PriorityLevel.LOW: "When convenient",
            PriorityLevel.PASSIVE: "No action needed"
        }
        
        base_time = time_suggestions.get(priority, "When convenient")
        
        # Adjust for emotional context
        if emotional_context['emotional_intensity'] >= 4:
            return f"Sooner: {base_time} (emotional urgency detected)"
        
        return base_time
    
    def _needs_confirmation(self, priority: PriorityLevel, impact: int, emotional_context: Dict) -> bool:
        """Determine if human confirmation is needed"""
        
        # Always confirm critical actions
        if priority == PriorityLevel.CRITICAL:
            return True
        
        # Confirm high-impact actions with emotional weight
        if impact >= 4 and emotional_context['requires_empathy']:
            return True
        
        # Confirm actions with ethical considerations
        if self._has_ethical_considerations(emotional_context):
            return True
        
        return False
    
    def _calculate_confidence(self, priority: PriorityLevel, emotional_context: Dict) -> int:
        """Calculate confidence score (0-100)"""
        
        base_confidence = 85
        
        # Adjust for emotional context clarity
        if emotional_context['emotional_state'] != EmotionalContext.NEUTRAL.value:
            base_confidence -= 10
        
        # Adjust for critical situations
        if priority == PriorityLevel.CRITICAL:
            base_confidence -= 5  # More cautious with critical matters
        
        return max(50, min(95, base_confidence))  # Keep within reasonable bounds
    
    def _assess_risk(self, priority: PriorityLevel, impact: int, emotional_context: Dict) -> str:
        """Assess risk level"""
        
        risk_score = priority.value * impact
        
        # Adjust for emotional context
        if emotional_context['requires_empathy']:
            risk_score += 2
        
        if risk_score >= 20:
            return "Critical Risk"
        elif risk_score >= 15:
            return "High Risk"
        elif risk_score >= 10:
            return "Medium Risk"
        elif risk_score >= 5:
            return "Low Risk"
        else:
            return "Minimal Risk"
    
    def _determine_sensitivity(self, emotional_context: Dict) -> str:
        """Determine sensitivity level"""
        
        if emotional_context['emotional_intensity'] >= 4:
            return "high_sensitivity"
        elif emotional_context['requires_empathy']:
            return "medium_sensitivity"
        elif emotional_context['relationship_context'] in ['family', 'friend']:
            return "relationship_sensitive"
        else:
            return "standard_sensitivity"
    
    def _estimate_processing_time(self, decision_maturity: str) -> str:
        """Estimate decision processing time"""
        
        times = {
            'automatic': "1-5 seconds",
            'informed': "5-15 seconds",
            'deliberative': "15-30 seconds",
            'collaborative': "30-60 seconds",
            'ethical': "1-2 minutes"
        }
        
        return times.get(decision_maturity, "10-20 seconds")

# Example usage demonstration
def demonstrate_enhanced_engine():
    """Demonstrate the enhanced decision engine with various scenarios"""
    
    engine = DecisionEngine()
    
    test_scenarios = [
        "I'm having chest pains and feeling dizzy - this is an emergency!",
        "I need to prepare for my job interview tomorrow morning",
        "My daughter locked herself in the bathroom and she's crying",
        "Can you help me find a recipe for dinner tonight?",
        "I'm feeling really overwhelmed with all my deadlines",
        "Just wanted to share that I got promoted today!",
        "I think there might be a security breach in our system",
        "When you have time, could you explain how this works?"
    ]
    
    print("🚀 ENHANCED DECISION ENGINE DEMONSTRATION\n")
    print("="*60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Scenario {i}: \"{scenario}\"")
        print("-"*40)
        
        decision = engine.make_decision(scenario)
        print(f"🎯 Priority: {decision['priority']['name']}")
        print(f"❤️  Emotion: {decision['human_context']['emotional_state']}")
        print(f"⏱️  Timing: {decision['action_plan']['timing']}")
        print(f"🤝 Framework: {decision['decision_framework']['maturity_level']}")
        
        # Show key recommendation
        if decision['recommendations']:
            first_rec = decision['recommendations'][0]
            print(f"💡 Suggestion: {first_rec['suggestion']}")
        
        print("-"*40)
    
    # Show detailed analysis for one scenario
    print("\n" + "="*60)
    print("📊 DETAILED ANALYSIS FOR SCENARIO 1:")
    print("="*60)
    
    detailed_summary = engine.get_enhanced_decision_summary(test_scenarios[0])
    print(detailed_summary)

if __name__ == "__main__":
    demonstrate_enhanced_engine()