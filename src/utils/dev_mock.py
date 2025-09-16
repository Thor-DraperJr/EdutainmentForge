"""
Development mock services for testing podcast generation without Azure services.

Creates fake audio files and simulated processing for local development.
"""

import os
import wave
import struct
import math
import time
from pathlib import Path
from typing import Dict, Optional
import tempfile
import random

from utils.logger import get_logger

logger = get_logger(__name__)


class MockMultiVoiceTTSService:
    """Mock TTS service that creates fake audio files for development."""
    
    def __init__(self, config: Dict):
        """Initialize mock TTS service."""
        self.config = config
        logger.info("🎭 Using MockMultiVoiceTTSService for development")
    
    def create_podcast_from_script(self, script: str, output_path: Path, 
                                 progress_callback=None) -> bool:
        """
        Create a mock podcast with fake audio.
        
        Args:
            script: The podcast script
            output_path: Where to save the audio file
            progress_callback: Progress update function
            
        Returns:
            True if successful
        """
        try:
            # Simulate processing time and progress updates
            steps = [
                (10, "Parsing dialogue segments..."),
                (30, "Generating Sarah's voice segments..."),
                (50, "Generating Mike's voice segments..."),
                (70, "Adding natural pauses..."),
                (85, "Assembling audio segments..."),
                (95, "Finalizing podcast...")
            ]
            
            for progress, message in steps:
                if progress_callback:
                    try:
                        progress_callback(progress, message)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
                
                # Simulate processing time
                time.sleep(0.5 + random.uniform(0.1, 0.3))
            
            # Calculate approximate duration based on script length
            word_count = len(script.split())
            # Assume ~150 words per minute speaking rate
            duration_seconds = max(10, (word_count / 150) * 60)
            
            # Create the mock audio file
            self._create_mock_audio_file(output_path, duration_seconds)
            
            # Save the script alongside the audio
            script_path = output_path.with_suffix('.txt').with_name(
                output_path.stem + '_script.txt'
            )
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            if progress_callback:
                try:
                    progress_callback(100, "Mock podcast generated successfully!")
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            logger.info(f"🎧 Created mock podcast: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create mock podcast: {e}")
            return False
    
    def _create_mock_audio_file(self, output_path: Path, duration_seconds: float):
        """Create a mock WAV file with generated tones."""
        sample_rate = 22050
        channels = 1
        sample_width = 2  # 16-bit
        
        with wave.open(str(output_path), 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            
            frames = []
            total_frames = int(sample_rate * duration_seconds)
            
            # Create a more interesting mock audio with multiple tones
            # to simulate conversation
            for i in range(total_frames):
                t = float(i) / sample_rate
                
                # Simulate conversation with different "voices" (frequencies)
                # Switch between two frequencies to simulate Sarah and Mike
                segment_length = 3.0  # 3 second segments
                segment = int(t / segment_length) % 2
                
                if segment == 0:  # "Sarah" - higher pitch
                    frequency = 350.0
                    volume = 0.3
                else:  # "Mike" - lower pitch  
                    frequency = 250.0
                    volume = 0.3
                
                # Add some variation and make it less monotonous
                frequency += 20 * math.sin(t * 0.5)  # Slight pitch variation
                
                # Fade in/out at segment boundaries to simulate pauses
                fade_time = 0.2  # 200ms fade
                segment_time = t % segment_length
                if segment_time < fade_time:
                    volume *= (segment_time / fade_time)
                elif segment_time > (segment_length - fade_time):
                    volume *= ((segment_length - segment_time) / fade_time)
                
                # Generate the wave value
                wave_value = int(16384 * volume * math.sin(frequency * 2 * math.pi * t))
                
                # Add some background "static" to make it sound more realistic
                noise = random.randint(-500, 500)
                wave_value = max(-32767, min(32767, wave_value + noise))
                
                frames.append(struct.pack('<h', wave_value))
            
            wav_file.writeframes(b''.join(frames))


class MockScriptProcessor:
    """Mock script processor that generates sample dialogue."""
    
    def __init__(self):
        logger.info("📝 Using MockScriptProcessor for development")
    
    def process_content_to_script(self, content: Dict) -> Dict:
        """Generate a mock podcast script from content."""
        title = content.get('title', 'Unknown Topic')
        topic = title.replace(' - Microsoft Learn Module', '')
        
        # Generate a realistic podcast script
        script = f"""Sarah: Welcome to today's episode about {topic}!

Mike: Thanks Sarah! I'm really excited to dive into this topic. For our listeners who might be new to this, could you give us a quick overview of what {topic} is all about?

Sarah: Absolutely! {topic} is a fundamental concept that every developer working with cloud technologies should understand. It provides essential functionality for modern applications.

Mike: That's a great point. What are some of the key benefits that make {topic} so important?

Sarah: Well, there are several key advantages. First, it enables scalability - you can grow your applications as your business needs change. Second, it provides robust security features that protect your data and applications.

Mike: Security is definitely crucial. Can you walk us through some best practices that developers should follow?

Sarah: Of course! One of the most important principles is to always follow the principle of least privilege. This means giving users and applications only the minimum access they need to do their job.

Mike: That makes a lot of sense. What about monitoring and maintenance? How should teams approach that?

Sarah: Great question! It's essential to implement proper monitoring from day one. You want to track performance metrics, usage patterns, and costs. This helps you optimize your setup and catch issues early.

Mike: Speaking of real-world applications, could you share a common scenario where developers would use {topic}?

Sarah: Absolutely! A common scenario is setting up a new project. You need to configure your environment properly, establish authentication, and ensure everything is secure from the start.

Mike: That's really helpful. What advice would you give to someone just starting out with {topic}?

Sarah: I'd recommend starting with the basics - understand the core concepts first, then practice with hands-on exercises. Don't try to learn everything at once; build your knowledge gradually.

Mike: Excellent advice! Before we wrap up, are there any additional resources our listeners should check out?

Sarah: Definitely! The Microsoft Learn documentation is comprehensive, and there are plenty of hands-on labs you can try. Practice makes perfect!

Mike: Thanks so much for sharing your expertise, Sarah. This has been really insightful!

Sarah: My pleasure, Mike! Thanks for having me, and thank you to our listeners for joining us today. Until next time!"""

        return {
            'script': script,
            'word_count': len(script.split()),
            'estimated_duration': f"{len(script.split()) // 150}m {(len(script.split()) % 150) * 60 // 150}s"
        }


class MockMSLearnFetcher:
    """Mock fetcher that returns sample content for development."""
    
    def __init__(self):
        logger.info("🌐 Using MockMSLearnFetcher for development")
    
    def fetch_module_content(self, url: str) -> Dict:
        """Return mock content based on URL."""
        # Extract a topic from the URL or use default
        topic = "Azure Fundamentals"
        
        if "authentication" in url.lower():
            topic = "Azure Authentication"
        elif "storage" in url.lower():
            topic = "Azure Storage"
        elif "compute" in url.lower():
            topic = "Azure Compute"
        elif "network" in url.lower():
            topic = "Azure Networking"
        
        # Simulate processing time
        time.sleep(1.0)
        
        return {
            'title': f'{topic} - Microsoft Learn Module',
            'content': self._generate_mock_content(topic),
            'url': url,
            'summary': f'This module covers the fundamentals of {topic}.',
            'learning_objectives': [
                f'Understand the basics of {topic}',
                f'Learn key concepts and terminology',
                f'Apply {topic} in real-world scenarios'
            ]
        }
    
    def _generate_mock_content(self, topic: str) -> str:
        """Generate mock educational content for the topic."""
        return f"""
# {topic} Overview

## Introduction

{topic} is a fundamental concept in cloud computing that every developer should understand. In this module, we'll explore the key concepts and practical applications.

## Key Concepts

### What is {topic}?

{topic} provides essential functionality for modern cloud applications. It enables developers to build scalable, secure, and efficient solutions.

### Core Components

The main components of {topic} include:

1. **Configuration** - Setting up your environment properly
2. **Implementation** - Writing the code to use these services
3. **Security** - Ensuring your solutions are protected
4. **Monitoring** - Keeping track of performance and usage

## Best Practices

When working with {topic}, consider these best practices:

- Always follow the principle of least privilege
- Implement proper error handling and retry logic
- Monitor your usage and costs regularly
- Keep your configurations up to date

## Common Scenarios

### Scenario 1: Basic Setup
Setting up {topic} for a new project involves configuring the necessary services and establishing proper authentication.

### Scenario 2: Integration
Integrating {topic} with existing applications requires careful planning and testing.

## Summary

{topic} is essential for building modern cloud applications. By understanding these concepts and following best practices, you can create robust and scalable solutions.

## Next Steps

- Try the hands-on exercises
- Explore additional resources
- Practice with real-world scenarios
"""


def create_mock_services():
    """Create mock services when Azure services aren't available."""
    return {
        'tts_service': MockMultiVoiceTTSService,
        'fetcher': MockMSLearnFetcher
    }


def is_development_mode() -> bool:
    """
    Check if we should use mock services for local development.
    
    This is designed to be conservative - only activate development mode
    when explicitly requested, not when production credentials are missing.
    """
    # Only activate development mode if explicitly requested via environment variables
    
    # Method 1: Explicit development mode flag
    if os.getenv('DEV_MODE', '').lower() == 'true':
        logger.info("🔧 Development mode activated via DEV_MODE environment variable")
        return True
    
    # Method 2: Explicit testing flag (for local testing)
    if os.getenv('DISABLE_AUTH_FOR_TESTING', '').lower() == 'true':
        logger.info("🔧 Development mode activated via DISABLE_AUTH_FOR_TESTING environment variable")
        return True
    
    # Method 3: Check for explicit dummy/test credentials (not missing credentials)
    test_credentials = ['dummy-key-for-local-testing', 'test-key', 'local-dev']
    openai_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    speech_key = os.getenv('AZURE_SPEECH_KEY', '')
    
    if openai_key.lower() in test_credentials or speech_key.lower() in test_credentials:
        logger.info("🔧 Development mode activated due to test/dummy credentials")
        return True
    
    # Method 4: Check for localhost/development environment indicators
    flask_env = os.getenv('FLASK_ENV', '').lower()
    if flask_env in ['development', 'dev', 'local']:
        logger.info(f"🔧 Development mode activated via FLASK_ENV={flask_env}")
        return True
    
    # Default: Production mode (safer default)
    return False