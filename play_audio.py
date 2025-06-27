#!/usr/bin/env python3
"""
Simple audio player for EdutainmentForge podcasts.
"""

import os
import sys
import subprocess
from pathlib import Path

def list_audio_files():
    """List all available audio files."""
    output_dir = Path("output")
    audio_files = []
    
    # Find WAV files
    if output_dir.exists():
        for file in output_dir.glob("*.wav"):
            size = file.stat().st_size
            audio_files.append((file.name, size))
    
    # Also check voice demos
    demo_dir = output_dir / "voice_demos"
    if demo_dir.exists():
        for file in demo_dir.glob("*.wav"):
            size = file.stat().st_size
            audio_files.append((f"voice_demos/{file.name}", size))
    
    return sorted(audio_files)

def play_audio(file_path):
    """Play audio file using available system tools."""
    file_path = Path("output") / file_path
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"🎵 Playing: {file_path.name}")
    print(f"📊 Size: {file_path.stat().st_size:,} bytes")
    print("🎧 Use Ctrl+C to stop playback")
    
    # Try different audio players
    players = [
        ['paplay', str(file_path)],
        ['aplay', str(file_path)],
        ['ffplay', '-nodisp', str(file_path)],
        ['vlc', '--intf', 'dummy', str(file_path)],
        ['mpv', '--no-video', str(file_path)]
    ]
    
    for player_cmd in players:
        try:
            # Check if player is available
            subprocess.run(['which', player_cmd[0]], 
                         check=True, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            
            # Play the audio
            print(f"▶️  Using {player_cmd[0]}...")
            subprocess.run(player_cmd, check=True)
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("❌ No suitable audio player found.")
    print("💡 Try installing: sudo apt install pulseaudio-utils")
    return False

def main():
    """Main audio player interface."""
    print("🎙️  EdutainmentForge Audio Player")
    print("=" * 50)
    
    # List available files
    audio_files = list_audio_files()
    
    if not audio_files:
        print("❌ No audio files found in output/")
        print("💡 Generate some podcasts first using podcast_cli.py")
        return
    
    print("📻 Available audio files:")
    for i, (filename, size) in enumerate(audio_files, 1):
        size_mb = size / (1024 * 1024)
        print(f"   {i}. {filename} ({size_mb:.1f} MB)")
    
    # Get user choice
    try:
        while True:
            print(f"\n🎯 Enter file number (1-{len(audio_files)}) or 'q' to quit:")
            choice = input(">>> ").strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                break
            
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(audio_files):
                    filename = audio_files[file_index][0]
                    play_audio(filename)
                    print("\n✅ Playback finished.")
                else:
                    print(f"❌ Please enter a number between 1 and {len(audio_files)}")
            except ValueError:
                print("❌ Please enter a valid number or 'q'")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
