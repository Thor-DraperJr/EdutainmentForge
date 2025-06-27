"""
Command Line Interface for EdutainmentForge.

Provides interactive command-line interface for podcast generation.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

from content import MSLearnFetcher, ContentFetchError, create_sample_content, ScriptProcessor
from audio import create_tts_service, TTSError, AudioProcessor, create_sample_audio
from utils.logger import get_logger


logger = get_logger(__name__)


class CLIInterface:
    """Command-line interface for EdutainmentForge."""
    
    def __init__(self, config: Dict):
        """
        Initialize CLI interface.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.fetcher = MSLearnFetcher()
        self.processor = ScriptProcessor()
        self.audio_processor = AudioProcessor()
        
        # Initialize TTS service
        try:
            self.tts_service = create_tts_service(config)
            logger.info("TTS service initialized successfully")
        except TTSError as e:
            logger.warning(f"TTS service initialization failed: {e}")
            self.tts_service = None
    
    def run(self):
        """Run the interactive CLI."""
        self._print_welcome()
        
        while True:
            try:
                choice = self._show_main_menu()
                
                if choice == '1':
                    self._generate_from_url()
                elif choice == '2':
                    self._generate_from_sample()
                elif choice == '3':
                    self._list_sample_modules()
                elif choice == '4':
                    self._show_configuration()
                elif choice == '5':
                    self._test_tts_service()
                elif choice == 'q':
                    print("\nThank you for using EdutainmentForge!")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"CLI error: {e}")
                print(f"An error occurred: {e}")
    
    def _print_welcome(self):
        """Print welcome message and app info."""
        print("=" * 60)
        print("🎙️  Welcome to EdutainmentForge!")
        print("   Convert MS Learn content into engaging podcasts")
        print("=" * 60)
        print()
    
    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        print("\nMain Menu:")
        print("1. Generate podcast from MS Learn URL")
        print("2. Generate podcast from sample content")
        print("3. List sample modules")
        print("4. Show configuration")
        print("5. Test TTS service")
        print("q. Quit")
        print()
        
        return input("Enter your choice: ").strip().lower()
    
    def _generate_from_url(self):
        """Generate podcast from user-provided URL."""
        print("\n" + "=" * 50)
        print("Generate Podcast from URL")
        print("=" * 50)
        
        url = input("Enter MS Learn module URL: ").strip()
        if not url:
            print("No URL provided.")
            return
        
        try:
            # Fetch content
            print(f"\n📥 Fetching content from: {url}")
            content = self.fetcher.fetch_module_content(url)
            
            # Process to script
            print("🎬 Processing content into podcast script...")
            script_data = self.processor.process_content_to_script(content)
            
            # Generate filename
            safe_title = "".join(c for c in script_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            output_path = self.config['output_directory'] / f"{safe_title}.mp3"
            
            # Generate audio
            success = self._generate_audio(script_data['script'], output_path)
            
            if success:
                self._show_generation_results(script_data, output_path)
            else:
                print("❌ Failed to generate audio. Check logs for details.")
                
        except ContentFetchError as e:
            print(f"❌ Failed to fetch content: {e}")
        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            print(f"❌ Podcast generation failed: {e}")
    
    def _generate_from_sample(self):
        """Generate podcast from sample content."""
        print("\n" + "=" * 50)
        print("Generate Podcast from Sample Content")
        print("=" * 50)
        
        # Use sample content
        content = create_sample_content()
        
        try:
            print("🎬 Processing sample content into podcast script...")
            script_data = self.processor.process_content_to_script(content)
            
            output_path = self.config['output_directory'] / "sample_podcast.mp3"
            
            # Generate audio
            success = self._generate_audio(script_data['script'], output_path)
            
            if success:
                self._show_generation_results(script_data, output_path)
            else:
                print("❌ Failed to generate audio. Check logs for details.")
                
        except Exception as e:
            logger.error(f"Sample podcast generation failed: {e}")
            print(f"❌ Sample podcast generation failed: {e}")
    
    def _generate_audio(self, script: str, output_path: Path) -> bool:
        """Generate audio from script."""
        print(f"🎵 Generating audio: {output_path}")
        
        if self.tts_service:
            success = self.tts_service.synthesize_text(script, output_path)
            
            if success and output_path.exists():
                # Post-process audio if possible
                temp_path = output_path.with_suffix('.tmp.mp3')
                if self.audio_processor.process_audio(output_path, temp_path, normalize_audio=True):
                    # Replace original with processed version
                    temp_path.replace(output_path)
                
                return True
            else:
                return False
        else:
            # Fallback: create sample audio
            print("⚠️  No TTS service available, creating sample file...")
            return create_sample_audio(output_path)
    
    def _show_generation_results(self, script_data: Dict, output_path: Path):
        """Show results of podcast generation."""
        print("\n" + "✅ Podcast Generated Successfully!")
        print("=" * 40)
        print(f"Title: {script_data['title']}")
        print(f"Word Count: {script_data['word_count']}")
        print(f"Estimated Duration: {script_data['estimated_duration']}")
        print(f"Output File: {output_path}")
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"File Size: {file_size / 1024:.1f} KB")
            
            # Show audio info if available
            audio_info = self.audio_processor.get_audio_info(output_path)
            if audio_info.get('duration'):
                print(f"Actual Duration: {audio_info['duration']:.1f} seconds")
        
        print("\n📝 Script Preview:")
        print("-" * 40)
        preview = script_data['script'][:200] + "..." if len(script_data['script']) > 200 else script_data['script']
        print(preview)
        print("-" * 40)
    
    def _list_sample_modules(self):
        """List available sample modules."""
        print("\n" + "=" * 50)
        print("Available Sample Modules")
        print("=" * 50)
        
        modules = self.fetcher.get_sample_modules()
        
        for i, module in enumerate(modules, 1):
            print(f"{i}. {module['title']}")
            print(f"   URL: {module['url']}")
            print(f"   Description: {module['description']}")
            print()
    
    def _show_configuration(self):
        """Show current configuration."""
        print("\n" + "=" * 50)
        print("Current Configuration")
        print("=" * 50)
        
        config_items = [
            ("TTS Service", self.config.get('tts_service', 'Not configured')),
            ("TTS Voice", self.config.get('tts_voice', 'Default')),
            ("Audio Format", self.config.get('audio_format', 'mp3')),
            ("Output Directory", str(self.config.get('output_directory', 'output'))),
            ("Debug Mode", "Yes" if self.config.get('debug') else "No"),
            ("Log Level", self.config.get('log_level', 'INFO')),
        ]
        
        for key, value in config_items:
            print(f"{key:<20}: {value}")
        
        # TTS Service status
        tts_status = "✅ Available" if self.tts_service else "❌ Not available"
        print(f"{'TTS Status':<20}: {tts_status}")
        
        if self.tts_service:
            voices = self.tts_service.get_available_voices()
            if voices:
                print(f"\nAvailable TTS Voices:")
                for voice_id, voice_name in list(voices.items())[:5]:  # Show first 5
                    print(f"  - {voice_id}: {voice_name}")
                if len(voices) > 5:
                    print(f"  ... and {len(voices) - 5} more")
    
    def _test_tts_service(self):
        """Test TTS service with sample text."""
        print("\n" + "=" * 50)
        print("Test TTS Service")
        print("=" * 50)
        
        if not self.tts_service:
            print("❌ No TTS service available. Please check your configuration.")
            return
        
        test_text = input("Enter text to test (or press Enter for default): ").strip()
        if not test_text:
            test_text = "Hello! This is a test of the EdutainmentForge text-to-speech system."
        
        test_output = self.config['output_directory'] / "tts_test.mp3"
        
        print(f"🎵 Testing TTS with text: '{test_text}'")
        
        try:
            success = self.tts_service.synthesize_text(test_text, test_output)
            
            if success and test_output.exists():
                print(f"✅ TTS test successful! Audio saved to: {test_output}")
                
                # Show audio info
                audio_info = self.audio_processor.get_audio_info(test_output)
                if audio_info:
                    print(f"Duration: {audio_info.get('duration', 'unknown')} seconds")
                    print(f"File size: {audio_info.get('file_size', 0) / 1024:.1f} KB")
            else:
                print("❌ TTS test failed. Check your configuration and API keys.")
                
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            print(f"❌ TTS test failed: {e}")


def main(config: Dict):
    """
    Main entry point for CLI interface.
    
    Args:
        config: Application configuration dictionary
    """
    try:
        cli = CLIInterface(config)
        cli.run()
    except Exception as e:
        logger.error(f"CLI initialization failed: {e}")
        print(f"Failed to start EdutainmentForge: {e}")
        sys.exit(1)
