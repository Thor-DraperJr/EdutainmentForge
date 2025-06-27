#!/usr/bin/env python3
"""
Quick test script for EdutainmentForge functionality.

Tests the core pipeline without requiring full setup.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from content import create_sample_content, ScriptProcessor
from audio import create_sample_audio
from utils import setup_logger


def main():
    """Run quick functionality test."""
    print("🧪 EdutainmentForge Quick Test")
    print("=" * 40)
    
    # Setup logging
    logger = setup_logger(level='INFO')
    
    try:
        # Test content processing
        print("1️⃣  Testing content processing...")
        content = create_sample_content()
        processor = ScriptProcessor()
        script_data = processor.process_content_to_script(content)
        
        print(f"✅ Content processed successfully!")
        print(f"   Title: {script_data['title']}")
        print(f"   Word count: {script_data['word_count']}")
        print(f"   Estimated duration: {script_data['estimated_duration']}")
        
        # Test audio generation (sample)
        print("\n2️⃣  Testing sample audio generation...")
        output_dir = Path(__file__).parent.parent / 'output'
        output_dir.mkdir(exist_ok=True)
        
        audio_file = output_dir / 'test_sample.mp3'
        success = create_sample_audio(audio_file)
        
        if success:
            print("✅ Sample audio generated successfully!")
            print(f"   Output: {audio_file}")
        else:
            print("❌ Sample audio generation failed")
        
        print("\n🎉 Quick test completed!")
        print("\nTo run the full application:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python src/main.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
