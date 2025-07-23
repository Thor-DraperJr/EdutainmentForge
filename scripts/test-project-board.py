#!/usr/bin/env python3
"""
Project Board Integration Test

This script validates that the GitHub Project Board infrastructure is properly set up.
Run this after setting up the project board to ensure all components work correctly.
"""

import os
import yaml
import json
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report the result."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def validate_yaml_file(file_path, description):
    """Validate YAML file syntax."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print(f"✅ {description}: Valid YAML syntax")
        return True
    except Exception as e:
        print(f"❌ {description}: Invalid YAML - {e}")
        return False

def validate_workflow_structure(workflow_path):
    """Validate GitHub Actions workflow structure."""
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check for required keys (accounting for YAML 'on' being parsed as True)
        has_name = 'name' in workflow
        has_on = True in workflow or 'on' in workflow  # YAML parses 'on:' as True
        has_jobs = 'jobs' in workflow
        
        if not has_name:
            print(f"❌ Workflow missing 'name' key")
            return False
        if not has_on:
            print(f"❌ Workflow missing 'on' key") 
            return False
        if not has_jobs:
            print(f"❌ Workflow missing 'jobs' key")
            return False
        
        # Get the triggers (using True key since YAML parses 'on:' as True)
        triggers = workflow.get(True, workflow.get('on', {}))
        
        # Check for project board specific triggers
        if 'issues' in triggers and 'pull_request' in triggers:
            print(f"✅ Workflow has proper triggers for project board automation")
            return True
        else:
            print(f"⚠️  Workflow may be missing some project board triggers")
            return True  # Still return true as basic structure is valid
            
    except Exception as e:
        print(f"❌ Error validating workflow: {e}")
        return False

def main():
    """Main validation function."""
    print("🎯 EdutainmentForge Project Board Integration Test")
    print("=" * 55)
    
    success = True
    
    # Test 1: Check required files exist
    print("\n📁 File Existence Check:")
    files_to_check = [
        (".github/workflows/project-board.yml", "Basic project board workflow"),
        (".github/workflows/enhanced-project-management.yml", "Enhanced project management workflow"),
        (".github/ISSUE_TEMPLATE/feature_request.md", "Feature request template"),
        (".github/ISSUE_TEMPLATE/bug_report.md", "Bug report template"),
        (".github/ISSUE_TEMPLATE/hackathon_task.md", "Hackathon task template"),
        (".github/ISSUE_TEMPLATE/config.yml", "Issue template configuration"),
        (".github/pull_request_template.md", "Pull request template"),
        ("docs/PROJECT_BOARD.md", "Project board documentation"),
        ("scripts/setup-project-board.sh", "Setup script"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            success = False
    
    # Test 2: Validate YAML syntax
    print("\n📝 YAML Validation:")
    yaml_files = [
        (".github/workflows/project-board.yml", "Project board workflow"),
        (".github/workflows/enhanced-project-management.yml", "Enhanced workflow"),
        (".github/ISSUE_TEMPLATE/config.yml", "Issue template config"),
    ]
    
    for file_path, description in yaml_files:
        if Path(file_path).exists():
            if not validate_yaml_file(file_path, description):
                success = False
    
    # Test 3: Validate workflow structure
    print("\n⚙️  Workflow Structure Validation:")
    for workflow_path in [".github/workflows/project-board.yml", ".github/workflows/enhanced-project-management.yml"]:
        if Path(workflow_path).exists():
            print(f"Checking {workflow_path}...")
            if not validate_workflow_structure(workflow_path):
                success = False
    
    # Test 4: Check environment setup
    print("\n🔧 Environment Check:")
    project_url = os.environ.get('PROJECT_URL')
    if project_url:
        print(f"✅ PROJECT_URL environment variable set: {project_url}")
    else:
        print("⚠️  PROJECT_URL environment variable not set (required for automation)")
        print("   Set this as a repository variable in GitHub settings")
    
    # Test 5: Check setup script permissions
    print("\n🛠️  Setup Script Check:")
    setup_script = Path("scripts/setup-project-board.sh")
    if setup_script.exists():
        if os.access(setup_script, os.X_OK):
            print("✅ Setup script has execute permissions")
        else:
            print("⚠️  Setup script needs execute permissions (run: chmod +x scripts/setup-project-board.sh)")
    
    # Final results
    print("\n" + "=" * 55)
    if success:
        print("🎉 All tests passed! Project board infrastructure is ready.")
        print("\nNext steps:")
        print("1. Create GitHub Project Board in repository")
        print("2. Set PROJECT_URL repository variable")
        print("3. Test automation by creating a sample issue")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())