#!/usr/bin/env python3
"""
Azure Speech Service Voice Demo

Demonstrates different Azure neural voices for EdutainmentForge.
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

def test_voice(speech_config, voice_name, voice_description, output_dir):
    """Test a specific Azure voice."""
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Set voice
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Create output file
        safe_name = voice_name.replace('-', '_')
        output_path = output_dir / f"demo_{safe_name}.wav"
        
        # Audio config
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # Demo text
        demo_text = f"""
        Hello! I'm {voice_description}. 
        Welcome to EdutainmentForge, where we transform Microsoft Learn content 
        into engaging, entertaining podcasts. This demo showcases my voice 
        for educational content narration. I can make learning about artificial 
        intelligence, cloud computing, and other technical topics both 
        informative and enjoyable!
        """
        
        print(f"🎤 Testing {voice_name} ({voice_description})...")
        
        # Synthesize
        result = synthesizer.speak_text_async(demo_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            file_size = output_path.stat().st_size if output_path.exists() else 0
            print(f"   ✅ Success! Generated {output_path.name} ({file_size:,} bytes)")
            return True
        else:
            print(f"   ❌ Failed: {result.reason}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🎙️  Azure Speech Service Voice Demo")
    print("=" * 60)
    
    load_env()
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Get credentials
        api_key = os.getenv('TTS_API_KEY')
        region = os.getenv('TTS_REGION', 'eastus2')
        
        if not api_key:
            print("❌ No API key found. Set TTS_API_KEY in .env file.")
            return False
        
        print(f"📍 Using region: {region}")
        print(f"🔑 API key configured: Yes")
        
        # Create speech config
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        
        # Create output directory
        output_dir = Path('output/voice_demos')
        output_dir.mkdir(exist_ok=True)
        
        # Test different voices
        voices_to_test = [
            ("en-US-AriaNeural", "Aria - US English Female, Expressive"),
            ("en-US-GuyNeural", "Guy - US English Male, Friendly"),
            ("en-US-JennyNeural", "Jenny - US English Female, Assistant"),
            ("en-US-DavisNeural", "Davis - US English Male, Conversational"),
            ("en-GB-LibbyNeural", "Libby - UK English Female"),
        ]
        
        print(f"\n🎵 Generating voice demos...")
        print(f"📁 Output directory: {output_dir}")
        
        successful = 0
        for voice_name, voice_description in voices_to_test:
            if test_voice(speech_config, voice_name, voice_description, output_dir):
                successful += 1
        
        print(f"\n📊 Results: {successful}/{len(voices_to_test)} voices tested successfully")
        
        if successful > 0:
            print(f"\n🎧 Listen to the demos in: {output_dir}")
            print("💡 Choose your favorite voice by updating TTS_VOICE in .env")
            print("\n📝 Recommended voices for podcasts:")
            print("   • Aria: Great for engaging, expressive narration")
            print("   • Guy: Perfect for friendly, approachable content")
            print("   • Davis: Excellent for conversational style")
        
        return successful > 0
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("🎉 Voice demo completed! Choose your favorite voice for EdutainmentForge.")
    else:
        print("⚠️  Demo failed. Check your Azure Speech Service configuration.")
