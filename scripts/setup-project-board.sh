#!/bin/bash

# EdutainmentForge Project Board Setup Script
# This script helps set up local development environment for project board integration

echo "🎯 EdutainmentForge Project Board Setup"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the EdutainmentForge repository root"
    exit 1
fi

echo "✅ Repository structure verified"

# Create local labels if they don't exist (requires gh CLI)
if command -v gh &> /dev/null; then
    echo "🏷️  Setting up project labels..."
    
    # Priority labels
    gh label create "critical" --description "Must have for hackathon demo" --color "d73a4a" --force
    gh label create "high" --description "Important for demo quality" --color "f85149" --force
    gh label create "medium" --description "Nice to have" --color "fb8500" --force
    gh label create "low" --description "Future enhancement" --color "0969da" --force
    
    # Status labels
    gh label create "backlog" --description "In backlog column" --color "d4d4d4" --force
    gh label create "in-progress" --description "Active development" --color "0052cc" --force
    gh label create "review" --description "Code review needed" --color "5319e7" --force
    gh label create "done" --description "Completed work" --color "1a7f37" --force
    
    # Component labels
    gh label create "audio" --description "Audio generation pipeline" --color "007700" --force
    gh label create "ui" --description "Web interface" --color "006b75" --force
    gh label create "ms-learn" --description "Microsoft Learn integration" --color "0366d6" --force
    gh label create "azure" --description "Azure services" --color "1f883d" --force
    gh label create "api" --description "API development" --color "8b5cf6" --force
    gh label create "hackathon" --description "Hackathon-specific tasks" --color "fbca04" --force
    
    echo "✅ Labels created successfully"
else
    echo "⚠️  GitHub CLI not found. Please install gh CLI and run 'gh auth login' to set up labels automatically"
    echo "   Or create labels manually in the GitHub web interface"
fi

# Check for project board URL environment variable
if [ -z "$PROJECT_URL" ]; then
    echo ""
    echo "📋 Project Board Configuration"
    echo "=============================="
    echo "⚠️  PROJECT_URL environment variable not set"
    echo ""
    echo "To enable full project board automation:"
    echo "1. Create a GitHub Project Board at: https://github.com/Thor-DraperJr/EdutainmentForge/projects"
    echo "2. Add PROJECT_URL as a repository variable with your project URL"
    echo "3. Format: https://github.com/users/USERNAME/projects/PROJECT_NUMBER"
    echo ""
else
    echo "✅ PROJECT_URL configured: $PROJECT_URL"
fi

# Verify workflow files
if [ -f ".github/workflows/project-board.yml" ] && [ -f ".github/workflows/enhanced-project-management.yml" ]; then
    echo "✅ Project board workflows configured"
else
    echo "❌ Project board workflows missing"
fi

# Verify issue templates
if [ -d ".github/ISSUE_TEMPLATE" ]; then
    template_count=$(ls .github/ISSUE_TEMPLATE/*.md 2>/dev/null | wc -l)
    echo "✅ Issue templates configured ($template_count templates)"
else
    echo "❌ Issue templates missing"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next Steps:"
echo "1. Create your GitHub Project Board (if not already created)"
echo "2. Set the PROJECT_URL repository variable"
echo "3. Test the automation by creating a sample issue"
echo "4. Review the project board documentation: docs/PROJECT_BOARD.md"
echo ""
echo "Happy hacking! 🚀"