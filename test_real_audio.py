#!/usr/bin/env python3
"""
Test script to generate real audio from MS Learn content.
This demonstrates the full pipeline workflow.
"""

import sys
import os
sys.path.insert(0, 'src')

from content.fetcher import MSLearnFetcher
from audio.speechGeneration import generate_speech
from utils.logger import setup_logger

def test_ms_learn_audio_generation():
    """Test the complete pipeline from MS Learn URL to audio."""
    
    # Setup logging
    logger = setup_logger("test_audio", "INFO")
    
    # Example MS Learn module URL - Introduction to AI
    test_url = "https://docs.microsoft.com/en-us/learn/modules/introduction-to-ai/"
    
    try:
        logger.info(f"Testing audio generation for: {test_url}")
        
        # Step 1: Fetch content from MS Learn
        logger.info("Step 1: Fetching content from MS Learn...")
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(test_url)
        
        if not content:
            logger.error("Failed to fetch content")
            return False
            
        logger.info(f"Fetched content: {content.get('title', 'Unknown')}")
        
        # Step 2: Format content as SSML
        logger.info("Step 2: Formatting content as SSML...")
        
        # Create a sample podcast-style script from the content
        script = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-AriaNeural">
                <prosody rate="medium" pitch="medium">
                    Welcome to EdutainmentForge! Today we're diving into an exciting topic from Microsoft Learn.
                </prosody>
                <break time="1s"/>
                
                <prosody rate="medium" pitch="+2st">
                    Our topic today is: {content.get('title', 'Introduction to AI')}
                </prosody>
                <break time="1s"/>
                
                <prosody rate="medium">
                    {content.get('description', 'Learn about artificial intelligence and its applications in modern technology.')}
                </prosody>
                <break time="2s"/>
                
                <prosody rate="slow" pitch="-1st">
                    This has been EdutainmentForge, making learning fun and engaging. 
                    Thanks for listening!
                </prosody>
            </voice>
        </speak>
        """
        
        # Step 3: Generate speech
        logger.info("Step 3: Generating speech audio...")
        audio = generate_speech(script, "en-US-AriaNeural")
        
        # Step 4: Save the audio
        output_file = "output/test_ms_learn_audio.wav"
        os.makedirs("output", exist_ok=True)
        
        logger.info(f"Step 4: Saving audio to {output_file}")
        audio.export(output_file, format="wav")
        
        logger.info(f"✓ Audio generation successful! File saved: {output_file}")
        logger.info(f"Audio duration: {len(audio) / 1000:.2f} seconds")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ms_learn_audio_generation()
    if success:
        print("\n🎵 Audio generation completed successfully!")
        print("You can now listen to: output/test_ms_learn_audio.wav")
    else:
        print("\n❌ Audio generation failed. Check the logs for details.")
        sys.exit(1)
