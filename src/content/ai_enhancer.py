"""
AI-powered script enhancement for creating more interactive podcast conversations.

Uses Azure OpenAI to transform monotonous content into engaging dialogue between hosts.
"""

import os
import json
import re
from typing import Dict, List, Optional
from openai import AzureOpenAI
from utils.config import load_config
from utils.logger import get_logger


logger = get_logger(__name__)


class ScriptEnhancementError(Exception):
    """Custom exception for script enhancement failures."""
    pass


class AIScriptEnhancer:
    """Enhances podcast scripts using Azure OpenAI to create more interactive dialogue."""
    
    def __init__(self):
        """Initialize the AI script enhancer with Azure OpenAI client."""
        self.config = load_config()
        self.client = self._initialize_openai_client()
    
    def _initialize_openai_client(self) -> Optional[AzureOpenAI]:
        """Initialize Azure OpenAI client."""
        try:
            endpoint = self.config.get("azure_openai_endpoint")
            api_key = self.config.get("azure_openai_api_key")
            api_version = self.config.get("azure_openai_api_version", "2024-02-01")
            
            if not endpoint or not api_key:
                logger.warning("Azure OpenAI credentials not configured - AI enhancement disabled")
                return None
            
            return AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            return None
    
    def enhance_script(self, original_script: str, content_topic: str) -> str:
        """
        Transform a monotonous script into an engaging interactive dialogue.
        
        Args:
            original_script: The original generated script
            content_topic: The main topic being discussed
            
        Returns:
            Enhanced script with balanced dialogue and interactions
        """
        if not self.client:
            logger.warning("Azure OpenAI client not available - returning original script")
            return original_script
            
        try:
            prompt = self._create_enhancement_prompt(original_script, content_topic)
            
            response = self.client.chat.completions.create(
                model=self.config.get("azure_openai_deployment", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            enhanced_script = response.choices[0].message.content
            
            # Post-process the enhanced script to ensure proper formatting
            cleaned_script = self._post_process_enhanced_script(enhanced_script)
            
            logger.info("Successfully enhanced script with AI")
            return cleaned_script
            
        except Exception as e:
            logger.error(f"Script enhancement failed: {e}")
            # Return original script if enhancement fails
            logger.warning("Returning original script due to enhancement failure")
            return original_script
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI assistant."""
        return """You are an expert podcast script writer who specializes in creating engaging, interactive educational content. Your job is to transform monotonous, one-sided content into dynamic conversations between two enthusiastic co-hosts: Sarah and Mike.

Key requirements:
1. BALANCE THE CONVERSATION: Both Sarah and Mike should contribute equally (roughly 50/50 split)
2. ADD NATURAL INTERACTIONS: Include interruptions, follow-up questions, "aha!" moments, and reactions
3. MAKE IT CONVERSATIONAL: Use natural speech patterns, not formal documentation language
4. BREAK DOWN COMPLEX TOPICS: Have the hosts explain things to each other and the audience
5. ADD ENTHUSIASM: Show genuine excitement about the technical concepts
6. USE REAL EXAMPLES: When discussing roles, permissions, etc., give concrete scenarios
7. CREATE TEACHING MOMENTS: Have one host explain to the other, then reverse roles

CRITICAL FORMAT REQUIREMENTS:
- ALWAYS use exactly this format: "Sarah:" or "Mike:" at the start of each line
- Each speaker should be on a separate line
- Never use asterisks (*) or markdown formatting
- Use plain text only
- Replace any technical symbols with words (e.g., "star" instead of "*")

Example format:
Sarah: Welcome to today's episode about Azure identity management!
Mike: Thanks Sarah! I'm really excited to dive into this topic.
Sarah: Great! So let's start with the basics.

Format guidelines:
- Keep the existing intro and outro structure
- Use "Sarah:" and "Mike:" speaker labels ONLY
- Include natural speech fillers and reactions
- Make technical concepts accessible and engaging
- Ensure smooth transitions between topics
- NO asterisks, NO markdown, NO special characters"""

    def _create_enhancement_prompt(self, original_script: str, content_topic: str) -> str:
        """Create the enhancement prompt for the AI."""
        return f"""Please transform this podcast script about "{content_topic}" into a much more interactive and engaging conversation. The current script has Sarah doing almost all the talking, which makes it boring and monotonous.

CRITICAL FORMAT REQUIREMENTS:
- Start each speaker's dialogue with "Sarah:" or "Mike:" exactly
- Put each speaker on a separate line
- NO asterisks (*) - replace with "star" or appropriate words
- NO markdown formatting - plain text only
- NO special characters that could be read as "asterisk"

CURRENT PROBLEMS TO FIX:
- Sarah dominates the conversation (90% of speaking time)
- Very little back-and-forth interaction
- Sounds like reading documentation, not having a conversation
- Missing enthusiasm and natural reactions
- No follow-up questions or clarifications

WHAT I WANT:
- Balanced conversation where both hosts contribute equally
- Natural interruptions and reactions ("Wait, that's interesting!" "Hold on, let me make sure I understand this...")
- More enthusiastic and conversational tone
- Hosts teaching each other and the audience
- Breaking down complex concepts with examples
- Natural transitions and better flow

EXAMPLE OF CORRECT FORMAT:
Sarah: Welcome everyone to today's episode!
Mike: Thanks Sarah! I'm excited to explore this topic with you.
Sarah: Perfect! So let's dive right in.

ORIGINAL SCRIPT:
{original_script}

Please rewrite this as an engaging, interactive conversation between Sarah and Mike. Use the exact format shown above - each speaker on their own line with "Sarah:" or "Mike:" at the beginning. Keep the same factual content but make it much more dynamic and balanced."""

    def enhance_table_discussion(self, table_content: str, context: str) -> str:
        """
        Specifically enhance table discussions to be more interactive.
        
        Args:
            table_content: The extracted table content
            context: Surrounding context about the table
            
        Returns:
            Enhanced dialogue about the table content
        """
        if not self.client:
            return f"Sarah: Let's go through this table together.\nMike: Great idea! {table_content}"
            
        try:
            prompt = f"""Create an engaging dialogue between Sarah and Mike discussing this table content. Make them excited about exploring the details and comparing different options.

TABLE CONTENT: {table_content}
CONTEXT: {context}

Make the hosts:
1. Point out interesting differences and similarities
2. Ask each other clarifying questions
3. Give practical examples of when you'd use each option
4. React with genuine interest ("Oh wow, I didn't realize that!")
5. Break down complex permissions into understandable terms

Format as natural conversation with both hosts contributing equally."""

            response = self.client.chat.completions.create(
                model=self.config.get("azure_openai_deployment", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Table discussion enhancement failed: {e}")
            return f"Sarah: Let's go through this table together.\nMike: Great idea! {table_content}"
    
    def _post_process_enhanced_script(self, enhanced_script: str) -> str:
        """
        Post-process the enhanced script to ensure proper formatting and clean text.
        
        Args:
            enhanced_script: The raw enhanced script from AI
            
        Returns:
            Cleaned and properly formatted script
        """
        lines = enhanced_script.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove markdown formatting
            line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)  # Bold
            line = re.sub(r'\*([^*]+)\*', r'\1', line)      # Italic
            line = re.sub(r'`([^`]+)`', r'\1', line)        # Code
            
            # Replace asterisks with words to prevent TTS saying "asterisk"
            line = line.replace('*', ' star ')
            line = line.replace('•', ' bullet point ')
            line = line.replace('–', ' dash ')
            line = line.replace('—', ' dash ')
            
            # Clean up extra spaces
            line = re.sub(r'\s+', ' ', line).strip()
            
            # Ensure proper speaker format
            if line.startswith(('Sarah:', 'Mike:')):
                processed_lines.append(line)
            elif processed_lines and not line.startswith(('Sarah:', 'Mike:')):
                # Continue previous speaker's line
                processed_lines[-1] += ' ' + line
            else:
                # Fallback - add as Sarah if no speaker detected
                processed_lines.append(f"Sarah: {line}")
        
        return '\n'.join(processed_lines)
