#!/usr/bin/env python3
"""
Simple test script to generate audio with sample content.
This demonstrates the audio generation without network dependencies.
"""

import sys
import os
sys.path.insert(0, 'src')

from audio.speechGeneration import generate_speech
from utils.logger import setup_logger

def test_sample_audio_generation():
    """Test audio generation with sample educational content."""
    
    # Setup logging
    logger = setup_logger("test_audio", "INFO")
    
    try:
        logger.info("Testing audio generation with sample content...")
        
        # Create a sample podcast-style script
        script = """
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-AriaNeural">
                <prosody rate="medium" pitch="medium">
                    Welcome to EdutainmentForge! Today we're exploring the fascinating world of Artificial Intelligence.
                </prosody>
                <break time="1s"/>
                
                <prosody rate="medium" pitch="+2st">
                    What exactly is Artificial Intelligence?
                </prosody>
                <break time="500ms"/>
                
                <prosody rate="medium">
                    Simply put, AI is the simulation of human intelligence in machines. 
                    These machines are programmed to think like humans and mimic their actions.
                </prosody>
                <break time="1s"/>
                
                <prosody rate="slow">
                    AI can be categorized into different types: Machine Learning, Deep Learning, 
                    and Natural Language Processing are just a few examples.
                </prosody>
                <break time="1s"/>
                
                <prosody rate="medium" pitch="+1st">
                    Machine Learning allows computers to learn without being explicitly programmed.
                    It's like teaching a computer to recognize patterns and make decisions!
                </prosody>
                <break time="2s"/>
                
                <prosody rate="slow" pitch="-1st">
                    This has been EdutainmentForge, making learning fun and engaging. 
                    Thanks for listening to our AI introduction!
                </prosody>
            </voice>
        </speak>
        """
        
        logger.info("Generating speech audio...")
        audio = generate_speech(script, "en-US-AriaNeural")
        
        # Save the audio
        output_file = "output/sample_ai_podcast.wav"
        os.makedirs("output", exist_ok=True)
        
        logger.info(f"Saving audio to {output_file}")
        audio.export(output_file, format="wav")
        
        logger.info(f"✓ Audio generation successful! File saved: {output_file}")
        logger.info(f"Audio duration: {len(audio) / 1000:.2f} seconds")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sample_audio_generation()
    if success:
        print("\n🎵 Audio generation completed successfully!")
        print("You can now listen to: output/sample_ai_podcast.wav")
        print("This demonstrates the EdutainmentForge podcast-style audio generation!")
    else:
        print("\n❌ Audio generation failed. Check the logs for details.")
        sys.exit(1)
