#!/usr/bin/env python3
"""
Comprehensive test script for EdutainmentForge AI enhancement features.
Tests both the regular script generation and AI-enhanced version.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from content.processor import PodcastContentProcessor
from content.ai_enhancer import AIScriptEnhancer
from utils.config import load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def test_ai_enhancement():
    """Test the AI enhancement functionality."""
    print("🤖 Testing AI Enhancement Functionality")
    print("=" * 50)
    
    try:
        # Load configuration
        config = load_config()
        print(f"✅ Configuration loaded successfully")
        
        # Check AI configuration
        ai_endpoint = config.get("azure_openai_endpoint")
        ai_key = config.get("azure_openai_api_key")
        
        if not ai_endpoint or not ai_key:
            print("⚠️  Azure OpenAI not configured - AI enhancement will be disabled")
            print("   To enable AI enhancement, set these environment variables:")
            print("   - AZURE_OPENAI_ENDPOINT")
            print("   - AZURE_OPENAI_API_KEY")
            print("   - AZURE_OPENAI_DEPLOYMENT_NAME (optional)")
            return False
        
        print(f"✅ Azure OpenAI configured: {ai_endpoint}")
        
        # Test AI enhancer directly
        enhancer = AIScriptEnhancer()
        if not enhancer.client:
            print("❌ Failed to initialize Azure OpenAI client")
            return False
        
        print("✅ Azure OpenAI client initialized successfully")
        
        # Test with sample script
        sample_script = """
Sarah: Welcome to EdutainmentForge! I'm Sarah.
Mike: And I'm Mike. Today we're covering Azure roles and permissions.
Sarah: Let's start with the basics. Azure roles control access to Azure resources like virtual machines and storage accounts.
Mike: That's right, Sarah. There are different types of roles with different scopes.
Sarah: Azure roles can be applied at multiple levels like management groups, subscriptions, and resource groups.
Mike: Yes, and Microsoft Entra roles are typically at the tenant level.
Sarah: Thanks for joining us today, everyone!
Mike: Keep learning and exploring!
"""
        
        print("\n🔧 Testing AI script enhancement...")
        try:
            enhanced_script = enhancer.enhance_script(sample_script, "Azure Roles and Permissions")
            print("✅ AI enhancement successful!")
            print(f"📝 Enhanced script length: {len(enhanced_script)} characters")
            print(f"📈 Original script length: {len(sample_script)} characters")
            
            # Save enhanced script for review
            output_file = Path("output") / "ai_enhancement_test.txt"
            output_file.parent.mkdir(exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== AI ENHANCED SCRIPT ===\n\n")
                f.write(enhanced_script)
                f.write("\n\n=== ORIGINAL SCRIPT ===\n\n")
                f.write(sample_script)
            
            print(f"📄 Enhanced script saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ AI enhancement failed: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_processor_integration():
    """Test the full processor integration with AI enhancement."""
    print("\n🔧 Testing Processor Integration")
    print("=" * 50)
    
    try:
        # Test with AI enhancement enabled
        processor = PodcastContentProcessor(use_ai_enhancement=True)
        
        if processor.ai_enhancer:
            print("✅ Processor initialized with AI enhancement enabled")
        else:
            print("⚠️  Processor initialized but AI enhancement is disabled")
            return False
        
        # Test with sample content
        sample_content = {
            'title': 'Azure Security Best Practices',
            'content': 'Azure security involves multiple layers including network security, identity management, and data protection. Network security groups control traffic flow. Azure Active Directory manages user identities. Data encryption protects sensitive information both at rest and in transit.'
        }
        
        print("\n📝 Generating podcast script with AI enhancement...")
        script = processor.create_podcast_script(sample_content)
        
        if script and len(script) > 100:
            print("✅ AI-enhanced script generated successfully!")
            print(f"📝 Script length: {len(script)} characters")
            
            # Save test script
            output_file = Path("output") / "processor_ai_test_script.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(script)
            
            print(f"📄 Script saved to: {output_file}")
            return True
        else:
            print("❌ Script generation failed or produced empty result")
            return False
    
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 EdutainmentForge AI Enhancement Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test AI enhancement
    results.append(test_ai_enhancement())
    
    # Test processor integration
    results.append(test_processor_integration())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✅ All tests passed! ({success_count}/{total_count})")
        print("🎉 AI enhancement is ready for production!")
    else:
        print(f"⚠️  {total_count - success_count} test(s) failed ({success_count}/{total_count})")
        print("🔧 Check configuration and Azure OpenAI setup")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
