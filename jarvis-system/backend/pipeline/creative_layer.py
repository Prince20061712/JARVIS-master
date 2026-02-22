"""
Creative Layer - Handles response generation, formatting, and academic styling
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Output formats for responses"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    LATEX = "latex"
    CODE = "code"
    DIAGRAM = "diagram"
    STEP_BY_STEP = "step_by_step"
    BULLET_POINTS = "bullet_points"
    TABLE = "table"


class AcademicStyle(Enum):
    """Academic writing styles"""
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    SIMPLIFIED = "simplified"
    DETAILED = "detailed"
    TEACHING = "teaching"
    RESEARCH = "research"
    EXAM_PREP = "exam_prep"


@dataclass
class ResponseTemplate:
    """Template for response generation"""
    format: ResponseFormat
    style: AcademicStyle
    structure: List[str]
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CreativeOutput:
    """Output from creative layer"""
    content: str
    format: ResponseFormat
    style: AcademicStyle
    word_count: int
    reading_time_minutes: float
    has_code: bool = False
    has_math: bool = False
    has_diagram: bool = False
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CreativeLayer:
    """
    Handles response generation, formatting, and academic styling.
    Creates engaging, well-structured educational content.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Response templates by format and style
        self.templates: Dict[Tuple[ResponseFormat, AcademicStyle], ResponseTemplate] = {}
        
        # Format converters
        self.format_converters = self._init_format_converters()
        
        # Style processors
        self.style_processors = self._init_style_processors()
        
        # Academic phrase library
        self.academic_phrases = self._init_academic_phrases()
        
        # Initialize templates
        self._init_templates()
        
        logger.info("Creative Layer initialized with %d templates", len(self.templates))
    
    def _init_format_converters(self) -> Dict[ResponseFormat, callable]:
        """Initialize format conversion functions"""
        return {
            ResponseFormat.TEXT: self._convert_to_text,
            ResponseFormat.MARKDOWN: self._convert_to_markdown,
            ResponseFormat.HTML: self._convert_to_html,
            ResponseFormat.LATEX: self._convert_to_latex,
            ResponseFormat.CODE: self._convert_to_code,
            ResponseFormat.STEP_BY_STEP: self._format_as_steps,
            ResponseFormat.BULLET_POINTS: self._format_as_bullets,
            ResponseFormat.TABLE: self._format_as_table
        }
    
    def _init_style_processors(self) -> Dict[AcademicStyle, callable]:
        """Initialize style processing functions"""
        return {
            AcademicStyle.FORMAL: self._apply_formal_style,
            AcademicStyle.CONVERSATIONAL: self._apply_conversational_style,
            AcademicStyle.SIMPLIFIED: self._apply_simplified_style,
            AcademicStyle.DETAILED: self._apply_detailed_style,
            AcademicStyle.TEACHING: self._apply_teaching_style,
            AcademicStyle.RESEARCH: self._apply_research_style,
            AcademicStyle.EXAM_PREP: self._apply_exam_prep_style
        }
    
    def _init_academic_phrases(self) -> Dict[str, List[str]]:
        """Initialize academic phrase library"""
        return {
            'introduction': [
                "Let's explore",
                "Consider the concept of",
                "We can understand",
                "Let me explain"
            ],
            'explanation': [
                "This means that",
                "In other words",
                "Essentially,",
                "To put it simply"
            ],
            'example': [
                "For example,",
                "Consider the following:",
                "To illustrate,",
                "A practical example is"
            ],
            'conclusion': [
                "In conclusion,",
                "To summarize,",
                "Therefore,",
                "Thus we can see that"
            ],
            'emphasis': [
                "Importantly,",
                "Notably,",
                "Crucially,",
                "Significantly,"
            ],
            'transition': [
                "Furthermore,",
                "Additionally,",
                "Moreover,",
                "In addition,"
            ]
        }
    
    def _init_templates(self):
        """Initialize response templates"""
        # Teaching template
        self.templates[(ResponseFormat.TEXT, AcademicStyle.TEACHING)] = ResponseTemplate(
            format=ResponseFormat.TEXT,
            style=AcademicStyle.TEACHING,
            structure=[
                "hook",
                "introduction",
                "core_concept",
                "example",
                "practice",
                "summary",
                "next_steps"
            ],
            examples=[
                "Let's learn about [topic]! Think of it like [analogy]...",
                "Today we'll explore [concept]. Here's a simple way to understand it..."
            ]
        )
        
        # Exam prep template
        self.templates[(ResponseFormat.TEXT, AcademicStyle.EXAM_PREP)] = ResponseTemplate(
            format=ResponseFormat.TEXT,
            style=AcademicStyle.EXAM_PREP,
            structure=[
                "key_points",
                "common_mistakes",
                "practice_questions",
                "tips",
                "quick_reference"
            ],
            examples=[
                "Key points for [topic]:\n1. ...\n2. ...",
                "Common exam questions about [topic] include..."
            ]
        )
        
        # Research template
        self.templates[(ResponseFormat.MARKDOWN, AcademicStyle.RESEARCH)] = ResponseTemplate(
            format=ResponseFormat.MARKDOWN,
            style=AcademicStyle.RESEARCH,
            structure=[
                "abstract",
                "introduction",
                "methodology",
                "findings",
                "discussion",
                "references"
            ],
            examples=[
                "# Research Summary: [Topic]\n\n## Abstract\n...",
                "## Key Findings\n- Finding 1\n- Finding 2"
            ]
        )
    
    async def process(self,
                     content: str,
                     context: Dict[str, Any],
                     target_format: ResponseFormat = ResponseFormat.TEXT,
                     target_style: AcademicStyle = AcademicStyle.TEACHING,
                     word_limit: Optional[int] = None) -> CreativeOutput:
        """
        Process and format content creatively
        
        Args:
            content: Raw content to format
            context: Context information
            target_format: Desired output format
            target_style: Desired academic style
            word_limit: Optional word limit
            
        Returns:
            Formatted creative output
        """
        try:
            # Get template
            template = self._get_template(target_format, target_style)
            
            # Apply structure
            structured_content = await self._apply_structure(content, template, context)
            
            # Apply style
            styled_content = await self._apply_style(structured_content, target_style, context)
            
            # Apply format
            formatted_content = await self._apply_format(styled_content, target_format, context)
            
            # Enhance with academic phrases
            enhanced_content = self._enhance_with_phrases(formatted_content, target_style, context)
            
            # Apply word limit if specified
            if word_limit:
                enhanced_content = self._apply_word_limit(enhanced_content, word_limit)
            
            # Calculate metrics
            word_count = len(enhanced_content.split())
            reading_time = word_count / 200  # Average reading speed: 200 wpm
            
            # Detect content features
            has_code = '```' in enhanced_content or any(lang in enhanced_content for lang in ['def ', 'class ', 'function'])
            has_math = any(symbol in enhanced_content for symbol in ['$', '\\', '∫', '∑', '√'])
            has_diagram = any(marker in enhanced_content for marker in ['graph', 'diagram', 'figure'])
            
            # Extract citations (simplified)
            citations = self._extract_citations(enhanced_content)
            
            return CreativeOutput(
                content=enhanced_content,
                format=target_format,
                style=target_style,
                word_count=word_count,
                reading_time_minutes=reading_time,
                has_code=has_code,
                has_math=has_math,
                has_diagram=has_diagram,
                citations=citations,
                metadata={
                    'template_used': template.structure if template else None,
                    'enhancements_applied': True
                }
            )
            
        except Exception as e:
            logger.error(f"Error in creative processing: {str(e)}", exc_info=True)
            return CreativeOutput(
                content=content,
                format=ResponseFormat.TEXT,
                style=AcademicStyle.CONVERSATIONAL,
                word_count=len(content.split()),
                reading_time_minutes=len(content.split()) / 200,
                metadata={'error': str(e)}
            )
    
    def _get_template(self, format: ResponseFormat, style: AcademicStyle) -> Optional[ResponseTemplate]:
        """Get appropriate template for format and style"""
        return self.templates.get((format, style))
    
    async def _apply_structure(self, 
                              content: str, 
                              template: Optional[ResponseTemplate], 
                              context: Dict[str, Any]) -> str:
        """Apply structural template to content"""
        if not template:
            return content
        
        structured_parts = []
        
        for section in template.structure:
            section_content = self._generate_section(section, content, context)
            if section_content:
                structured_parts.append(section_content)
        
        return '\n\n'.join(structured_parts)
    
    def _generate_section(self, section: str, content: str, context: Dict[str, Any]) -> str:
        """Generate content for a specific section"""
        topic = context.get('topic', 'this topic')
        
        section_templates = {
            'hook': f"Let's explore {topic} in an engaging way!",
            'introduction': f"Today we'll learn about {topic}. This is an important concept because...",
            'core_concept': content,
            'example': f"Here's an example to help understand {topic}:\n{context.get('example', 'Example goes here')}",
            'practice': f"Try this practice question: {context.get('practice_question', 'Question goes here')}",
            'summary': f"To summarize what we've learned about {topic}:",
            'next_steps': f"Ready to learn more? Next, we could explore {context.get('next_topic', 'related concepts')}.",
            'key_points': f"Key points about {topic}:",
            'common_mistakes': f"Common mistakes when learning {topic}:",
            'tips': f"Tips for mastering {topic}:"
        }
        
        return section_templates.get(section, "")
    
    async def _apply_style(self, content: str, style: AcademicStyle, context: Dict[str, Any]) -> str:
        """Apply stylistic transformations to content"""
        if style in self.style_processors:
            return self.style_processors[style](content, context)
        return content
    
    def _apply_formal_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply formal academic style"""
        # Use formal language
        replacements = {
            "can't": "cannot",
            "don't": "do not",
            "won't": "will not",
            "it's": "it is",
            "I'll": "I will",
            "gonna": "going to",
            "wanna": "want to"
        }
        
        for informal, formal in replacements.items():
            content = content.replace(informal, formal)
        
        # Add formal markers
        content = f"According to established principles, {content[0].lower()}{content[1:]}"
        
        return content
    
    def _apply_conversational_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply conversational style"""
        # Make it more conversational
        if not content.startswith(("Hey", "Hi", "Hello")):
            content = f"Hey there! {content}"
        
        # Add conversational markers
        content = content.replace("Therefore,", "So,")
        content = content.replace("Furthermore,", "Also,")
        content = content.replace("Nevertheless,", "But,")
        
        # Add occasional questions
        if "?" not in content:
            content += " Does that make sense?"
        
        return content
    
    def _apply_simplified_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply simplified style for easier understanding"""
        # Break long sentences
        sentences = content.split('. ')
        simplified = []
        
        for sentence in sentences:
            if len(sentence.split()) > 15:
                # Split long sentences
                parts = sentence.split(', ')
                for part in parts:
                    simplified.append(part + '.')
            else:
                simplified.append(sentence + '.')
        
        content = ' '.join(simplified)
        
        # Simplify vocabulary
        complex_words = {
            'utilize': 'use',
            'implement': 'use',
            'commence': 'start',
            'terminate': 'end',
            'facilitate': 'help',
            'demonstrate': 'show',
            'illustrate': 'show'
        }
        
        for complex_word, simple_word in complex_words.items():
            content = content.replace(complex_word, simple_word)
        
        return content
    
    def _apply_detailed_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply detailed explanatory style"""
        # Add explanatory phrases
        content = content.replace(".", ". Let me explain further: ")
        
        # Add depth markers
        if context.get('depth'):
            content += f"\n\nFor more depth, consider that {context['depth']}"
        
        return content
    
    def _apply_teaching_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply teaching-oriented style"""
        # Add teaching elements
        sections = []
        
        # Opening question
        sections.append(f"Have you ever wondered about {context.get('topic', 'this topic')}?")
        
        # Core content with checkpoints
        sections.append(content)
        
        # Comprehension check
        sections.append(f"Let's check your understanding: {context.get('check_question', 'What did we learn?')}")
        
        # Encouragement
        sections.append("Great job! You're making excellent progress.")
        
        return '\n\n'.join(sections)
    
    def _apply_research_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply research paper style"""
        # Format as research content
        sections = [
            "## Abstract",
            context.get('abstract', 'Brief summary of the topic...'),
            "## Introduction",
            content,
            "## Key Findings",
            context.get('findings', 'Main findings...'),
            "## References",
            context.get('references', '1. Reference 1\n2. Reference 2')
        ]
        
        return '\n\n'.join(sections)
    
    def _apply_exam_prep_style(self, content: str, context: Dict[str, Any]) -> str:
        """Apply exam preparation style"""
        # Format as exam prep
        sections = [
            "📚 EXAM PREPARATION",
            "=" * 50,
            f"Topic: {context.get('topic', 'General')}",
            "\n🔑 KEY POINTS:",
            self._format_as_bullets(content, context),
            "\n⚠️ COMMON MISTAKES:",
            context.get('mistakes', '• Mistake 1\n• Mistake 2'),
            "\n📝 PRACTICE QUESTIONS:",
            context.get('practice', '1. Question 1\n2. Question 2'),
            "\n💡 TIPS:",
            context.get('tips', '• Tip 1\n• Tip 2')
        ]
        
        return '\n'.join(sections)
    
    async def _apply_format(self, content: str, format: ResponseFormat, context: Dict[str, Any]) -> str:
        """Apply format conversion to content"""
        if format in self.format_converters:
            return self.format_converters[format](content, context)
        return content
    
    def _convert_to_text(self, content: str, context: Dict[str, Any]) -> str:
        """Convert to plain text"""
        # Remove markdown and special characters
        content = re.sub(r'[*_~`]', '', content)
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Remove links
        return content
    
    def _convert_to_markdown(self, content: str, context: Dict[str, Any]) -> str:
        """Convert to markdown"""
        # Add markdown formatting
        lines = content.split('\n')
        formatted = []
        
        for line in lines:
            if line.strip():
                if len(line) < 50:  # Potential heading
                    formatted.append(f"## {line}")
                else:
                    formatted.append(line)
        
        return '\n'.join(formatted)
    
    def _convert_to_html(self, content: str, context: Dict[str, Any]) -> str:
        """Convert to HTML"""
        # Simple HTML conversion
        html = ["<div class='creative-content'>"]
        
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                if len(line) < 50:
                    html.append(f"<h3>{line}</h3>")
                else:
                    html.append(f"<p>{line}</p>")
        
        html.append("</div>")
        return '\n'.join(html)
    
    def _convert_to_latex(self, content: str, context: Dict[str, Any]) -> str:
        """Convert to LaTeX format"""
        # Wrap math expressions
        content = re.sub(r'(\d+\.?\d*\s*[\+\-\*\/]\s*\d+\.?\d*)', r'$\1$', content)
        
        # Add LaTeX document structure
        latex = [
            "\\documentclass{article}",
            "\\begin{document}",
            content,
            "\\end{document}"
        ]
        
        return '\n'.join(latex)
    
    def _convert_to_code(self, content: str, context: Dict[str, Any]) -> str:
        """Format as code block"""
        language = context.get('language', 'python')
        return f"```{language}\n{content}\n```"
    
    def _format_as_steps(self, content: str, context: Dict[str, Any]) -> str:
        """Format content as step-by-step instructions"""
        steps = content.split('. ')
        formatted = []
        
        for i, step in enumerate(steps, 1):
            if step.strip():
                formatted.append(f"Step {i}: {step.strip()}.")
        
        return '\n'.join(formatted)
    
    def _format_as_bullets(self, content: str, context: Dict[str, Any]) -> str:
        """Format content as bullet points"""
        points = content.split('. ')
        formatted = []
        
        for point in points:
            if point.strip():
                formatted.append(f"• {point.strip()}")
        
        return '\n'.join(formatted)
    
    def _format_as_table(self, content: str, context: Dict[str, Any]) -> str:
        """Format content as table"""
        rows = content.split('\n')
        if not rows:
            return content
        
        # Assume first row is header
        headers = rows[0].split(',')
        table = []
        
        # Create markdown table
        table.append('| ' + ' | '.join(headers) + ' |')
        table.append('|' + '|'.join([' --- ' for _ in headers]) + '|')
        
        for row in rows[1:]:
            cells = row.split(',')
            table.append('| ' + ' | '.join(cells) + ' |')
        
        return '\n'.join(table)
    
    def _enhance_with_phrases(self, content: str, style: AcademicStyle, context: Dict[str, Any]) -> str:
        """Enhance content with academic phrases"""
        sentences = content.split('. ')
        enhanced = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # Add variety based on position
                if i == 0:  # Introduction
                    phrase = self._get_random_phrase('introduction')
                    sentence = f"{phrase} {sentence[0].lower()}{sentence[1:]}"
                elif i == len(sentences) - 1:  # Conclusion
                    phrase = self._get_random_phrase('conclusion')
                    sentence = f"{phrase} {sentence[0].lower()}{sentence[1:]}"
                elif i % 3 == 0:  # Every third sentence
                    phrase = self._get_random_phrase('transition')
                    sentence = f"{phrase} {sentence[0].lower()}{sentence[1:]}"
                
                enhanced.append(sentence)
        
        return '. '.join(enhanced)
    
    def _get_random_phrase(self, category: str) -> str:
        """Get a random phrase from category"""
        import random
        phrases = self.academic_phrases.get(category, [''])
        return random.choice(phrases) if phrases else ''
    
    def _apply_word_limit(self, content: str, word_limit: int) -> str:
        """Apply word limit to content"""
        words = content.split()
        if len(words) <= word_limit:
            return content
        
        # Truncate intelligently at sentence boundaries
        truncated = words[:word_limit]
        last_sentence = ' '.join(truncated)
        
        # Find last complete sentence
        sentences = last_sentence.split('. ')
        if len(sentences) > 1:
            return '. '.join(sentences[:-1]) + '.'
        
        return last_sentence + '...'
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from content"""
        citations = []
        
        # Look for citation patterns
        citation_patterns = [
            r'\(([^,]+,\s*\d{4})\)',  # (Author, 2020)
            r'\[\d+\]',  # [1]
            r'according to ([^(]+)\(\d{4}\)'  # according to Author (2020)
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return citations
    
    def generate_variations(self, content: str, count: int = 3) -> List[str]:
        """Generate multiple variations of content"""
        variations = []
        
        for i in range(count):
            # Apply different styles randomly
            style = list(AcademicStyle)[i % len(AcademicStyle)]
            variation = self._apply_style(content, style, {})
            variations.append(variation)
        
        return variations
    
    def get_format_recommendation(self, content_type: str, user_preferences: Dict[str, Any]) -> ResponseFormat:
        """Get recommended format based on content type and user preferences"""
        recommendations = {
            'explanation': ResponseFormat.TEXT,
            'example': ResponseFormat.CODE if 'code' in content_type else ResponseFormat.TEXT,
            'formula': ResponseFormat.LATEX,
            'comparison': ResponseFormat.TABLE,
            'procedure': ResponseFormat.STEP_BY_STEP,
            'summary': ResponseFormat.BULLET_POINTS,
            'diagram': ResponseFormat.DIAGRAM
        }
        
        return recommendations.get(content_type, ResponseFormat.TEXT)
    
    def get_style_recommendation(self, 
                                user_level: str, 
                                purpose: str,
                                emotional_state: Optional[str] = None) -> AcademicStyle:
        """Get recommended style based on user context"""
        if emotional_state == 'frustrated':
            return AcademicStyle.SIMPLIFIED
        elif emotional_state == 'confident':
            return AcademicStyle.DETAILED
        
        level_recommendations = {
            'beginner': AcademicStyle.SIMPLIFIED,
            'intermediate': AcademicStyle.TEACHING,
            'advanced': AcademicStyle.DETAILED,
            'expert': AcademicStyle.RESEARCH
        }
        
        purpose_recommendations = {
            'learning': AcademicStyle.TEACHING,
            'review': AcademicStyle.SIMPLIFIED,
            'exam': AcademicStyle.EXAM_PREP,
            'research': AcademicStyle.RESEARCH
        }
        
        # Combine recommendations
        style = level_recommendations.get(user_level, AcademicStyle.TEACHING)
        if purpose in purpose_recommendations:
            style = purpose_recommendations[purpose]
        
        return style