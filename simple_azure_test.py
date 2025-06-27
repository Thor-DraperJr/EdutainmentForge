#!/usr/bin/env python3
"""Simple Azure Speech test."""

print("Starting Azure Speech test...")

try:
    import azure.cognitiveservices.speech as speechsdk
    print("✅ Azure Speech SDK imported successfully")
except Exception as e:
    print(f"❌ Azure import failed: {e}")
    exit(1)

try:
    import os
    from pathlib import Path
    
    # Load .env file
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        print("✅ .env file loaded")
    
    # Test environment variables
    api_key = os.getenv('TTS_API_KEY')
    region = os.getenv('TTS_REGION')
    voice = os.getenv('TTS_VOICE')
    
    print(f"API Key set: {'Yes' if api_key else 'No'}")
    print(f"Region: {region}")
    print(f"Voice: {voice}")
    
    if not api_key:
        print("❌ No API key found in environment")
        exit(1)
    
    # Create speech config
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    print("✅ Speech config created")
    
    # Test synthesis to file
    output_path = Path("output/simple_test.wav")
    output_path.parent.mkdir(exist_ok=True)
    
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    test_text = "Hello from Azure Speech Services! This is a test."
    
    print("Starting synthesis...")
    result = synthesizer.speak_text_async(test_text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✅ Success! Audio saved to: {output_path}")
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"File size: {size} bytes")
        else:
            print("❌ File not found after synthesis")
    else:
        print(f"❌ Synthesis failed: {result.reason}")
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"Cancellation reason: {cancellation.reason}")
            print(f"Error details: {cancellation.error_details}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
