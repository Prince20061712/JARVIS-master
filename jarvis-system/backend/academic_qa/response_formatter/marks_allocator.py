"""
Marks-Based Response Formatter for Exam-Oriented Answers
"""

from typing import Dict, Any, Optional
import re

class MarksBasedFormatter:
    """
    Formats responses based on marks allocation and exam patterns
    """
    
    def __init__(self):
        self.templates = {
            2: {
                'structure': ['definition'],
                'max_words': 50,
                'include_diagram': False
            },
            5: {
                'structure': ['definition', 'explanation', 'example'],
                'max_words': 150,
                'include_diagram': True
            },
            10: {
                'structure': ['definition', 'detailed_explanation', 'example', 
                             'application', 'diagram'],
                'max_words': 350,
                'include_diagram': True
            },
            15: {
                'structure': ['introduction', 'derivation', 'explanation', 
                             'example', 'application', 'conclusion', 'diagram'],
                'max_words': 600,
                'include_diagram': True
            }
        }
        
        self.subject_formats = {
            'mathematics': self._format_math,
            'physics': self._format_physics,
            'computer_science': self._format_cs,
            'electronics': self._format_electronics
        }
    
    def format_response(self, 
                       content: Dict[str, Any], 
                       marks: int,
                       subject: str,
                       question_type: str = 'theory') -> str:
        """Format response based on marks and subject"""
        
        # Get template for marks
        template = self.templates.get(marks, self.templates[5])
        
        # Apply subject-specific formatting
        if subject in self.subject_formats:
            return self.subject_formats[subject](content, marks, template)
        
        # Default formatting
        return self._format_generic(content, marks, template)
    
    def _format_math(self, content: Dict, marks: int, template: Dict) -> str:
        """Format mathematical answers"""
        response = []
        
        if marks <= 5:
            # Short answer with formula
            response.append(f"**Formula:** {content.get('formula', '')}")
            response.append(f"**Solution:** {content.get('solution', '')}")
        else:
            # Step-by-step derivation
            response.append("**Step-by-Step Derivation:**")
            for i, step in enumerate(content.get('steps', []), 1):
                response.append(f"Step {i}: {step}")
            
            if content.get('diagram'):
                response.append(f"\n**Diagram:**\n{content['diagram']}")
        
        return '\n\n'.join(response)
    
    def _format_physics(self, content: Dict, marks: int, template: Dict) -> str:
        """Format physics answers with diagrams"""
        response = []
        
        # Always include definition for physics
        response.append(f"**Definition:** {content.get('definition', '')}")
        
        if marks >= 5:
            response.append(f"**Explanation:** {content.get('explanation', '')}")
            response.append(f"**Formula:** {content.get('formula', '')}")
            
            if content.get('numerical_example'):
                response.append(f"**Numerical Example:**\n{content['numerical_example']}")
        
        if marks >= 10 and content.get('application'):
            response.append(f"**Real-world Application:** {content['application']}")
        
        if template['include_diagram'] and content.get('diagram'):
            response.append(f"\n**Diagram:**\n{content['diagram']}")
        
        return '\n\n'.join(response)
    
    def _format_cs(self, content: Dict, marks: int, template: Dict) -> str:
        """Format computer science answers with code"""
        response = []
        
        response.append(f"**Concept:** {content.get('definition', '')}")
        
        if marks >= 5:
            response.append(f"**Explanation:** {content.get('explanation', '')}")
            
            if content.get('algorithm'):
                response.append(f"**Algorithm:**\n{content['algorithm']}")
            
            if content.get('code'):
                response.append(f"**Code Example:**\n```python\n{content['code']}\n```")
        
        if marks >= 10 and content.get('complexity'):
            response.append(f"**Time Complexity:** {content['complexity']}")
            response.append(f"**Space Complexity:** {content.get('space_complexity', 'N/A')}")
        
        return '\n\n'.join(response)
    
    def _format_electronics(self, content: Dict, marks: int, template: Dict) -> str:
        """Format electronics answers with circuit diagrams"""
        response = []
        
        response.append(f"**Definition:** {content.get('definition', '')}")
        
        if marks >= 5:
            response.append(f"**Working Principle:** {content.get('working', '')}")
            
            if content.get('circuit_diagram'):
                response.append(f"**Circuit Diagram:**\n{content['circuit_diagram']}")
            
            response.append(f"**Formula:** {content.get('formula', '')}")
        
        if marks >= 10 and content.get('applications'):
            response.append("**Applications:**")
            for app in content['applications']:
                response.append(f"• {app}")
        
        return '\n\n'.join(response)
    
    def _format_generic(self, content: Dict, marks: int, template: Dict) -> str:
        """Generic formatting for other subjects"""
        response = []
        
        for section in template['structure']:
            if section in content:
                response.append(f"**{section.title()}:** {content[section]}")
            elif section == 'diagram' and template['include_diagram']:
                if content.get('diagram'):
                    response.append(f"**Diagram:**\n{content['diagram']}")
        
        return '\n\n'.join(response)
