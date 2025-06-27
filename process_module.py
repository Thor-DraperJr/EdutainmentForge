"""
Single Module Processor for EdutainmentForge

Process one Microsoft Learn module at a time for testing and development.
"""

import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher, ScriptProcessor, create_sample_content
from audio import create_tts_service, TTSError, create_sample_audio
from utils import load_config, setup_logger


def process_single_module(url: str, generate_audio: bool = False):
    """
    Process a single Microsoft Learn module.
    
    Args:
        url: URL of the module to process
        generate_audio: Whether to generate audio output
    """
    logger = setup_logger()
    
    print("🎯 EdutainmentForge - Single Module Processor")
    print("=" * 60)
    print(f"📚 Processing: {url}")
    print()
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        fetcher = MSLearnFetcher()
        processor = ScriptProcessor()
        
        # Step 1: Fetch content
        print("📥 Step 1: Fetching module content...")
        content = fetcher.fetch_module_content(url)
        
        print(f"✅ Content fetched successfully!")
        print(f"   Title: {content['title']}")
        print(f"   Content length: {len(content['content'])} characters")
        print(f"   Source: {content['url']}")
        print()
        
        # Show content preview
        print("📄 Content Preview:")
        print("-" * 50)
        preview = content['content'][:500] + "..." if len(content['content']) > 500 else content['content']
        print(preview)
        print("-" * 50)
        print()
        
        # Step 2: Generate script
        print("🎬 Step 2: Processing content into podcast script...")
        script_data = processor.process_content_to_script(content)
        
        print(f"✅ Script generated successfully!")
        print(f"   Word count: {script_data['word_count']}")
        print(f"   Estimated duration: {script_data['estimated_duration']}")
        print()
        
        # Show script preview
        print("🎙️ Script Preview:")
        print("-" * 50)
        script_preview = script_data['script'][:300] + "..." if len(script_data['script']) > 300 else script_data['script']
        print(script_preview)
        print("-" * 50)
        print()
        
        # Save script to file
        output_dir = config['output_directory']
        safe_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        
        script_file = output_dir / f"{safe_title}_script.txt"
        script_file.write_text(script_data['script'], encoding='utf-8')
        print(f"💾 Script saved to: {script_file}")
        
        # Step 3: Generate audio (optional)
        if generate_audio:
            print("🎵 Step 3: Generating audio...")
            
            try:
                tts_service = create_tts_service(config)
                audio_file = output_dir / f"{safe_title}.mp3"
                
                success = tts_service.synthesize_text(script_data['script'], audio_file)
                
                if success and audio_file.exists():
                    print(f"✅ Audio generated successfully: {audio_file}")
                    file_size = audio_file.stat().st_size / 1024
                    print(f"   File size: {file_size:.1f} KB")
                else:
                    # Fallback to sample audio
                    print("⚠️  TTS not available, creating sample file...")
                    create_sample_audio(audio_file)
                    print(f"📝 Sample file created: {audio_file}")
                    
            except TTSError as e:
                print(f"⚠️  TTS Error: {e}")
                # Create sample file instead
                audio_file = output_dir / f"{safe_title}.txt"
                create_sample_audio(audio_file)
                print(f"📝 Sample file created: {audio_file}")
        
        # Summary
        print()
        print("🎉 Module Processing Complete!")
        print("=" * 40)
        print(f"Module: {content['title']}")
        print(f"Original content: {len(content['content'])} characters")
        print(f"Generated script: {script_data['word_count']} words")
        print(f"Estimated podcast: {script_data['estimated_duration']}")
        print(f"Files saved to: {output_dir}")
        
        return {
            'success': True,
            'title': content['title'],
            'content_length': len(content['content']),
            'script_words': script_data['word_count'],
            'duration': script_data['estimated_duration'],
            'script_file': str(script_file)
        }
        
    except Exception as e:
        logger.error(f"Module processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Process a single Microsoft Learn module')
    parser.add_argument('url', help='URL of the Microsoft Learn module')
    parser.add_argument('--audio', action='store_true', help='Generate audio output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    result = process_single_module(args.url, args.audio)
    
    if not result['success']:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode if no arguments
        print("🎯 EdutainmentForge - Single Module Processor")
        print("=" * 60)
        print()
        
        url = input("Enter Microsoft Learn module URL: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            sys.exit(1)
        
        audio_choice = input("Generate audio? (y/n): ").strip().lower()
        generate_audio = audio_choice in ['y', 'yes']
        
        process_single_module(url, generate_audio)
    else:
        main()
