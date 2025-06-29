#!/usr/bin/env python3
"""
Simple test to generate fresh audio using the main app pipeline
"""

import sys
import os
import subprocess

def main():
    print("🎵 EdutainmentForge - Fresh Audio Test")
    print("=" * 50)
    
    url = "https://learn.microsoft.com/en-us/training/modules/explore-identity-azure-active-directory/14-explain-auditing-identity"
    
    print(f"🔄 Generating audio from: {url}")
    print("📥 Using main app pipeline...")
    
    try:
        # Use the main app.py to generate audio
        result = subprocess.run([
            sys.executable, "app.py", 
            "--url", url,
            "--output", "output/fresh_aad_auditing_test.wav"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            output_file = "output/fresh_aad_auditing_test.wav"
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ Audio generated successfully!")
                print(f"📁 File: {output_file}")
                print(f"📊 Size: {file_size / 1024:.1f} KB")
                print("\n🎧 You can now listen to the generated audio file.")
                return True
            else:
                print("❌ Audio file was not created")
                
        print("❌ App execution failed:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Process timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("=" * 50)
    if not success:
        print("❌ Test failed!")
        sys.exit(1)
