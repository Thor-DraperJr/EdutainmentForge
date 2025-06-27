#!/usr/bin/env python3
"""
Single Module Processor for EdutainmentForge

Process one Microsoft Learn module at a time for focused testing and development.
Usage: python process_single_module.py <module_url>
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher, ScriptProcessor
from audio import create_tts_service, TTSError, create_sample_audio
from utils import load_config, setup_logger


def process_single_module(module_url: str, output_dir: Path = None):
    """
    Process a single Microsoft Learn module into a podcast episode.
    
    Args:
        module_url: URL of the MS Learn module/unit to process
        output_dir: Optional output directory (defaults to ./output)
    """
    logger = setup_logger()
    
    if not output_dir:
        output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print("🎯 EdutainmentForge - Single Module Processor")
    print("=" * 60)
    print(f"Processing: {module_url}")
    print()
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize services
        fetcher = MSLearnFetcher()
        processor = ScriptProcessor()
        
        # Step 1: Fetch content
        print("📥 Step 1: Fetching content...")
        content = fetcher.fetch_module_content(module_url)
        
        print(f"✅ Content fetched successfully!")
        print(f"   Title: {content['title']}")
        print(f"   Content length: {len(content['content'])} characters")
        print(f"   Source: {content['url']}")
        print()
        
        # Show content preview
        preview = content['content'][:300] + "..." if len(content['content']) > 300 else content['content']
        print("📄 Content Preview:")
        print("-" * 40)
        print(preview)
        print("-" * 40)
        print()
        
        # Step 2: Process into script
        print("🎬 Step 2: Converting to podcast script...")
        script_data = processor.process_content_to_script(content)
        
        print(f"✅ Script generated successfully!")
        print(f"   Word count: {script_data['word_count']}")
        print(f"   Estimated duration: {script_data['estimated_duration']}")
        print()
        
        # Show script preview
        script_preview = script_data['script'][:400] + "..." if len(script_data['script']) > 400 else script_data['script']
        print("🎭 Script Preview:")
        print("-" * 40)
        print(script_preview)
        print("-" * 40)
        print()
        
        # Save script to file
        safe_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        
        script_file = output_dir / f"{safe_title}_script.txt"
        script_file.write_text(script_data['script'], encoding='utf-8')
        print(f"💾 Script saved to: {script_file}")
        
        # Step 3: Generate audio (if TTS available)
        print("\n🎵 Step 3: Generating audio...")
        
        try:
            tts_service = create_tts_service(config)
            audio_file = output_dir / f"{safe_title}.mp3"
            
            success = tts_service.synthesize_text(script_data['script'], audio_file)
            
            if success and audio_file.exists():
                print(f"✅ Audio generated successfully: {audio_file}")
                file_size = audio_file.stat().st_size / 1024
                print(f"   File size: {file_size:.1f} KB")
            else:
                print("⚠️  TTS failed, creating sample file...")
                sample_file = output_dir / f"{safe_title}_sample.txt"
                create_sample_audio(sample_file)
                print(f"📝 Sample file created: {sample_file}")
                
        except TTSError as e:
            print(f"⚠️  TTS not available: {e}")
            print("📝 Creating text file instead...")
            text_file = output_dir / f"{safe_title}_audio_script.txt"
            text_file.write_text(f"Audio Script for: {content['title']}\n\n{script_data['script']}", encoding='utf-8')
            print(f"💾 Audio script saved to: {text_file}")
        
        # Step 4: Summary
        print("\n🎉 Processing Complete!")
        print("=" * 40)
        print(f"Module: {content['title']}")
        print(f"Original content: {len(content['content'])} chars")
        print(f"Script: {script_data['word_count']} words")
        print(f"Estimated audio: {script_data['estimated_duration']}")
        print(f"Output directory: {output_dir}")
        
        # List generated files
        print(f"\n📁 Generated files:")
        for file in output_dir.glob(f"{safe_title}*"):
            print(f"   - {file.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Module processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        return False


def main():
    """Main entry point for single module processing."""
    parser = argparse.ArgumentParser(
        description="Process a single Microsoft Learn module into a podcast episode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_single_module.py "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/1-introduction"
  python process_single_module.py "https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/" --output-dir custom_output
        """
    )
    
    parser.add_argument("url", help="URL of the Microsoft Learn module or unit to process")
    parser.add_argument("--output-dir", "-o", type=Path, help="Output directory for generated files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = process_single_module(args.url, args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
