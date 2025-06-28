#!/usr/bin/env python3
"""
Test script for Azure deployment of EdutainmentForge.
This script tests the Container App with Azure Speech Service integration.
"""

import requests
import time
import json
from urllib.parse import urljoin

# Azure Container App URL
BASE_URL = "https://edutainmentforge-app.happymeadow-088e7533.eastus.azurecontainerapps.io"

def test_app_health():
    """Test if the application is responding."""
    try:
        response = requests.get(BASE_URL, timeout=30)
        if response.status_code == 200:
            print("✅ Application is responding")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to application: {e}")
        return False

def test_process_url():
    """Test URL processing with a sample Microsoft Learn URL."""
    test_url = "https://docs.microsoft.com/en-us/learn/modules/intro-to-azure-fundamentals/"
    
    try:
        # Submit URL for processing
        response = requests.post(
            urljoin(BASE_URL, "/api/process"), 
            json={"url": test_url},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ URL processing started. Task ID: {task_id}")
            
            # Monitor processing status
            for i in range(30):  # Wait up to 5 minutes
                status_response = requests.get(
                    urljoin(BASE_URL, f"/api/status/{task_id}"),
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    message = status_data.get('message', '')
                    
                    print(f"Status: {status} ({progress}%) - {message}")
                    
                    if status == 'completed':
                        print("✅ Processing completed successfully!")
                        print(f"Audio file: {status_data.get('audio_file')}")
                        print(f"Script file: {status_data.get('script_file')}")
                        return True
                    elif status == 'error':
                        print(f"❌ Processing failed: {message}")
                        return False
                    
                    time.sleep(10)  # Wait 10 seconds before checking again
                else:
                    print(f"❌ Failed to get status: {status_response.status_code}")
                    return False
            
            print("⏰ Processing timed out")
            return False
        else:
            print(f"❌ Failed to submit URL: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to test URL processing: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing EdutainmentForge Azure Deployment")
    print("=" * 50)
    
    # Test 1: Application health
    print("\n1. Testing application health...")
    if not test_app_health():
        print("❌ Application health check failed. Exiting.")
        return
    
    # Test 2: URL processing (commented out for now as it takes time)
    print("\n2. Testing URL processing...")
    print("⚠️  Note: This test will take several minutes to complete")
    
    user_input = input("Do you want to test URL processing? (y/n): ")
    if user_input.lower() == 'y':
        test_process_url()
    else:
        print("⏭️  Skipping URL processing test")
    
    print("\n✅ Testing complete!")
    print(f"🌐 Application URL: {BASE_URL}")

if __name__ == "__main__":
    main()
