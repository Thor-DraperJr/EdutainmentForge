"""
Content processing and script generation for podcasts.

Transforms technical content into engaging podcast scripts.
"""

import re
from typing import Dict, List, Tuple
from utils.logger import get_logger


logger = get_logger(__name__)


class ScriptProcessor:
    """Processes content and generates podcast scripts."""
    
    def __init__(self):
        """Initialize the script processor."""
        self.intro_phrases = [
            "Welcome to today's learning session!",
            "Let's dive into an exciting topic!",
            "Today we're exploring something fascinating!",
            "Get ready for an educational adventure!"
        ]
        
        self.transition_phrases = [
            "Now, let's move on to",
            "Speaking of which",
            "This brings us to",
            "Another important aspect is",
            "Building on that idea"
        ]
        
        self.conclusion_phrases = [
            "To wrap things up",
            "In summary",
            "Let's recap what we've learned",
            "The key takeaway here is"
        ]
    
    def process_content_to_script(self, content: Dict[str, str]) -> Dict[str, str]:
        """
        Convert raw content into an engaging podcast script.
        
        Args:
            content: Dictionary with title, content, and url
            
        Returns:
            Dictionary with processed script information
        """
        logger.info(f"Processing content to script: {content['title']}")
        
        # Clean and structure the content
        cleaned_content = self._clean_content(content['content'])
        
        # Break into sections
        sections = self._break_into_sections(cleaned_content)
        
        # Generate script with narrative structure
        script = self._generate_narrative_script(content['title'], sections)
        
        # Add timing estimates
        word_count = len(script.split())
        estimated_duration = self._estimate_duration(word_count)
        
        return {
            'title': content['title'],
            'script': script,
            'word_count': word_count,
            'estimated_duration': estimated_duration,
            'source_url': content['url']
        }
    
    def _clean_content(self, content: str) -> str:
        """Clean and prepare content for script generation."""
        # Remove time/duration indicators
        content = re.sub(r'\b\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bcompleted\s+\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bestimated\s+time:?\s*\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        
        # Remove markdown headers (# ## ###)
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        
        # Remove markdown formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # **bold**
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # *italic*
        content = re.sub(r'`(.*?)`', r'\1', content)        # `code`
        content = re.sub(r'```.*?```', '[code example]', content, flags=re.DOTALL)  # code blocks
        
        # Remove URLs and links
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # [text](url)
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        
        # Remove bullet points and list formatting, but preserve the text
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        
        # Remove navigation/metadata text
        content = re.sub(r'\bnext\s+unit:?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bprevious\s+unit:?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bunit\s+\d+\s+of\s+\d+\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bmodule\s+\d+\s+of\s+\d+\b', '', content, flags=re.IGNORECASE)
        
        # Remove page/document metadata
        content = re.sub(r'\bkey\s+points?(\s+to\s+understand)?(\s+about)?:?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bin\s+this\s+unit,?\s+(you\s+will\s+learn|we\s+will\s+cover|you\s+will):?', '', content, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and newlines
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r'[ \t]+', ' ', content)       # Multiple spaces to single
        
        # Remove common technical artifacts
        content = re.sub(r'\s*\|\s*', ' ', content)     # Table separators
        content = re.sub(r'[{}[\]()<>]', '', content)   # Brackets and braces
        
        # Remove standalone colons that don't make sense in speech
        content = re.sub(r'\s*:\s*$', '.', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _break_into_sections(self, content: str) -> List[str]:
        """Break content into logical sections for narrative flow."""
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 20]
        
        # Combine short paragraphs and create logical sections
        sections = []
        current_section = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would make section too long, start new section
            if current_section and len(current_section) + len(paragraph) > 800:
                sections.append(current_section.strip())
                current_section = paragraph
            else:
                current_section = current_section + " " + paragraph if current_section else paragraph
        
        # Add the last section
        if current_section:
            sections.append(current_section.strip())
        
        return sections
    
    def _generate_narrative_script(self, title: str, sections: List[str]) -> str:
        """Generate an engaging narrative script from content sections."""
        script_parts = []
        
        # Dynamic introduction based on content
        intro_options = [
            f"Welcome to another episode of our learning series! Today, we're diving deep into {title.lower()}.",
            f"Hey there, learners! Ready to explore {title.lower()}? Let's make this both fun and educational.",
            f"Welcome back! In today's session, we're going to unpack everything you need to know about {title.lower()}.",
        ]
        intro = intro_options[0] + " So grab your favorite beverage, get comfortable, and let's get started!"
        script_parts.append(intro)
        
        # Process each section with natural transitions
        transition_phrases = [
            "Let's start with the basics.",
            "Now, here's where it gets interesting.",
            "Building on that idea,",
            "Another key point to understand is",
            "What's really fascinating is",
            "Now you might be wondering,",
            "Here's the thing though,",
            "Let me break this down for you.",
        ]
        
        for i, section in enumerate(sections):
            # Add natural transition
            if i < len(transition_phrases):
                transition = transition_phrases[i]
            else:
                transition = "Moving forward,"
            
            # Convert section to conversational style
            conversational_section = self._make_conversational(section)
            
            # Combine transition with content
            full_section = f"{transition} {conversational_section}"
            script_parts.append(full_section)
            
            # Add natural pause between major sections
            if i < len(sections) - 1 and len(sections) > 2:
                script_parts.append("Let me pause here for a moment to let that sink in.")
        
        # Natural conclusion
        conclusion = f"So there you have it - a complete overview of {title.lower()}. "
        conclusion += "I hope this helped clarify things and gave you some practical insights you can use. "
        conclusion += "Thanks for joining me today, and I'll see you in the next episode!"
        script_parts.append(conclusion)
        
        return " ".join(script_parts)
    
    def _make_conversational(self, text: str) -> str:
        """Transform formal text into conversational podcast style."""
        # Split into sentences for better processing
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        conversational_sentences = []
        
        for i, sentence in enumerate(sentences):
            # Skip very short sentences
            if len(sentence) < 10:
                continue
                
            # Remove formal language and make conversational
            sentence = self._conversationalize_sentence(sentence)
            
            # Add natural connectors occasionally
            if i > 0 and len(conversational_sentences) > 0:
                connectors = ["", "", "", "You see,", "In other words,", "Think of it this way,", "Simply put,"]
                connector = connectors[i % len(connectors)]
                if connector:
                    sentence = f"{connector} {sentence.lower()}"
            
            conversational_sentences.append(sentence)
        
        return ". ".join(conversational_sentences) + "."
    
    def _conversationalize_sentence(self, sentence: str) -> str:
        """Convert a single sentence to conversational style."""
        # Replace formal/technical terms with conversational equivalents
        replacements = {
            r'\bIn order to\b': 'To',
            r'\bUtilize\b': 'use',
            r'\bFurthermore\b': 'Also',
            r'\bHowever\b': 'But',
            r'\bTherefore\b': 'So',
            r'\bSubsequently\b': 'Then',
            r'\bAdditionally\b': 'Plus',
            r'\bNevertheless\b': 'Still',
            r'\bMoreover\b': 'What\'s more',
            r'\bConsequently\b': 'As a result',
            r'\bIn conclusion\b': 'To wrap up',
            r'\bFor example\b': 'Like',
            r'\bSuch as\b': 'like',
            r'\bIn addition to\b': 'Along with',
            r'\bWith regard to\b': 'About',
            r'\bConcerning\b': 'About',
            r'\bIt is important to note that\b': 'Keep in mind that',
            r'\bIt should be noted that\b': 'Remember that',
            r'\bOne should\b': 'You should',
            r'\bOne can\b': 'You can',
            r'\bThis enables\b': 'This lets',
            r'\bThis allows\b': 'This lets',
        }
        
        for pattern, replacement in replacements.items():
            sentence = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)
        
        # Remove awkward technical phrasing
        sentence = re.sub(r'\bthat is to say\b', 'in other words', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bin other words,?\s*', 'basically, ', sentence, flags=re.IGNORECASE)
        
        # Make abbreviations more natural
        sentence = re.sub(r'\bAI\b', 'artificial intelligence', sentence)
        sentence = re.sub(r'\bAPI\b', 'A-P-I', sentence)
        sentence = re.sub(r'\bURL\b', 'U-R-L', sentence)
        sentence = re.sub(r'\bHTTP\b', 'H-T-T-P', sentence)
        
        # Remove redundant academic language
        sentence = re.sub(r'\bIt is evident that\b', '', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bIt is clear that\b', '', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bObviously,?\s*', '', sentence, flags=re.IGNORECASE)
        
        return sentence.strip()
    
    def _estimate_duration(self, word_count: int) -> str:
        """Estimate podcast duration based on word count."""
        # Average speaking rate is about 150-160 words per minute for podcasts
        minutes = word_count / 155
        
        if minutes < 1:
            return f"{int(minutes * 60)} seconds"
        elif minutes < 60:
            return f"{int(minutes)} minutes"
        else:
            hours = int(minutes // 60)
            remaining_minutes = int(minutes % 60)
            return f"{hours}h {remaining_minutes}m"
