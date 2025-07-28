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
from utils.premium_integration import get_best_ai_enhancer, is_premium_available

logger = get_logger(__name__)


class ScriptProcessor:
    """Processes content and generates podcast scripts."""
    
    def __init__(self, use_ai_enhancement: bool = True):
        """Initialize the script processor."""
        self.use_ai_enhancement = use_ai_enhancement
        self.ai_enhancer = None
        
        if self.use_ai_enhancement:
            try:
                self.ai_enhancer = get_best_ai_enhancer()
                if self.ai_enhancer:
                    enhancement_type = "Premium (GPT-4)" if is_premium_available('ai_enhancement') else "Standard (GPT-4o-mini)"
                    logger.info(f"AI script enhancement enabled: {enhancement_type}")
                else:
                    logger.warning("AI enhancement disabled: No AI service available")
                    self.use_ai_enhancement = False
            except Exception as e:
                logger.warning(f"AI enhancement disabled: {e}")
                self.use_ai_enhancement = False
        
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
            'source_url': content.get('url', 'Direct Content')
        }
    
    def _clean_content(self, content: str) -> str:
        """Clean and prepare content for script generation."""
        # Remove time/duration indicators
        content = re.sub(r'\b\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bcompleted\s+\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\bestimated\s+time:?\s*\d+\s+minutes?\b', '', content, flags=re.IGNORECASE)
        
        # Remove markdown headers (# ## ###)
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        
        # Detect and preserve table structures before other processing
        content = self._preserve_table_structures(content)
        
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
        
        # Remove common technical artifacts (but preserve table markers)
        content = re.sub(r'[{}[\]()<>]', '', content)   # Brackets and braces
        
        # Remove standalone colons that don't make sense in speech
        content = re.sub(r'\s*:\s*$', '.', content, flags=re.MULTILINE)
        
        return content.strip()

    def _preserve_table_structures(self, content: str) -> str:
        """Detect and convert tables into conversational explanations."""
        # First, look for specific Microsoft Learn table patterns
        content = self._handle_microsoft_learn_tables(content)
        
        # Then look for generic table patterns
        lines = content.split('\n')
        table_sections = []
        current_table = []
        in_table = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect table start - line with multiple pipes or consistent separators
            if self._is_table_header_or_separator(line):
                if not in_table:
                    in_table = True
                    current_table = []
                continue
            
            # If we're in a table and find a data row
            elif in_table and self._is_table_row(line):
                current_table.append(line)
            
            # End of table - empty line or non-table content
            elif in_table:
                if current_table:
                    table_explanation = self._convert_table_to_explanation(current_table)
                    table_sections.append((i - len(current_table), table_explanation))
                in_table = False
                current_table = []
        
        # Handle table at end of content
        if in_table and current_table:
            table_explanation = self._convert_table_to_explanation(current_table)
            table_sections.append((len(lines) - len(current_table), table_explanation))
        
        # Replace tables in reverse order to maintain line numbers
        for start_line, explanation in reversed(table_sections):
            # Find the original table bounds
            table_start = start_line
            table_end = start_line
            
            # Find where the table actually ends
            for j in range(start_line, len(lines)):
                if self._is_table_row(lines[j].strip()) or self._is_table_header_or_separator(lines[j].strip()):
                    table_end = j + 1
                else:
                    break
            
            # Replace the table lines with the explanation
            lines[table_start:table_end] = [explanation]
        
        return '\n'.join(lines)

    def _handle_microsoft_learn_tables(self, content: str) -> str:
        """Handle Microsoft Learn specific table patterns."""
        # Pattern 1: Role table with Global Administrator, User Administrator, etc.
        # More flexible pattern that looks for role descriptions
        roles_pattern = r'(Global Administrator[^\.]*?Manage access to all administrative features[^\.]*?User Administrator[^\.]*?Billing Administrator[^\.]*?)'
        
        def replace_roles_table(match):
            table_text = match.group(1)
            
            # Create engaging role explanations
            role_explanations = []
            
            role_explanations.append("Let me break down these essential Microsoft Entra roles that you'll encounter most often:")
            
            role_explanations.append("First up is the Global Administrator role - and wow, this one is powerful! The Global Administrator has manage access to all administrative features in Microsoft Entra ID and any services that connect to it. Here's something interesting: whoever signs up for the Microsoft Entra tenant automatically becomes the first Global Administrator. They can assign administrator roles to other people and even reset passwords for any user, including other administrators.")
            
            role_explanations.append("Next, we have the User Administrator role, which is really practical for everyday operations. This role is perfect for managing day-to-day user needs - you can create and manage all aspects of users and groups, handle support tickets, monitor service health, and change passwords for regular users, helpdesk administrators, and other user administrators.")
            
            role_explanations.append("Finally, there's the Billing Administrator role, which focuses on the financial side of things. This role lets you make purchases, manage subscriptions, handle support tickets, and monitor service health - basically everything related to costs and billing.")
            
            return " ".join(role_explanations)
        
        content = re.sub(roles_pattern, replace_roles_table, content, flags=re.DOTALL | re.IGNORECASE)
        
        # Alternative pattern for roles - look for key phrases
        alt_roles_pattern = r'(following table describes a few of the more important microsoft entra roles.*?(?:Global Administrator|User Administrator|Billing Administrator).*?(?:In the Azure portal|Differences between))'
        
        def replace_alt_roles_table(match):
            role_explanations = []
            role_explanations.append("Here are the key Microsoft Entra roles you need to understand:")
            
            role_explanations.append("The Global Administrator role is the most powerful - it can manage access to all administrative features in Microsoft Entra ID and connected services. The person who creates the tenant becomes the first Global Administrator, and they can assign roles to others and reset any user's password.")
            
            role_explanations.append("The User Administrator role handles day-to-day user management - creating and managing users and groups, handling support tickets, monitoring service health, and changing passwords for most users.")
            
            role_explanations.append("The Billing Administrator role focuses on financial operations - making purchases, managing subscriptions, handling billing-related support tickets, and monitoring service health.")
            
            return " ".join(role_explanations)
        
        content = re.sub(alt_roles_pattern, replace_alt_roles_table, content, flags=re.DOTALL | re.IGNORECASE)
        
        # Pattern 2: Azure vs Entra roles comparison table
        comparison_pattern = r'(Azure roles.*?Microsoft Entra roles.*?Manage access to Azure resources.*?Manage access to Microsoft Entra resources.*?)(?=Do Azure roles|$)'
        
        def replace_comparison_table(match):
            return "Let me break down the key differences between Azure roles and Microsoft Entra roles: Azure roles manage access to Azure resources like virtual machines and storage accounts, while Microsoft Entra roles manage access to Microsoft Entra resources like users and groups. Both support custom roles, but they have different scopes - Azure roles can be applied at multiple levels like management groups, subscriptions, and resource groups, while Microsoft Entra roles are typically at the tenant level. You can access Azure role information through the Azure portal, CLI, PowerShell, and REST APIs, while Microsoft Entra role information is available through the Azure admin portal, Microsoft 365 admin center, and Microsoft Graph."
        
        content = re.sub(comparison_pattern, replace_comparison_table, content, flags=re.DOTALL | re.IGNORECASE)
        
        return content

    def _is_table_header_or_separator(self, line: str) -> bool:
        """Check if a line looks like a table header or separator."""
        if not line:
            return False
        
        # Common table separator patterns
        separator_patterns = [
            r'^[\s\-\|:]+$',  # Lines with dashes, pipes, colons
            r'^\|[\s\-\|:]+\|$',  # Markdown table separators
        ]
        
        for pattern in separator_patterns:
            if re.match(pattern, line):
                return True
        
        # Header pattern - line with multiple words separated by pipes or tabs
        if '|' in line or '\t' in line:
            parts = re.split(r'[\|\t]', line)
            if len(parts) >= 2 and sum(1 for p in parts if p.strip()) >= 2:
                return True
        
        return False

    def _is_table_row(self, line: str) -> bool:
        """Check if a line looks like a table data row."""
        if not line:
            return False
        
        # Look for patterns that suggest tabular data
        if '|' in line or '\t' in line:
            parts = re.split(r'[\|\t]', line)
            # Must have at least 2 columns with content
            content_parts = [p.strip() for p in parts if p.strip()]
            return len(content_parts) >= 2
        
        return False

    def _convert_table_to_explanation(self, table_rows: List[str]) -> str:
        """Convert table rows into conversational explanation."""
        if not table_rows:
            return ""
        
        # Parse the table structure
        parsed_rows = []
        for row in table_rows:
            if '|' in row:
                columns = [col.strip() for col in row.split('|') if col.strip()]
            elif '\t' in row:
                columns = [col.strip() for col in row.split('\t') if col.strip()]
            else:
                continue
            
            if columns:
                parsed_rows.append(columns)
        
        if not parsed_rows:
            return ""
        
        # Generate conversational explanation
        explanations = []
        
        # Try to identify if this looks like a roles/permissions table
        first_row = parsed_rows[0]
        looks_like_roles = any(keyword in str(first_row).lower() for keyword in 
                             ['role', 'permission', 'access', 'admin', 'user', 'manage'])
        
        if looks_like_roles:
            explanations.append("Let me break down these important roles for you:")
            
            for i, row in enumerate(parsed_rows):
                if len(row) >= 2:
                    role_name = row[0]
                    description = row[1] if len(row) > 1 else ""
                    additional_info = " ".join(row[2:]) if len(row) > 2 else ""
                    
                    if role_name and description:
                        explanation = f"The {role_name} role is really important - {description}"
                        if additional_info:
                            explanation += f" {additional_info}"
                        explanations.append(explanation)
        else:
            # Generic table explanation
            explanations.append("Here are the key details from this comparison:")
            
            for row in parsed_rows:
                if len(row) >= 2:
                    explanations.append(f"For {row[0]}: {' '.join(row[1:])}")
        
        return " ".join(explanations)
    
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
        
        # Combine all parts into initial script
        initial_script = "\n".join(script_parts)
        
        # Enhance with AI if available
        if self.use_ai_enhancement and self.ai_enhancer:
            try:
                logger.info("Enhancing script with AI for better dialogue balance")
                enhanced_script = self.ai_enhancer.enhance_script(initial_script, title)
                return enhanced_script
            except Exception as e:
                logger.warning(f"AI enhancement failed, using original script: {e}")
                return initial_script
        
        return initial_script
    
    def _generate_dynamic_introduction(self, title: str, sections: List[str]) -> str:
        """Generate no introduction - jump straight into content."""
        # Return empty string to skip introductions entirely
        # Mike and Sarah are assumed to be already introduced
        return ""
    
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
        
        # Special conversation starters for structured content like tables/lists
        table_starters = [
            ("Sarah", ["Mike, I think this is where it gets really practical. Let's break down these different options."]),
            ("Mike", ["Absolutely, Sarah! These distinctions are super important to understand."]),
            ("Sarah", ["This is exactly the kind of detail that helps people make the right decisions!"]),
            ("Mike", ["You're right, Sarah. Let me walk through each of these because they all serve different purposes."]),
        ]
        
        # Generate more natural back-and-forth
        for i, section in enumerate(sections):
            # Detect if this section has structured content (tables, roles, etc.)
            has_structured_content = self._has_structured_content(section)
            
            if has_structured_content and i < len(table_starters):
                speaker, starters = table_starters[i]
                starter = starters[0]
            elif i < len(conversation_starters):
                speaker, starters = conversation_starters[i]
                starter = starters[i % len(starters)]
            else:
                speaker = "Sarah" if i % 2 == 0 else "Mike"
                if has_structured_content:
                    starter = "Now this is where it gets interesting..." if i % 2 == 0 else "Let me break this down for you..."
                else:
                    starter = "Let me continue with that thought..." if i % 2 == 0 else "Building on that..."
            
            # Process the section content
            conversational_content = self._make_conversational(section)
            
            # Create the exchange
            exchange = f"{speaker}: {starter} {conversational_content}"
            exchanges.append(exchange)
            
            # Add natural responses between major sections, especially for structured content
            if i < len(sections) - 1 and len(section) > 300:
                other_speaker = "Mike" if speaker == "Sarah" else "Sarah"
                
                if has_structured_content:
                    responses = [
                        "Wow, that breakdown really helps clarify the differences!",
                        "That's such a useful way to think about it!",
                        "Perfect! Those distinctions are so important.",
                        "I love how you explained each role - that makes it so much clearer!",
                        "Those examples really bring it to life!",
                        "That's exactly what people need to know!"
                    ]
                else:
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

    def _has_structured_content(self, section: str) -> bool:
        """Check if a section contains structured content like tables or role descriptions."""
        indicators = [
            "role is really important",  # Our table conversion marker
            "let me break down these",   # Our table conversion marker
            "here are the key details",  # Our table conversion marker
            ": ",  # Multiple colons suggest definitions/descriptions
            "permissions",
            "administrator",
            "manage",
            "access to"
        ]
        
        section_lower = section.lower()
        # Check for multiple indicators of structured content
        indicator_count = sum(1 for indicator in indicators if indicator in section_lower)
        
        return indicator_count >= 2 or "role is really important" in section_lower
    
    def _generate_dynamic_conclusion(self, title: str, sections: List[str]) -> str:
        """Generate a minimal conclusion without fluff."""
        # Very brief wrap-up focused on key takeaways
        key_themes = self._extract_main_themes(sections)
        
        conclusion_lines = []
        
        # Quick summary if we have themes
        if key_themes and len(key_themes) > 0:
            conclusion_lines.append(f"Sarah: So the key points are {', '.join(key_themes[:2])}.")
            conclusion_lines.append("Mike: Exactly. That's the foundation you need to get started.")
        else:
            conclusion_lines.append("Sarah: Those are the essential concepts to remember.")
            conclusion_lines.append("Mike: Perfect. Now you can put this into practice.")
        
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
