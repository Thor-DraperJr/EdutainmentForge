"""
Premium Feature Integration for EdutainmentForge
        # Check if premium voices are enabled
        premium_voices_enabled = os.getenv('USE_PREMIUM_VOICES', 'false').lower() == 'true'
        
        if premium_voices_enabled:
            try:
                # Use the standard multi-voice TTS with premium voice support
                from audio.multivoice_tts import MultiVoiceTTSService
                availability['neural_voices'] = True
                logger.info("✅ Premium neural voices available")
            except ImportError as e:
                logger.warning(f"Premium neural voices not available: {e}")
        else:
            # Standard voices are always available
            try:
                from audio.multivoice_tts import MultiVoiceTTSService
                availability['neural_voices'] = True
                logger.info("✅ Standard neural voices available")
            except ImportError as e:
                logger.warning(f"Neural voices not available: {e}")egration system that conditionally uses premium features when available
and configured, falling back to standard features gracefully.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from utils.logger import get_logger
from utils.config import load_config

logger = get_logger(__name__)

class PremiumFeatureManager:
    """Manages premium feature availability and configuration."""
    
    def __init__(self):
        """Initialize premium feature manager."""
        self.config = load_config()
        self._premium_available = self._check_premium_availability()
        
    def _check_premium_availability(self) -> Dict[str, bool]:
        """Check what premium features are available and configured."""
        availability = {
            'ai_enhancement': False,
            'neural_voices': False,
            'advanced_processing': False
        }
        
        # Check if premium AI is enabled
        premium_ai_enabled = os.getenv('USE_PREMIUM_AI', 'false').lower() == 'true'
        gpt4_available = os.getenv('AZURE_OPENAI_GPT4_DEPLOYMENT_NAME') is not None
        
        if premium_ai_enabled and gpt4_available:
            try:
                # Use the upgraded original AI enhancer instead of the complex premium one
                from content.ai_enhancer import AIScriptEnhancer
                availability['ai_enhancement'] = True
                logger.info("✅ Premium AI enhancement available")
            except ImportError as e:
                logger.warning(f"Premium AI enhancement not available: {e}")
        else:
            # Standard AI enhancement is always available
            try:
                from content.ai_enhancer import AIScriptEnhancer
                availability['ai_enhancement'] = True
                logger.info("✅ Standard AI enhancement available")
            except ImportError as e:
                logger.warning(f"AI enhancement not available: {e}")
        
        # Check if premium voices are enabled
        premium_voices_enabled = os.getenv('USE_PREMIUM_VOICES', 'false').lower() == 'true'
        
        if premium_voices_enabled:
            try:
                from audio.premium_multivoice_tts import PremiumMultiVoiceTTSService
                availability['neural_voices'] = True
                logger.info("✅ Premium neural voices available")
            except ImportError as e:
                logger.warning(f"Premium voices not available: {e}")
        
        # Advanced processing available if either premium feature is available
        availability['advanced_processing'] = (
            availability['ai_enhancement'] or 
            availability['neural_voices']
        )
        
        return availability
    
    def is_available(self, feature: str) -> bool:
        """Check if a specific premium feature is available."""
        return self._premium_available.get(feature, False)
    
    def get_ai_enhancer(self):
        """Get the upgraded AI enhancer with smart model selection."""
        try:
            from content.ai_enhancer import AIScriptEnhancer
            enhancer = AIScriptEnhancer()
            
            # Check if premium models are available
            if self.is_available('ai_enhancement'):
                logger.info("🚀 Using Premium AI Enhancer (GPT-4)")
            else:
                logger.info("📝 Using Standard AI Enhancer (GPT-4o-mini)")
            
            return enhancer
        except Exception as e:
            logger.warning(f"AI enhancement not available: {e}")
            return None
    
    def get_multivoice_tts_service(self, config: Dict):
        """Get the multi-voice TTS service (now with premium neural voice support)."""
        from audio.multivoice_tts import create_multivoice_tts_service
        
        if self.is_available('neural_voices'):
            logger.info("🎤 Using Premium Multi-Voice TTS (Neural Voices)")
        else:
            logger.info("🔊 Using Standard Multi-Voice TTS")
        
        return create_multivoice_tts_service(config)
    
    def get_feature_summary(self) -> Dict[str, Any]:
        """Get a summary of available premium features."""
        return {
            'premium_available': any(self._premium_available.values()),
            'features': self._premium_available,
            'config': {
                'premium_ai_enabled': os.getenv('USE_PREMIUM_AI', 'false'),
                'premium_voices_enabled': os.getenv('USE_PREMIUM_VOICES', 'false'),
                'gpt4_deployment': os.getenv('AZURE_OPENAI_GPT4_DEPLOYMENT_NAME')
            }
        }


# Global instance for easy access
_premium_manager = None

def get_premium_manager() -> PremiumFeatureManager:
    """Get the global premium feature manager instance."""
    global _premium_manager
    if _premium_manager is None:
        _premium_manager = PremiumFeatureManager()
    return _premium_manager

def is_premium_available(feature: str) -> bool:
    """Quick check if a premium feature is available."""
    return get_premium_manager().is_available(feature)

def get_best_ai_enhancer():
    """Get the best available AI enhancer."""
    return get_premium_manager().get_ai_enhancer()

def get_best_multivoice_tts_service(config: Dict):
    """Get the best available multi-voice TTS service."""
    return get_premium_manager().get_multivoice_tts_service(config)

def get_premium_services():
    """Get both AI enhancer and TTS service - main entry point for premium features."""
    manager = get_premium_manager()
    
    # Get the upgraded AI enhancer (with smart model selection)
    ai_enhancer = manager.get_ai_enhancer()
    
    # Get the best available TTS service
    config = load_config()
    tts_service = manager.get_multivoice_tts_service(config)
    
    return ai_enhancer, tts_service

def print_feature_status():
    """Print current premium feature status."""
    manager = get_premium_manager()
    summary = manager.get_feature_summary()
    
    print("\n🎯 EdutainmentForge Premium Features Status:")
    print("=" * 50)
    
    if summary['premium_available']:
        print("✅ Premium features are available!")
    else:
        print("📝 Using standard features (premium features not configured)")
    
    print(f"\n🤖 AI Enhancement: {'✅ Premium (GPT-4)' if summary['features']['ai_enhancement'] else '📝 Standard (GPT-4o-mini)' if summary['config']['premium_ai_enabled'] != 'false' else '❌ Disabled'}")
    print(f"🎤 Neural Voices: {'✅ Premium' if summary['features']['neural_voices'] else '📝 Standard'}")
    print(f"⚡ Advanced Processing: {'✅ Available' if summary['features']['advanced_processing'] else '📝 Standard'}")
    
    print(f"\n📊 Configuration:")
    print(f"  • Premium AI: {summary['config']['premium_ai_enabled']}")
    print(f"  • Premium Voices: {summary['config']['premium_voices_enabled']}")
    print(f"  • GPT-4 Deployment: {summary['config']['gpt4_deployment'] or 'Not configured'}")
    
    print("=" * 50)
