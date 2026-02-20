from typing import Dict, Any, Optional, List
from utils.logger import logger

class PromptTemplates:
    """
    Manages specialized prompt templates for different academic scenarios.
    Supports variable insertion and few-shot examples.
    """
    def __init__(self):
        self.templates = {
            "explanation": """
Explain the following engineering concept in detail:
Topic: {topic}
Context: {context}

Requirements:
- Use clear, academic tone.
- Highlight key terms in bold.
- Provide a real-world engineering application.
- If it's for {marks} marks, format accordingly.

Answer:
""",
            "derivation": """
Derive the expression for {concept} starting from first principles.
Context provided: {context}

Include:
1. Definition of terms and assumptions.
2. Step-by-step mathematical steps.
3. Final expression in LaTeX format ($$ ... $$).
4. Physical significance of the result.

Derivation:
""",
            "code_gen": """
Write a {language} implementation for the following algorithmic problem:
Problem: {problem}
Constraints: {constraints}

Requirements:
1. Provide optimized code with comments.
2. Explain the logic briefly.
3. Include time and space complexity analysis (O-notation).

Implementation:
""",
            "problem_solving": """
Solve the following numerical problem step-by-step:
Problem: {query}
Known values: {values}

Steps:
1. List the relevant formulas.
2. Substitution with units.
3. Intermediate calculations.
4. Final result with proper significant figures.

Solution:
"""
        }

    def get_template(self, template_id: str, **kwargs) -> str:
        """Retrieves and populates a template with provided variables."""
        template = self.templates.get(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found. Using generic.")
            return "Please answer the following as an engineering tutor: {query}"
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable for template '{template_id}': {e}")
            return template # Return raw if formatting fails

    def customize_template(self, template_id: str, new_text: str):
        """Allows runtime updates to prompt templates."""
        self.templates[template_id] = new_text
        logger.info(f"Customized template: {template_id}")

    def validate_prompt(self, prompt: str) -> bool:
        """Basic safety/quality check on the generated prompt."""
        return len(prompt.strip()) > 20
