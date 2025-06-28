"""
Content processing and script generation for podcasts.

Transforms technical content into engaging podcast scripts.
"""

import re
from typing import Dict, List, Tuple
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        
        # Normalize whitespace first to help with pattern matching
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r'[ \t]+', ' ', content)       # Multiple spaces to single
        content = content.strip()
        
        # Preserve and enhance headers for script structure with better hierarchy
        content = re.sub(r'^\s*#\s*Learning Content:\s*(.+?)$', r'LEARNING_PATH: \1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*##\s*LEARNING_UNIT\s*\d+:\s*(.+?)$', r'MODULE_UNIT: \1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*#{1,2}\s+(.+?)$', r'SECTION_HEADER: \1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*#{3,6}\s+(.+?)$', r'SUBSECTION: \1', content, flags=re.MULTILINE)
        
        # Preserve and transform emphasis formatting for script readability
        content = re.sub(r'\*\*(.*?)\*\*', r'EMPHASIS: \1', content)  # **bold** -> EMPHASIS:
        content = re.sub(r'\*(.*?)\*', r'HIGHLIGHT: \1', content)      # *italic* -> HIGHLIGHT:
        content = re.sub(r'`(.*?)`', r'TECHNICAL_TERM: \1', content)        # `code` -> TECHNICAL_TERM:
        content = re.sub(r'```.*?```', '[code example]', content, flags=re.DOTALL)  # code blocks
        
        # Clean up study guide formatting to be more script-friendly
        content = re.sub(r'\*\*([^:]+):\*\*\s*', r'STUDY_GUIDE_\1: ', content)  # **Learning Objectives:** -> STUDY_GUIDE_Learning Objectives:
        
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
        
        # Remove remaining markdown headers that weren't caught
        content = re.sub(r'^\s*#+\s*(.+?)$', r'SECTION_HEADER: \1', content, flags=re.MULTILINE)
        
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
        """Generate an engaging conversational script with two hosts."""
        script_parts = []
        
        # More natural introduction with better content preview
        intro = self._generate_dynamic_introduction(title, sections)
        script_parts.append(intro)
        
        # Generate natural conversational exchanges
        exchanges = self._generate_conversational_exchanges(sections)
        script_parts.extend(exchanges)
        
        # More natural conclusion with content recap
        conclusion = self._generate_dynamic_conclusion(title, sections)
        script_parts.append(conclusion)
        
        return "\n".join(script_parts)
    
    def _generate_dynamic_introduction(self, title: str, sections: List[str]) -> str:
        """Generate a streamlined introduction that quickly jumps into content."""
        # Extract key topics from the first section for preview
        preview_text = sections[0][:200] if sections else ""
        key_concepts = self._extract_key_concepts(preview_text)
        
        intro_lines = []
        
        # Streamlined intro - directly into the topic
        if any(term in title.lower() for term in ['azure', 'cloud', 'microsoft']):
            intro_lines.append(f"Sarah: Today we're diving into {title}.")
            intro_lines.append("Mike: Let's jump right in - this is going to be practical and useful.")
        elif any(term in title.lower() for term in ['ai', 'machine learning', 'artificial intelligence']):
            intro_lines.append(f"Sarah: We're exploring {title} today.")
            intro_lines.append("Mike: Perfect timing - AI is everywhere right now. Let's break this down.")
        else:
            intro_lines.append(f"Sarah: Today's topic is {title}.")
            intro_lines.append("Mike: Great choice - let's get into the details.")
        
        # Quick content preview if we have key concepts
        if key_concepts:
            intro_lines.append(f"Sarah: We'll cover {', '.join(key_concepts[:2])} and more.")
        
        return "\n".join(intro_lines)
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text for previewing content."""
        # Simple keyword extraction for preview
        concepts = []
        
        # Look for technical terms and important concepts
        patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper nouns
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b(?:Azure|Microsoft|cloud|AI|machine learning|deployment|security|data)\b',  # Key terms
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend([match.lower() for match in matches if len(match) > 3])
        
        # Remove duplicates and return up to 5 concepts
        return list(dict.fromkeys(concepts))[:5]
    
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
            
            # Handle emphasis markers for natural speech
            sentence = self._handle_emphasis_markers(sentence)
            
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
        
        # Make abbreviations more natural for speech
        sentence = re.sub(r'\bAI\b', 'A-I', sentence)
        sentence = re.sub(r'\bAPI\b', 'A-P-I', sentence)
        sentence = re.sub(r'\bURL\b', 'U-R-L', sentence)
        sentence = re.sub(r'\bHTTP\b', 'H-T-T-P', sentence)
        sentence = re.sub(r'\bHTTPS\b', 'H-T-T-P-S', sentence)
        sentence = re.sub(r'\bLLMs\b', 'Large Language Models', sentence)  # More natural
        sentence = re.sub(r'\bLLM\b', 'Large Language Model', sentence)
        sentence = re.sub(r'\bSLMs\b', 'Small Language Models', sentence)  # More natural
        sentence = re.sub(r'\bSLM\b', 'Small Language Model', sentence)
        sentence = re.sub(r'\bMLOps\b', 'M-L-Ops', sentence)
        sentence = re.sub(r'\bCI/CD\b', 'C-I-C-D', sentence)
        sentence = re.sub(r'\bJSON\b', 'J-S-O-N', sentence)
        sentence = re.sub(r'\bXML\b', 'X-M-L', sentence)
        sentence = re.sub(r'\bSQL\b', 'S-Q-L', sentence)
        sentence = re.sub(r'\bGUI\b', 'G-U-I', sentence)
        sentence = re.sub(r'\bCLI\b', 'C-L-I', sentence)
        sentence = re.sub(r'\bSDK\b', 'S-D-K', sentence)
        sentence = re.sub(r'\bIDE\b', 'I-D-E', sentence)
        sentence = re.sub(r'\bVM\b', 'Virtual Machine', sentence)
        sentence = re.sub(r'\bVMs\b', 'Virtual Machines', sentence)
        
        # Azure specific terms
        sentence = re.sub(r'\bAKS\b', 'Azure Kubernetes Service', sentence)
        sentence = re.sub(r'\bACR\b', 'Azure Container Registry', sentence)
        sentence = re.sub(r'\bACI\b', 'Azure Container Instances', sentence)
        sentence = re.sub(r'\bARM\b', 'Azure Resource Manager', sentence)
        sentence = re.sub(r'\bAAD\b', 'Azure Active Directory', sentence)
        sentence = re.sub(r'\bMSI\b', 'Managed Service Identity', sentence)
        
        # Remove redundant academic language
        sentence = re.sub(r'\bIt is evident that\b', '', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bIt is clear that\b', '', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bObviously,?\s*', '', sentence, flags=re.IGNORECASE)
        
        return sentence.strip()
    
    def _handle_emphasis_markers(self, sentence: str) -> str:
        """Convert emphasis markers to natural speech patterns."""
        # Handle learning hierarchy markers for structured flow
        sentence = re.sub(r'LEARNING_PATH:\s*(.+)', r'Welcome to our learning journey on \1.', sentence)
        sentence = re.sub(r'MODULE_UNIT:\s*(.+)', r'Now let\'s move to our next unit: \1.', sentence)
        sentence = re.sub(r'SECTION_HEADER:\s*(.+)', r'So let\'s talk about \1.', sentence)
        sentence = re.sub(r'SUBSECTION:\s*(.+)', r'Now, regarding \1,', sentence)
        
        # Handle study guide markers for teaching focus  
        sentence = re.sub(r'STUDY_GUIDE_Learning Objectives:\s*(.+)', r'Here\'s what you should focus on learning: \1', sentence)
        sentence = re.sub(r'STUDY_GUIDE_Key Points:\s*(.+)', r'The important things to remember are: \1', sentence)
        sentence = re.sub(r'STUDY_GUIDE_Study Questions:\s*(.+)', r'To test your understanding, think about: \1', sentence)
        
        # Handle emphasis markers with natural speech patterns
        sentence = re.sub(r'EMPHASIS:\s*(.+?)(?=\s|$|[,.!?])', r'and this is really important - \1', sentence)
        sentence = re.sub(r'HIGHLIGHT:\s*(.+?)(?=\s|$|[,.!?])', r'particularly \1', sentence)
        sentence = re.sub(r'TECHNICAL_TERM:\s*(.+?)(?=\s|$|[,.!?])', r'what we call "\1"', sentence)
        
        return sentence
    
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
    
    def _generate_conversational_exchanges(self, sections: List[str]) -> List[str]:
        """Generate more natural conversational exchanges between hosts."""
        exchanges = []
        
        # More varied and natural transitions
        conversation_starters = [
            ("Sarah", ["Mike, let's start with the fundamentals here.", 
                      "So Mike, what's the first thing people should know about this?",
                      "Mike, I'm curious about your take on this."]),
            ("Mike", ["That's a great question, Sarah. Here's what I think...",
                     "Sarah, you've hit on something really important there.",
                     "Let me break this down, Sarah, because it's actually pretty fascinating."]),
            ("Sarah", ["That makes sense! But I'm wondering about...",
                      "Interesting! Mike, what about when...",
                      "I see what you mean. Can you explain..."]),
            ("Mike", ["Good point, Sarah! That's exactly where it gets interesting.",
                     "Sarah, that's the perfect question to ask.",
                     "You know what, Sarah? That's something a lot of people wonder about."]),
            ("Sarah", ["This is really helpful, Mike. What else should our listeners know?",
                      "OK, that's clear. What's the next piece of the puzzle?",
                      "Got it! So what happens next?"]),
            ("Mike", ["Great question! Let me add to that...",
                     "Sarah, here's another angle to consider...",
                     "Building on that idea, Sarah..."]),
        ]
        
        # Generate more natural back-and-forth
        for i, section in enumerate(sections):
            if i < len(conversation_starters):
                speaker, starters = conversation_starters[i]
                starter = starters[i % len(starters)]
            else:
                speaker = "Sarah" if i % 2 == 0 else "Mike"
                starter = "Let me continue with that thought..." if i % 2 == 0 else "Building on that..."
            
            # Process the section content
            conversational_content = self._make_conversational(section)
            
            # Create the exchange
            exchange = f"{speaker}: {starter} {conversational_content}"
            exchanges.append(exchange)
            
            # Add natural responses between major sections
            if i < len(sections) - 1 and len(section) > 300:
                other_speaker = "Mike" if speaker == "Sarah" else "Sarah"
                responses = [
                    "That's really insightful!",
                    "I hadn't thought about it that way.",
                    "That's a great explanation!",
                    "This is making a lot of sense now.",
                    "Perfect! That really clarifies things.",
                    "Wow, that's actually pretty cool!"
                ]
                response = f"{other_speaker}: {responses[i % len(responses)]}"
                exchanges.append(response)
        
        return exchanges
    
    def _generate_dynamic_conclusion(self, title: str, sections: List[str]) -> str:
        """Generate a streamlined conclusion with clear takeaways."""
        # Extract main themes for recap
        key_themes = self._extract_main_themes(sections)
        
        conclusion_lines = []
        
        # Concise recap and takeaway
        if key_themes:
            conclusion_lines.append(f"Sarah: So we covered {', '.join(key_themes[:2])} - the key is understanding how these work together.")
            conclusion_lines.append("Mike: Exactly. Start with the basics and build from there.")
        else:
            conclusion_lines.append("Sarah: The main takeaway? Start experimenting with these concepts.")
            conclusion_lines.append("Mike: Right - practical experience is the best teacher.")
        
        # Clear transition signal
        conclusion_lines.append("Sarah: That's a wrap for today. Thanks for learning with us!")
        
        return "\n".join(conclusion_lines)
    
    def _extract_main_themes(self, sections: List[str]) -> List[str]:
        """Extract main themes from all sections for conclusion recap."""
        themes = []
        
        # Combine all sections and look for recurring important terms
        all_text = " ".join(sections).lower()
        
        # Look for key technical concepts that appear multiple times
        theme_patterns = [
            r'\b(?:security|authentication|authorization)\b',
            r'\b(?:deployment|hosting|scaling)\b',
            r'\b(?:data|database|storage)\b',
            r'\b(?:api|service|endpoint)\b',
            r'\b(?:cloud|azure|aws)\b',
            r'\b(?:monitoring|logging|debugging)\b',
            r'\b(?:configuration|setup|installation)\b',
            r'\b(?:performance|optimization|efficiency)\b',
        ]
        
        for pattern in theme_patterns:
            if re.search(pattern, all_text):
                # Extract the theme name
                match = re.search(pattern, all_text)
                if match:
                    themes.append(match.group())
        
        # Remove duplicates and return up to 3 main themes
        return list(dict.fromkeys(themes))[:3]
