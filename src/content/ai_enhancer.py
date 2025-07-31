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
    
    def _get_best_model(self, content: str = "", content_complexity: str = "medium") -> str:
        """Select the best AI model based on content complexity and availability."""
        # Analyze content complexity if content is provided
        if content:
            content_complexity = self._analyze_content_complexity(content)
        
        # Check for GPT-4 availability
        gpt4_deployment = self.config.get("azure_openai_gpt4_deployment", "gpt-4o")
        default_model = self.config.get("azure_openai_deployment_name", "gpt-4o-mini")
        
        # Use GPT-4 for complex content (tables, technical concepts)
        if content_complexity in ["high", "complex", "tables", "technical"]:
            logger.info(f"Using {gpt4_deployment} for {content_complexity} content")
            return gpt4_deployment
        
        # Use cost-effective model for simple content
        logger.info(f"Using {default_model} for {content_complexity} content")
        return default_model
    
    def _analyze_content_complexity(self, content: str) -> str:
        """Analyze content to determine complexity level for smart model selection."""
        content_lower = content.lower()
        
        # Check for table content
        table_indicators = ["table", "column", "row", "|", "data", "results", "comparison"]
        if any(indicator in content_lower for indicator in table_indicators):
            return "tables"
        
        # Check for complex technical content
        complex_patterns = [
            "architecture", "implementation", "deployment", "configuration",
            "authentication", "authorization", "encryption", "protocol",
            "algorithm", "framework", "infrastructure", "integration"
        ]
        if any(pattern in content_lower for pattern in complex_patterns):
            return "technical"
        
        # Check for complexity indicators
        complexity_indicators = [
            "advanced", "complex", "detailed", "comprehensive", "in-depth",
            "troubleshooting", "optimization", "performance", "security"
        ]
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in content_lower)
        
        if complexity_score >= 3:
            return "complex"
        
        return "simple"
    
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
            # Smart model selection based on content complexity
            selected_model = self._get_best_model(original_script + " " + content_topic)
            
            prompt = self._create_enhancement_prompt(original_script, content_topic)
            
            response = self.client.chat.completions.create(
                model=selected_model,
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
8. MINIMIZE NAME USAGE: Use names sparingly to avoid long pauses - focus on natural conversation flow

CRITICAL FORMAT REQUIREMENTS:
- ALWAYS use exactly this format: "Sarah:" or "Mike:" at the start of each line
- Each speaker should be on a separate line
- Never use asterisks (*) or markdown formatting
- Use plain text only
- Replace any technical symbols with words (e.g., "star" instead of "*")
- Keep dashes as regular hyphens (-) for natural speech pauses

Example format showing minimal name usage:
Sarah: Welcome to today's episode about Azure identity management!
Mike: Thanks! I'm really excited to dive into this topic.
Sarah: Great! So let's start with the basics.
Mike: Absolutely. The first thing to understand is...

Format guidelines:
- Keep the existing intro and outro structure
- Use "Sarah:" and "Mike:" speaker labels ONLY
- Include natural speech fillers and reactions
- Make technical concepts accessible and engaging
- Ensure smooth transitions between topics
- NO asterisks, NO markdown, NO special characters
- Use names only when necessary for clarity, not as conversational fillers"""

    def _create_enhancement_prompt(self, original_script: str, content_topic: str) -> str:
        """Create the enhancement prompt for the AI."""
        return f"""Transform this podcast script about "{content_topic}" into a focused conversation that IMMEDIATELY dives into the core material. Skip lengthy introductions and get straight to the technical content.

CRITICAL FORMAT REQUIREMENTS:
- Start each speaker's dialogue with "Sarah:" or "Mike:" exactly
- Put each speaker on a separate line
- NO asterisks (*) - replace with "star" or appropriate words
- NO markdown formatting - plain text only

STRUCTURE REQUIREMENTS:
1. Mike starts with a direct, specific question about the main topic (no general introductions)
2. Sarah provides the core answer with key details
3. Mike follows up with deeper technical questions
4. Keep content dense and focused - every line should teach something important
5. Balance speaking time 50/50 between Sarah and Mike

EXAMPLE OPENING (for Azure topic):
Mike: Sarah, let's talk about Azure Active Directory authentication. What's the fundamental difference between authentication and authorization?
Sarah: Great question Mike! Authentication is proving who you are, while authorization determines what you can access...

AVOID:
- General welcomes or introductions
- "Today we're going to explore..." style openings
- Level-setting about what Azure is
- Background explanations users already know

ORIGINAL SCRIPT:
{original_script}

Rewrite this as a focused, technical conversation between Sarah and Mike. Mike should immediately ask specific questions about the core concepts, and both hosts should dive straight into the material without preliminaries."""

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
            prompt = f"""Create an engaging dialogue between Sarah and Mike discussing this table content. They should analyze the MEANING and PURPOSE of the table, not just read it row by row.

TABLE CONTENT: {table_content}
CONTEXT: {context}

CRITICAL INSTRUCTIONS:
1. **Understand the table's PURPOSE** - What is it trying to demonstrate or teach? What's the core concept?
2. **Explain the RELATIONSHIPS** between columns - How do they work together? What's the logic?
3. **Identify KEY PATTERNS** - What's the main takeaway or principle being illustrated?
4. **Use REAL-WORLD EXAMPLES** - How would this apply in practice? Give concrete scenarios.
5. **Highlight CRITICAL DIFFERENCES** - What makes each row/option unique and important?
6. **Connect to BIGGER PICTURE** - How does this table relate to the overall topic?

EXAMPLE OF GOOD TABLE DISCUSSION:
Instead of: "Sarah: The first row says Verify Explicitly means Always validate all data points."
Write: "Sarah: So when they say 'Verify Explicitly', they're really challenging the old mindset of 'trust but verify.' Mike: Exactly! It's saying we can't just trust that someone is who they say they are because they have the right username. Sarah: Right! We need to check their device health, location, even the time of day they're logging in. Mike: It's like being a detective - you gather evidence from multiple sources before making a decision."

The hosts should sound like they truly understand the subject matter and are excited to help the listener understand it too. They should:
- Break down complex concepts into simple, relatable terms
- Connect ideas to practical scenarios people can relate to
- Show genuine enthusiasm for the learning
- Ask thoughtful follow-up questions that clarify important points
- Anticipate listener confusion and explain things multiple ways
- Use analogies and metaphors to make concepts stick
- Debate or discuss nuances to show depth of understanding
- Use names sparingly - focus on natural conversation flow instead of constantly saying each other's names

Format as natural conversation with both hosts contributing equally. Make it sound like two experts having an genuine discussion, not reading from a script."""
            
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
            
            # Replace problematic characters with TTS-friendly alternatives
            line = line.replace('*', ' star ')
            line = line.replace('•', ' bullet point ')
            # Convert em-dashes and en-dashes to regular hyphens (for natural speech pauses)
            line = line.replace('–', '-')
            line = line.replace('—', '-')
            
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
