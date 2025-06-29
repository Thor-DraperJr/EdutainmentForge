#!/usr/bin/env python3
"""
Final integration test for EdutainmentForge before deployment.
Tests all components including AI enhancement.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("🔧 Testing imports...")
    try:
        # Add src to path
        sys.path.append(str(Path(__file__).parent / "src"))
        
        # Test core imports
        from content.processor import ScriptProcessor
        from content.ai_enhancer import AIScriptEnhancer
        from utils.config import load_config
        from utils.logger import get_logger
        
        print("✅ All critical imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from utils.config import load_config
        
        config = load_config()
        
        # Check if basic config is loaded
        if not config:
            print("❌ Config loading failed")
            return False
        
        # Check Azure OpenAI config
        ai_configured = bool(config.get("azure_openai_endpoint") and config.get("azure_openai_api_key"))
        print(f"✅ Configuration loaded (AI: {'enabled' if ai_configured else 'disabled'})")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_ai_enhancer():
    """Test AI enhancer initialization."""
    print("🔧 Testing AI enhancer...")
    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from content.ai_enhancer import AIScriptEnhancer
        
        enhancer = AIScriptEnhancer()
        if enhancer.client:
            print("✅ AI enhancer initialized with OpenAI client")
        else:
            print("⚠️  AI enhancer initialized without OpenAI client (expected if not configured)")
        return True
    except Exception as e:
        print(f"❌ AI enhancer test failed: {e}")
        return False

def test_processor():
    """Test script processor."""
    print("🔧 Testing script processor...")
    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from content.processor import ScriptProcessor
        
        # Test with AI enhancement
        processor = ScriptProcessor(use_ai_enhancement=True)
        
        # Test basic script generation
        test_content = {
            'title': 'Test Content',
            'content': 'This is a test of the script processor functionality.'
        }
        
        result = processor.process_content_to_script(test_content)
        script = result.get('script', '')
        
        if script and len(script) > 10:
            print("✅ Script processor working correctly")
            return True
        else:
            print("❌ Script processor failed to generate content")
            return False
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("🔧 Testing file structure...")
    
    required_files = [
        "app.py",
        "podcast_cli.py",
        "requirements.txt",
        "Dockerfile",
        "src/content/ai_enhancer.py",
        "src/content/processor.py",
        "src/utils/config.py",
        ".env.example",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def main():
    """Run all tests."""
    print("🚀 EdutainmentForge Final Integration Test")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_imports,
        test_configuration,
        test_ai_enhancer,
        test_processor
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    success_count = sum(results)
    total_count = len(results)
    
    print("📊 Test Results Summary")
    print("=" * 30)
    
    if success_count == total_count:
        print(f"✅ All tests passed! ({success_count}/{total_count})")
        print("🎉 EdutainmentForge is ready for deployment!")
        return True
    else:
        print(f"⚠️  {total_count - success_count} test(s) failed ({success_count}/{total_count})")
        print("🔧 Please check the issues above before deploying")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
