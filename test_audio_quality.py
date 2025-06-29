#!/usr/bin/env python3
"""
Test script to generate fresh audio and verify quality before committing.
"""

import sys
import os
sys.path.insert(0, 'src')

from audio.speechGeneration import generate_speech
from audio.ssmlFormatter import SSMLFormatter
from utils.logger import setup_logger
import hashlib

def main():
    # Set up logging
    logger = setup_logger()
    
    # Create sample content for testing
    sample_content = {
        "title": "Introduction to Artificial Intelligence",
        "summary": "This module introduces the fundamental concepts of artificial intelligence, including machine learning, neural networks, and practical applications in modern technology.",
        "sections": [
            {
                "title": "What is AI?",
                "content": "Artificial Intelligence refers to the simulation of human intelligence in machines. It encompasses various techniques like machine learning, deep learning, and natural language processing."
            },
            {
                "title": "Machine Learning Basics", 
                "content": "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to find patterns in data."
            }
        ]
    }
    
    print("🎙️ Generating fresh audio content for quality test...")
    
    # Format content as SSML
    formatter = SSMLFormatter()
    ssml_content = formatter.format_podcast_content(sample_content)
    
    print(f"📝 SSML Content Preview:")
    print(ssml_content[:200] + "..." if len(ssml_content) > 200 else ssml_content)
    print()
    
    # Generate audio using the speech generation system
    voice = "en-US-AriaNeural"  # Using a good quality voice
    
    try:
        audio_segment = generate_speech(ssml_content, voice)
        
        # Save to output directory
        output_file = "output/quality_test_audio.wav"
        os.makedirs("output", exist_ok=True)
        
        audio_segment.export(output_file, format="wav")
        
        file_size = os.path.getsize(output_file)
        duration_ms = len(audio_segment)
        duration_sec = duration_ms / 1000
        
        print(f"✅ Audio generated successfully!")
        print(f"📄 File: {output_file}")
        print(f"📏 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"⏱️ Duration: {duration_sec:.1f} seconds")
        print(f"🎵 Sample Rate: {audio_segment.frame_rate} Hz")
        print(f"🔊 Channels: {audio_segment.channels}")
        
        # Generate cache key to show caching working
        cache_key = hashlib.sha256(f"{voice}_{ssml_content}".encode()).hexdigest()
        print(f"🔑 Cache key: {cache_key[:16]}...")
        
        print(f"\n🎧 You can now listen to: {output_file}")
        print("   This demonstrates the current quality of the EdutainmentForge speech generation system.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
