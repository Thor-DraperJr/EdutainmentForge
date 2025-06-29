#!/usr/bin/env python3
"""
Debug script to test script parsing and AI enhancement.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from content.ai_enhancer import AIScriptEnhancer
from audio.multivoice_tts import MultiVoiceTTSService
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def test_script_parsing():
    """Test the script parsing functionality."""
    
    # Sample script with clear dialogue format
    test_script = """Sarah: Welcome to today's episode about Azure identity management!

Mike: Thanks Sarah! I'm really excited to dive into this topic. So what exactly are we covering today?

Sarah: Great question Mike! We're going to explore how Microsoft Entra ID, formerly known as Azure Active Directory, helps organizations manage user identities and access to resources.

Mike: That sounds really important for security. Can you explain what makes it different from traditional on-premises Active Directory?

Sarah: Absolutely! Unlike traditional AD which runs on your company's servers, Microsoft Entra ID is a cloud-based service. This means it can handle modern authentication scenarios like mobile apps, web applications, and multi-cloud environments.

Mike: Wow, that's fascinating! So it's basically designed for our modern, connected world where people work from anywhere and use all kinds of devices?

Sarah: Exactly right Mike! And one of the coolest features is multi-factor authentication, which adds an extra layer of security beyond just passwords."""

    print("Testing script parsing...")
    print("Original script:")
    print("-" * 50)
    print(test_script)
    print("-" * 50)
    
    # Test parsing
    config = get_config()
    tts_service = MultiVoiceTTSService(config)
    
    segments = tts_service._parse_dialogue_script(test_script)
    
    print(f"\nParsed {len(segments)} segments:")
    for i, (speaker, text) in enumerate(segments):
        print(f"{i+1}. {speaker}: {text[:100]}{'...' if len(text) > 100 else ''}")

def test_ai_enhancement():
    """Test the AI enhancement functionality."""
    
    print("\n" + "="*60)
    print("Testing AI Enhancement")
    print("="*60)
    
    # Simple original script
    original_script = """Sarah: Welcome to our podcast about Microsoft Entra Business to Business.

Sarah: Microsoft Entra Business to Business, or B2B, allows organizations to securely share their applications and services with guest users from other organizations. This enables collaboration while maintaining security and control over organizational resources.

Sarah: Key features include guest user invitations, conditional access policies, and cross-tenant access settings. Organizations can invite external users and grant them specific permissions without requiring them to create new accounts.

Sarah: Thank you for listening to today's episode about Microsoft Entra B2B."""

    print("Original script:")
    print("-" * 50)
    print(original_script)
    print("-" * 50)
    
    # Initialize AI enhancer
    config = get_config()
    if not config.get('azure_openai_api_key'):
        print("No OpenAI API key found, skipping AI enhancement test")
        return
    
    enhancer = AIScriptEnhancer(config)
    
    try:
        enhanced_script = enhancer.enhance_script(
            original_script=original_script,
            content_topic="Microsoft Entra Business to Business"
        )
        
        print("\nEnhanced script:")
        print("-" * 50)
        print(enhanced_script)
        print("-" * 50)
        
        # Test parsing the enhanced script
        tts_service = MultiVoiceTTSService(config)
        segments = tts_service._parse_dialogue_script(enhanced_script)
        
        print(f"\nParsed enhanced script into {len(segments)} segments:")
        for i, (speaker, text) in enumerate(segments):
            print(f"{i+1}. {speaker}: {text[:100]}{'...' if len(text) > 100 else ''}")
            
    except Exception as e:
        print(f"AI enhancement failed: {e}")

if __name__ == '__main__':
    test_script_parsing()
    test_ai_enhancement()
