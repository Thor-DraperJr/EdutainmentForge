#!/usr/bin/env python3
"""
Test script to generate and play audio using the speechGeneration module.
"""

import sys
import os
sys.path.insert(0, 'src')

from audio.speechGeneration import generate_speech
from pydub import AudioSegment
from pydub.playback import play

def test_audio_generation():
    """Test actual audio generation with real TTS service."""
    
    # Test SSML content
    test_ssml = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="en-US-AriaNeural">
            <prosody rate="medium" pitch="medium">
                Hello! This is a test of the EdutainmentForge speech generation system.
                I'm testing the audio quality and voice naturalness.
            </prosody>
        </voice>
    </speak>
    """
    
    print("🎤 Testing speech generation...")
    print(f"SSML content: {test_ssml[:100]}...")
    
    try:
        # Generate audio
        audio = generate_speech(test_ssml, "en-US-AriaNeural")
        
        # Save to output directory
        output_file = "output/test_speech_generation.wav"
        os.makedirs("output", exist_ok=True)
        audio.export(output_file, format="wav")
        
        print(f"✅ Audio generated successfully!")
        print(f"📁 Saved to: {output_file}")
        print(f"⏱️  Duration: {len(audio) / 1000:.2f} seconds")
        print(f"🔊 Sample rate: {audio.frame_rate} Hz")
        
        # Try to play the audio (if system supports it)
        try:
            print("🔊 Playing audio...")
            play(audio)
        except Exception as e:
            print(f"⚠️  Could not play audio automatically: {e}")
            print(f"   You can manually play: {output_file}")
            
        return True
        
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 EdutainmentForge Audio Generation Test")
    print("=" * 50)
    
    success = test_audio_generation()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
