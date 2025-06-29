#!/usr/bin/env python3
"""
EdutainmentForge - Quick Azure Speech Processing

Simple command-line tool for processing Microsoft Learn URLs into podcasts using Azure Speech Service.
"""

import os
import sys
import argparse
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

def process_content_to_podcast(content_text, title, voice=None, output_name=None, ai_enhance=False):
    """Process direct content text into a podcast."""
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        from content.processor import ScriptProcessor
        from audio.tts import create_tts_service
        from audio.multivoice_tts import create_multivoice_tts_service
        from utils.config import load_config
        
        print(f"📝 Processing content: {title}")
        
        # Load config
        config = load_config()
        
        # Override voice if specified
        if voice:
            config['tts_voice'] = voice
            print(f"🎤 Using voice: {voice}")
        
        # Create content structure
        content = {
            'title': title,
            'content': content_text
        }
        
        print(f"✅ Content prepared: {content['title']}")
        print(f"📄 Content length: {len(content['content'])} characters")
        
        # Process into script
        print("✍️  Converting to podcast script...")
        if ai_enhance:
            print("🤖 AI enhancement enabled - creating interactive dialogue...")
        processor = ScriptProcessor(use_ai_enhancement=ai_enhance)
        script_result = processor.process_content_to_script(content)
        script = script_result.get('script', '')
        
        # Generate audio
        print("🎵 Generating audio with Azure Speech Service...")
        tts_service = create_tts_service(config)
        
        # Create output filename
        if not output_name:
            # Clean title for filename
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_title = clean_title.replace(' ', '_')[:50]  # Limit length
            output_name = f"{clean_title}_podcast"
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save script
        script_path = output_dir / f"{output_name}_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"📝 Script saved: {script_path}")
        
        # Generate audio
        audio_path = output_dir / f"{output_name}.wav"
        
        # Use multivoice TTS for better quality
        multivoice_tts = create_multivoice_tts_service(config)
        if multivoice_tts:
            multivoice_tts.generate_multivoice_audio(script, str(audio_path))
        else:
            # Fallback to single voice
            tts_service.generate_audio(script, str(audio_path))
        
        print(f"🎵 Audio saved: {audio_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing content: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_url_to_podcast(url, voice=None, output_name=None, ai_enhance=False):
    """Process a Microsoft Learn URL into a podcast."""
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        from content.fetcher import MSLearnFetcher
        from content.processor import ScriptProcessor
        from audio.tts import create_tts_service
        from audio.multivoice_tts import create_multivoice_tts_service
        from utils.config import load_config
        
        print(f"🔗 Processing URL: {url}")
        
        # Load config
        config = load_config()
        
        # Override voice if specified
        if voice:
            config['tts_voice'] = voice
            print(f"🎤 Using voice: {voice}")
        
        # Step 1: Fetch content
        print("📥 Fetching content from Microsoft Learn...")
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)
        
        if not content or not content.get('title') or not content.get('content'):
            print("❌ Failed to fetch content or content is empty")
            return False
        
        print(f"✅ Content fetched: {content['title']}")
        print(f"📄 Content length: {len(content['content'])} characters")
        
        # Step 2: Process into script
        print("✍️  Converting to podcast script...")
        if ai_enhance:
            print("🤖 AI enhancement enabled - creating interactive dialogue...")
        processor = ScriptProcessor(use_ai_enhancement=ai_enhance)
        script_result = processor.process_content_to_script(content)
        script = script_result.get('script', '')
        
        # Step 3: Generate audio
        print("🎵 Generating audio with Azure Speech Service...")
        tts_service = create_tts_service(config)
        
        # Create output filename
        if not output_name:
            # Clean title for filename
            clean_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_title = clean_title.replace(' ', '_')[:50]  # Limit length
            output_name = f"{clean_title}_podcast"
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save script
        script_path = output_dir / f"{output_name}_script.txt"
        script_path.write_text(script)
        print(f"📝 Script saved: {script_path}")
        
        # Generate audio with multi-voice support
        print("🎵 Generating multi-voice audio with Sarah & Mike...")
        multivoice_tts = create_multivoice_tts_service(config)
        audio_path = output_dir / f"{output_name}.wav"
        success = multivoice_tts.synthesize_dialogue_script(script, audio_path)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            duration_estimate = len(script) / 12  # ~12 chars per second
            
            print(f"✅ SUCCESS! Podcast generated:")
            print(f"   🎧 Audio: {audio_path}")
            print(f"   📝 Script: {script_path}")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️  Duration: ~{duration_estimate:.1f} seconds")
            return True
        else:
            print("❌ Failed to generate audio")
            return False
            
    except Exception as e:
        print(f"❌ Error processing URL: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_available_voices():
    """List available Azure voices."""
    voices = {
        "en-US-AriaNeural": "Aria - US English Female, Expressive (recommended for podcasts)",
        "en-US-GuyNeural": "Guy - US English Male, Friendly",
        "en-US-JennyNeural": "Jenny - US English Female, Assistant-like",
        "en-US-DavisNeural": "Davis - US English Male, Conversational",
        "en-GB-LibbyNeural": "Libby - UK English Female",
        "en-GB-RyanNeural": "Ryan - UK English Male",
    }
    
    print("🎤 Available Azure Neural Voices:")
    for voice_id, description in voices.items():
        current = " (current)" if os.getenv('TTS_VOICE') == voice_id else ""
        print(f"   • {voice_id}: {description}{current}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="EdutainmentForge - Convert Microsoft Learn content to podcasts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single unit
  python3 podcast_cli.py https://learn.microsoft.com/training/modules/intro-to-ai/

  # Use a specific voice
  python3 podcast_cli.py https://learn.microsoft.com/training/modules/intro-to-ai/ --voice en-US-GuyNeural

  # Custom output name
  python3 podcast_cli.py https://learn.microsoft.com/training/modules/intro-to-ai/ --output "AI_Basics"

  # List available voices
  python3 podcast_cli.py --list-voices
        """
    )
    
    parser.add_argument('url', nargs='?', help='Microsoft Learn URL to process')
    parser.add_argument('--content', help='Direct content text for processing (alternative to URL)')
    parser.add_argument('--title', help='Title for the content (required when using --content)')
    parser.add_argument('--voice', help='Azure voice to use (e.g., en-US-AriaNeural)')
    parser.add_argument('--output', help='Output filename prefix')
    parser.add_argument('--ai-enhance', action='store_true', help='Enable AI-enhanced dialogue generation')
    parser.add_argument('--list-voices', action='store_true', help='List available voices')
    
    args = parser.parse_args()
    
    print("🎙️  EdutainmentForge - Azure Speech Edition")
    print("=" * 60)
    
    # Load environment
    load_env()
    
    # Check if Azure Speech is configured
    if not os.getenv('TTS_API_KEY'):
        print("❌ Azure Speech Service not configured!")
        print("💡 Set TTS_API_KEY in your .env file")
        print("📖 See docs/azure-speech-setup.md for setup instructions")
        return False
    
    if args.list_voices:
        list_available_voices()
        return True
    
    # Check for content vs URL
    if args.content:
        if not args.title:
            print("❌ --title is required when using --content")
            return False
        
        # Process direct content
        success = process_content_to_podcast(args.content, args.title, args.voice, args.output, args.ai_enhance)
    else:
        if not args.url:
            parser.print_help()
            print("\n💡 Tip: Use --list-voices to see available Azure voices")
            print("💡 Use --content with --title to process text directly")
            return False

        # Validate URL
        if 'learn.microsoft.com' not in args.url:
            print("❌ URL must be from learn.microsoft.com")
            return False

        # Process the URL
        success = process_url_to_podcast(args.url, args.voice, args.output, args.ai_enhance)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Podcast generation completed successfully!")
        print("🎧 Your educational content is now ready to listen!")
    else:
        print("⚠️  Podcast generation failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
