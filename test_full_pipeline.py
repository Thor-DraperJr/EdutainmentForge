#!/usr/bin/env python3
"""
Test Azure Speech Service with existing script content.
"""

import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

def main():
    print("🎙️  Azure Speech Service Full Pipeline Test")
    print("=" * 50)
    
    # Load environment
    load_env()
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        print("✅ Azure Speech SDK available")
        
        # Get credentials
        api_key = os.getenv('TTS_API_KEY')
        region = os.getenv('TTS_REGION', 'eastus2')
        voice = os.getenv('TTS_VOICE', 'en-US-AriaNeural')
        
        if not api_key:
            print("❌ No API key found")
            return False
        
        print(f"📍 Region: {region}")
        print(f"🎤 Voice: {voice}")
        
        # Load existing script
        script_path = Path('output/Introduction_to_AI_script.txt')
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return False
        
        script_content = script_path.read_text()
        print(f"📄 Script loaded: {len(script_content)} characters")
        
        # Truncate for testing (full script might be very long)
        if len(script_content) > 500:
            script_content = script_content[:500] + "... This concludes our introduction to AI. Thank you for listening!"
            print("📝 Script truncated for testing")
        
        # Create Azure TTS service
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        
        # Generate audio
        output_path = Path('output/AI_Introduction_podcast.wav')
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        print("🎵 Generating audio...")
        result = synthesizer.speak_text_async(script_content).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            file_size = output_path.stat().st_size if output_path.exists() else 0
            duration_estimate = len(script_content) / 12  # ~12 chars per second
            
            print(f"✅ SUCCESS! Podcast generated: {output_path.name}")
            print(f"📊 File size: {file_size:,} bytes")
            print(f"⏱️  Estimated duration: {duration_estimate:.1f} seconds")
            print(f"🎯 Ready for playback!")
            
            return True
        else:
            print(f"❌ Synthesis failed: {result.reason}")
            if result.reason == speechsdk.ResultReason.Canceled:
                details = result.cancellation_details
                print(f"   Reason: {details.reason}")
                if details.error_details:
                    print(f"   Error: {details.error_details}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Azure Speech Service is working perfectly!")
        print("Your EdutainmentForge setup is ready for podcast generation!")
    else:
        print("⚠️  Setup needs attention. Check the errors above.")
