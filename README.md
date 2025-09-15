# EdutainmentForge 🎙️

> *"What if learning Azure could feel like listening to your favorite tech podcast?"*

**Transform Microsoft Learn content into engaging educational podcasts with AI-enhanced multi-voice narration**

Born from my own struggles as an auditory learner drowning in walls of technical documentation, EdutainmentForge represents a complete rethinking of how we consume complex technical content. This isn't just another TTS tool—it's a sophisticated AI system that understands content structure, generates natural dialogue, and creates truly engaging learning experiences.

🚀 **Live Demo**: [Try it now on Azure Container Apps](https://edutainmentforge-app.happymeadow-088e7533.eastus.azurecontainerapps.io/)

## ✨ What Makes This Special

**🧠 Smart Content Intelligence**: Automatically discovers and processes entire Microsoft certification paths using live API integration—no more manual URL hunting

**🎭 AI-Driven Dialogue**: GPT-4o transforms dry documentation into natural conversations between Sarah and Mike, our AI podcast hosts

**🎙️ Premium Voice Synthesis**: Azure Neural TTS with custom SSML styling creates podcast-quality audio that doesn't sound robotic

**⚡ Production-Ready Architecture**: Built with enterprise patterns—managed identity auth, Key Vault secrets, Container Apps deployment, and smart caching

## 🎯 The Technical Journey

This project pushed me to solve fascinating engineering challenges:

- **API Integration Mastery**: Reverse-engineered Microsoft Learn's catalog structure to build scalable content discovery
- **Multi-Service Orchestration**: Seamlessly coordinated Azure OpenAI and Speech Services into a unified experience
- **Content Structure Understanding**: Built intelligent parsers that recognize tables, code blocks, and technical hierarchies
- **Enterprise Security**: Implemented zero-credential deployments with managed identity and Key Vault integration

## 🚀 Recent Engineering Wins

**Live API Integration**: Just completed a major overhaul that connects directly to Microsoft Learn's catalog API. No more manual URL hunting—the system now auto-discovers entire certification paths and keeps content fresh.

**Multi-Voice Intelligence**: Cracked the code on making AI conversations actually sound natural. Sarah and Mike don't just alternate lines—they have personalities, ask each other questions, and build on each other's explanations.

**Zero-Credential Deployment**: Implemented true enterprise security with managed identity and Key Vault integration. The production system has zero hardcoded secrets.

## 🎧 How It Works

1. **Content Discovery** → Browse Microsoft's entire learning catalog or paste any Learn URL
2. **AI Enhancement** → GPT-4o analyzes structure and creates natural dialogue between hosts
3. **Voice Synthesis** → Premium Azure Neural voices bring the conversation to life
4. **Smart Caching** → Never regenerate the same content twice

Perfect for commutes, workouts, or any time you want to absorb Azure knowledge without staring at a screen.

## 🛠️ Quick Start

```bash
# Clone and setup
git clone https://github.com/Thor-DraperJr/EdutainmentForge.git
cd EdutainmentForge
pip install -r requirements.txt

# Copy the provided sample env file (already named .env in repo template) and edit values
# (This file is ignored by git when containing real secrets.)

# Run the app
python app.py
```

Visit `http://localhost:5000` and start exploring Microsoft Learn content in a whole new way!

## 🎯 Technical Stack

- **Azure OpenAI**: GPT-4o for intelligent dialogue generation
- **Azure Speech**: Premium neural voices (Emma & Davis)
- **Python/Flask**: Core application with clean architecture
- **Azure Container Apps**: Production deployment platform
- **Key Vault**: Enterprise secret management

## 🤝 Contributing

Found a bug? Have an idea? I'd love your input! This project represents my journey in AI systems engineering, and I'm always excited to learn from the community.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
