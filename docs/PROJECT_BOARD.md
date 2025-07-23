# GitHub Project Board for EdutainmentForge Hackathon

## 📋 Overview

This document outlines the GitHub Project Board setup for EdutainmentForge hackathon task tracking. The board provides visual project management with automated workflow integration.

## 🎯 Project Board Structure

### Columns

| Column | Purpose | Automation |
|--------|---------|------------|
| **Backlog** | New issues and planned features | ✅ Auto-populated when issues are created |
| **In Progress** | Active development work | ✅ Auto-populated when PRs are opened |
| **Review** | Code review and testing phase | 🔄 Manual movement or label-based |
| **Done** | Completed and merged work | ✅ Auto-populated when issues/PRs are closed |

### Labels and Automation

The project board uses automated workflows triggered by issue and PR activities:

- **New Issues** → Automatically added to **Backlog**
- **New Pull Requests** → Automatically added to **In Progress**
- **Closed Issues/PRs** → Automatically moved to **Done**

## 🚀 Getting Started

### Setting Up the Project Board

1. **Create the Project Board**:
   - Go to repository **Projects** tab
   - Click **New project**
   - Choose **Table** view
   - Name: "EdutainmentForge Hackathon"

2. **Configure Columns**:
   - Create columns: Backlog, In Progress, Review, Done
   - Set up column automation (see automation section below)

3. **Set Repository Variables**:
   - Add `PROJECT_URL` repository variable with your project board URL
   - Format: `https://github.com/users/USERNAME/projects/PROJECT_NUMBER`

### Using Issue Templates

When creating new issues, use the provided templates:

- **🚀 Feature Request**: For new functionality
- **🐛 Bug Report**: For bug fixes and issues
- **🎯 Hackathon Task**: For hackathon-specific work

All templates automatically apply appropriate labels for project board integration.

## 🔄 Workflow Integration

### Automated Actions

The `.github/workflows/project-board.yml` workflow handles:

```yaml
Triggers:
- Issue opened/reopened/closed
- PR opened/reopened/closed/merged

Actions:
- New issues → Backlog column
- New PRs → In Progress column
- Closed items → Done column
```

### Manual Workflow

For items that need manual movement:

1. **Backlog → In Progress**: Move when you start working on an issue
2. **In Progress → Review**: Move when PR is ready for review
3. **Review → Done**: Automated when PR is merged

## 📊 Project Board Labels

### Priority Labels
- `critical` - Must have for hackathon demo
- `high` - Important for demo quality
- `medium` - Nice to have
- `low` - Future enhancement

### Type Labels
- `enhancement` - New features
- `bug` - Bug fixes
- `hackathon` - Hackathon-specific tasks
- `documentation` - Documentation updates

### Status Labels
- `backlog` - In backlog column
- `in-progress` - Active development
- `review` - Code review needed
- `done` - Completed work

### Component Labels
- `audio` - Audio generation pipeline
- `ui` - Web interface
- `ms-learn` - Microsoft Learn integration
- `azure` - Azure services
- `api` - API development

## 🎮 Team Collaboration

### Best Practices

1. **Create Issues First**: Always create an issue before starting work
2. **Use Templates**: Use appropriate issue templates for consistency
3. **Link PRs to Issues**: Reference issues in PR descriptions (`Fixes #123`)
4. **Update Status**: Move cards manually when automation doesn't apply
5. **Add Comments**: Keep team updated with progress comments

### Hackathon Demo Preparation

Track demo-critical items:
- [ ] Core functionality working
- [ ] UI polished and presentable
- [ ] Azure services configured
- [ ] Documentation updated
- [ ] Demo script prepared

### Project Board Views

**Filter by Priority**:
- Critical items: `label:critical`
- Demo features: `label:hackathon`
- Bugs: `label:bug`

**Filter by Component**:
- Audio pipeline: `label:audio`
- UI work: `label:ui`
- Azure integration: `label:azure`

## 🔧 Troubleshooting

### Common Issues

**Automation not working**:
1. Check `PROJECT_URL` repository variable is set correctly
2. Verify workflow permissions in repository settings
3. Ensure project board is public or accessible to actions

**Items not moving automatically**:
1. Check issue/PR has correct labels
2. Verify automation rules in project board settings
3. Review GitHub Actions workflow logs

**Missing from project board**:
1. Items created before automation setup need manual addition
2. Use "Add items" in project board to include existing issues

### Getting Help

- Check [GitHub Projects documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- Review workflow logs in Actions tab
- Create issue with `documentation` label for board improvements

## 📈 Project Metrics

Track hackathon progress:
- **Velocity**: Issues completed per day
- **Burn-down**: Remaining work vs. time
- **Quality**: Bug reports vs. features
- **Demo Readiness**: Critical items completion rate

---

**Next Steps**: After setting up the project board, update the `PROJECT_URL` repository variable and test the automation with a sample issue.