#!/usr/bin/env python3
"""
Cost monitoring script for EdutainmentForge premium services.

Tracks usage and costs across Azure OpenAI and Speech Services.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("⚠ Azure SDK not available. Install with: pip install azure-mgmt-cognitiveservices azure-mgmt-monitor")

from utils.config import load_config
from utils.logger import get_logger


logger = get_logger(__name__)


class CostMonitor:
    """Monitor costs and usage for Azure AI services."""
    
    def __init__(self):
        """Initialize cost monitor."""
        self.config = load_config()
        if AZURE_AVAILABLE:
            self.credential = DefaultAzureCredential()
            self.subscription_id = self._get_subscription_id()
        
    def _get_subscription_id(self) -> str:
        """Get Azure subscription ID from environment or config."""
        # Try to get from environment first
        sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if sub_id:
            return sub_id
        
        # Try to get from Azure CLI
        try:
            import subprocess
            result = subprocess.run(
                ["az", "account", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not get subscription ID: {e}")
        
        raise ValueError("Azure subscription ID not found. Set AZURE_SUBSCRIPTION_ID environment variable.")
    
    def get_openai_usage(self, days: int = 30) -> dict:
        """Get Azure OpenAI usage and cost estimates."""
        if not AZURE_AVAILABLE:
            return {"error": "Azure SDK not available"}
        
        try:
            # This is a simplified version - real implementation would use Azure Monitor API
            usage_data = {
                "service": "Azure OpenAI",
                "period_days": days,
                "estimated_tokens": 0,
                "estimated_cost": 0.0,
                "models_used": ["gpt-4o-mini"],
                "recommendations": []
            }
            
            # Check if premium models are configured
            gpt4_deployment = self.config.get("azure_openai_gpt4_deployment")
            if gpt4_deployment:
                usage_data["models_used"].append("gpt-4")
                usage_data["recommendations"].append("GPT-4 is active - monitor token usage carefully")
            
            # Add cost optimization recommendations
            premium_enabled = self.config.get("premium_mode_enabled", "false").lower() == "true"
            if premium_enabled:
                usage_data["recommendations"].extend([
                    "Premium mode enabled - enhanced quality with higher costs",
                    "Consider using smart model selection to optimize costs",
                    "Monitor complex content detection to ensure GPT-4 is used efficiently"
                ])
            else:
                usage_data["recommendations"].append("Enable premium mode for better script quality")
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Failed to get OpenAI usage: {e}")
            return {"error": str(e)}
    
    def get_speech_usage(self, days: int = 30) -> dict:
        """Get Azure Speech Services usage and cost estimates."""
        if not AZURE_AVAILABLE:
            return {"error": "Azure SDK not available"}
        
        try:
            usage_data = {
                "service": "Azure Speech Services",
                "period_days": days,
                "estimated_characters": 0,
                "estimated_cost": 0.0,
                "voice_types": ["Standard Neural"],
                "recommendations": []
            }
            
            # Check for premium voice features
            neural_enabled = self.config.get("neural_voice_enabled", "false").lower() == "true"
            styles_enabled = self.config.get("voice_styles_enabled", "false").lower() == "true"
            
            if neural_enabled:
                usage_data["voice_types"].append("Premium Neural")
                usage_data["recommendations"].append("Neural voices enabled - higher quality at premium cost")
            
            if styles_enabled:
                usage_data["voice_types"].append("Neural with Styles")
                usage_data["recommendations"].append("Voice styles active - emotional expression enabled")
            
            # Add optimization recommendations
            usage_data["recommendations"].extend([
                "Implement segment caching to reduce repeat TTS calls",
                "Use smart content detection to optimize voice style selection",
                "Consider custom voices for unique podcast branding"
            ])
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Failed to get Speech usage: {e}")
            return {"error": str(e)}
    
    def generate_cost_report(self, days: int = 30) -> dict:
        """Generate comprehensive cost report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "services": {},
            "total_estimated_cost": 0.0,
            "optimization_recommendations": []
        }
        
        # Get usage for each service
        openai_usage = self.get_openai_usage(days)
        speech_usage = self.get_speech_usage(days)
        
        report["services"]["openai"] = openai_usage
        report["services"]["speech"] = speech_usage
        
        # Calculate total estimated cost
        if "estimated_cost" in openai_usage:
            report["total_estimated_cost"] += openai_usage["estimated_cost"]
        if "estimated_cost" in speech_usage:
            report["total_estimated_cost"] += speech_usage["estimated_cost"]
        
        # Compile optimization recommendations
        for service_data in report["services"].values():
            if "recommendations" in service_data:
                report["optimization_recommendations"].extend(service_data["recommendations"])
        
        # Add general recommendations
        report["optimization_recommendations"].extend([
            "Monitor usage weekly to avoid unexpected costs",
            "Use batch processing for multiple learning modules",
            "Implement content caching to reduce API calls",
            "Consider cost alerts in Azure Portal"
        ])
        
        return report
    
    def save_report(self, report: dict, filename: str = None):
        """Save cost report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_report_{timestamp}.json"
        
        report_path = Path("logs") / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Cost report saved to: {report_path}")
        return report_path


def main():
    """Main function for cost monitoring."""
    parser = argparse.ArgumentParser(description="Monitor EdutainmentForge Azure service costs")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")
    
    args = parser.parse_args()
    
    monitor = CostMonitor()
    report = monitor.generate_cost_report(args.days)
    
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        # Print summary
        print(f"\n🏷️  EdutainmentForge Cost Report ({args.days} days)")
        print("=" * 50)
        
        print(f"\n💰 Estimated Total Cost: ${report['total_estimated_cost']:.2f}")
        
        for service_name, service_data in report["services"].items():
            if "error" not in service_data:
                print(f"\n📊 {service_data['service']}:")
                if "estimated_cost" in service_data:
                    print(f"   Cost: ${service_data['estimated_cost']:.2f}")
                if "models_used" in service_data:
                    print(f"   Models: {', '.join(service_data['models_used'])}")
                if "voice_types" in service_data:
                    print(f"   Voices: {', '.join(service_data['voice_types'])}")
        
        print(f"\n💡 Optimization Recommendations:")
        for i, rec in enumerate(report["optimization_recommendations"][:5], 1):
            print(f"   {i}. {rec}")
        
        if len(report["optimization_recommendations"]) > 5:
            print(f"   ... and {len(report['optimization_recommendations']) - 5} more")
    
    if args.save:
        monitor.save_report(report)


if __name__ == "__main__":
    main()
