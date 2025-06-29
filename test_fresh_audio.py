#!/usr/bin/env python3
"""
Test script to generate fresh audio from MS Learn content.
This will fetch content from the specified URL and generate a podcast-style audio file.
"""

import sys
import os
sys.path.insert(0, 'src')

from content.fetcher import MSLearnFetcher
from audio.ssmlFormatter import SSMLFormatter
from audio.multivoice_tts import MultiVoiceTTS
from utils.logger import setup_logger

def test_fresh_audio_generation():
    """Generate fresh audio from MS Learn URL"""
    
    # Setup logging
    logger = setup_logger()
    
    # Target URL
    url = "https://learn.microsoft.com/en-us/training/modules/explore-identity-azure-active-directory/14-explain-auditing-identity"
    
    print(f"🔄 Fetching content from: {url}")
    
    try:
        # Initialize components
        fetcher = MSLearnFetcher()
        formatter = SSMLFormatter()
        tts_service = MultiVoiceTTS()
        
        # Fetch content
        print("📥 Fetching MS Learn content...")
        content = fetcher.fetch_module_content(url)
        
        if not content:
            print("❌ Failed to fetch content from URL")
            return False
            
        print(f"✅ Content fetched successfully: {len(content.get('text', ''))} characters")
        
        # Format as SSML
        print("🎙️ Formatting content as podcast-style SSML...")
        ssml_content = formatter.format_as_podcast(
            title=content.get('title', 'Azure Active Directory Auditing'),
            content=content.get('text', ''),
            voice="en-US-AriaNeural"
        )
        
        print(f"✅ SSML formatted: {len(ssml_content)} characters")
        
        # Generate audio
        print("🔊 Generating audio...")
        output_path = "output/fresh_aad_auditing_podcast.wav"
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Generate the audio
        success = tts_service.synthesize_ssml(
            ssml_content=ssml_content,
            output_path=output_path
        )
        
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"🎉 Audio generated successfully!")
            print(f"📁 File: {output_path}")
            print(f"📊 Size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ Audio generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Fresh audio generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🎵 EdutainmentForge - Fresh Audio Generation Test")
    print("=" * 60)
    
    success = test_fresh_audio_generation()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("🎧 You can now listen to the generated audio file.")
    else:
        print("\n❌ Test failed!")
    
    print("=" * 60)
