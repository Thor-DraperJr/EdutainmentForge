# 🎯 Project Board Quick Reference

## Instant Setup Checklist

- [ ] **Create Project Board**: Go to repository Projects tab → New project → Table view
- [ ] **Set PROJECT_URL**: Add repository variable in Settings → Secrets and variables → Actions
- [ ] **Run Setup Script**: `./scripts/setup-project-board.sh`
- [ ] **Test Automation**: Create a sample issue to verify auto-labeling

## Project Board Columns

| Status | Description | How Items Get Here |
|--------|-------------|-------------------|
| 🗂️ **Backlog** | New issues, planned features | ✅ Auto: New issues |
| 🔄 **In Progress** | Active development | ✅ Auto: New PRs |
| 👀 **Review** | Code review, testing | 🔄 Manual: Ready for review |
| ✅ **Done** | Completed work | ✅ Auto: Closed issues/PRs |

## Issue Templates

| Template | When to Use | Auto Labels |
|----------|-------------|-------------|
| 🚀 **Feature Request** | New functionality | `enhancement`, `backlog` |
| 🐛 **Bug Report** | Bug fixes | `bug`, `backlog` |
| 🎯 **Hackathon Task** | Time-boxed work | `hackathon`, `backlog` |

## Smart Labels

### Priority (Auto-applied based on title)
- `critical` - [CRITICAL] or "critical" in title
- `high` - [HIGH] or "high" in title  
- `hackathon` - [HACKATHON] or "hackathon" in title

### Components (Auto-applied based on content)
- `audio` - Audio, TTS, Speech keywords
- `ui` - UI, Interface, Frontend keywords
- `azure` - Azure, Cloud keywords
- `api` - API, Endpoint keywords
- `ms-learn` - MS Learn, Microsoft Learn keywords

## Quick Commands

```bash
# Setup project board infrastructure
./scripts/setup-project-board.sh

# Test infrastructure is working
python scripts/test-project-board.py

# Create feature request issue
gh issue create --template feature_request.md

# Create hackathon task
gh issue create --template hackathon_task.md
```

## Automation Triggers

| Action | Result |
|--------|--------|
| Create issue | → Backlog column + auto-labels |
| Open PR | → In Progress column + `in-progress` label |
| Close issue/PR | → Done column + `done` label |
| Comment "ready for review" | → Adds `review` label |

## Project URLs

- **Project Board**: [Create here](https://github.com/Thor-DraperJr/EdutainmentForge/projects)
- **Documentation**: [docs/PROJECT_BOARD.md](docs/PROJECT_BOARD.md)
- **Issue Templates**: [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/)
- **Workflows**: [.github/workflows/](.github/workflows/)

---
**💡 Pro Tip**: Use descriptive titles with keywords for automatic categorization!