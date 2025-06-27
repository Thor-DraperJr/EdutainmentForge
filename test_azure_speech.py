#!/usr/bin/env python3
"""
Test Azure Speech Service integration for EdutainmentForge.

This script tests the full pipeline from script to audio generation using Azure TTS.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.tts import create_tts_service, TTSError
from utils.config import load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def test_azure_speech_service():
    """Test Azure Speech Service configuration and audio generation."""
    try:
        # Load .env file manually
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Log current TTS settings (without exposing API key)
        logger.info(f"TTS Service: {config.get('tts_service', 'not set')}")
        logger.info(f"TTS Region: {config.get('tts_region', 'not set')}")
        logger.info(f"TTS Voice: {config.get('tts_voice', 'not set')}")
        logger.info(f"API Key configured: {'Yes' if config.get('tts_api_key') else 'No'}")
        
        # Create TTS service
        logger.info("Creating TTS service...")
        tts_service = create_tts_service(config)
        logger.info(f"TTS service created: {type(tts_service).__name__}")
        
        # Test with a short sample text
        test_text = """
        Welcome to EdutainmentForge! This is a test of Azure Speech Services.
        We're converting Microsoft Learn content into engaging podcasts.
        If you can hear this clearly, the integration is working perfectly!
        """
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate audio file
        audio_path = output_dir / "azure_speech_test.wav"
        logger.info(f"Generating audio file: {audio_path}")
        
        success = tts_service.synthesize_text(test_text, audio_path)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            logger.info(f"✅ SUCCESS! Audio file generated: {audio_path}")
            logger.info(f"File size: {file_size:,} bytes")
            
            # Check available voices
            voices = tts_service.get_available_voices()
            logger.info(f"Available voices: {len(voices)}")
            for voice_id, voice_name in list(voices.items())[:3]:  # Show first 3
                logger.info(f"  - {voice_id}: {voice_name}")
            
            return True
        else:
            logger.error("❌ FAILED: Audio file was not generated")
            return False
            
    except TTSError as e:
        logger.error(f"❌ TTS Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_full_pipeline():
    """Test the full pipeline with an existing script."""
    try:
        # Load existing script
        script_path = Path("output/Introduction_to_AI_script.txt")
        if not script_path.exists():
            logger.error(f"Script file not found: {script_path}")
            return False
        
        script_content = script_path.read_text()
        logger.info(f"Loaded script: {len(script_content)} characters")
        
        # Create TTS service
        config = load_config()
        tts_service = create_tts_service(config)
        
        # Generate audio from full script
        audio_path = Path("output/Introduction_to_AI_full_audio.wav")
        logger.info(f"Generating full audio: {audio_path}")
        
        success = tts_service.synthesize_text(script_content, audio_path)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            duration_estimate = len(script_content) / 1000 * 60  # Rough estimate
            logger.info(f"✅ SUCCESS! Full audio generated: {audio_path}")
            logger.info(f"File size: {file_size:,} bytes")
            logger.info(f"Estimated duration: ~{duration_estimate:.1f} seconds")
            return True
        else:
            logger.error("❌ FAILED: Full audio was not generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Full pipeline error: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("🎙️  Testing Azure Speech Service Integration")
    logger.info("=" * 60)
    
    # Test 1: Basic Azure Speech Service
    logger.info("\n📋 Test 1: Basic Azure Speech Service")
    test1_success = test_azure_speech_service()
    
    # Test 2: Full pipeline with existing script
    logger.info("\n📋 Test 2: Full Pipeline Test")
    test2_success = test_full_pipeline()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary:")
    logger.info(f"  Basic Azure TTS: {'✅ PASS' if test1_success else '❌ FAIL'}")
    logger.info(f"  Full Pipeline: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        logger.info("\n🎉 All tests passed! Azure Speech Service is working correctly.")
        logger.info("You can now process Microsoft Learn content into audio podcasts!")
    else:
        logger.info("\n⚠️  Some tests failed. Check the logs above for details.")
    
    return test1_success and test2_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
