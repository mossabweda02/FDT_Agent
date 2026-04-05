<div align="center">
    <h1>FDT Agent - AI-Powered Timesheet Analytics</h1>
    <p>Autonomous agent for intelligent timesheet analysis and business intelligence on Azure Synapse</p>
    <br />
    <p align="center">
    <a href="README.fr.md">
        <img src="https://img.shields.io/badge/lang-fr-blue.svg" alt="Français" />
    </a>
    <a href="README.md">
        <img src="https://img.shields.io/badge/lang-en-red.svg" alt="English" />
    </a>
    </p>
    <br />
    <p align="center">
    <a href="https://github.com/mossabweda02/FDT_Agent/actions" target="_blank">
        <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/blob/main/LICENSE" target="_blank">
        <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/pulls" target="_blank">
        <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/issues" target="_blank">
        <img src="https://img.shields.io/badge/Issues-open-brightgreen.svg" alt="Open Issues" />
    </a>
    </p>
</div>

---

## ⚠️ Important Notice

This project is under active development and may contain breaking changes. It requires Azure credentials and Synapse access to function.

---

## 🎯 FDT Agent - The Vision

FDT Agent is an **autonomous AI system** that transforms natural language questions into intelligent timesheet analytics. Using Azure AI Services and Azure Synapse Analytics, it automatically discovers your data schema, generates optimized SQL queries, and delivers insights without requiring technical SQL knowledge.

Ask questions in French, get answers in seconds.

### Key Capabilities
- 💬 **Natural Language Queries**: Ask in French, get instant SQL-backed results
- 🧠 **Schema Discovery**: Automatic database structure learning
- ⚡ **Async-First**: Non-blocking, high-concurrency architecture
- 🔒 **Enterprise Security**: Azure AD integration, parameterized queries
- 🔧 **Modular Design**: Extensible tool system for custom analytics

---

## 🌟 Features

- **Natural Language Querying** - Plain French questions become SQL queries automatically
- **Schema Auto-Discovery** - Agent learns your database structure without configuration
- **French-First Design** - Prompts, responses, and documentation in French
- **Azure Integration** - Native Synapse Analytics and Azure AI Agent support
- **Async Architecture** - High-performance, non-blocking I/O
- **Secure by Default** - Parameterized queries, no SQL injection vulnerabilities
- **Extensible Tools** - Add custom functions for domain-specific analytics

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Azure CLI** installed: `az login`
- **ODBC Driver 18 for SQL Server** (system dependency)
- **Azure Credentials**: Access to Synapse SilverLayer database
- **Azure AI Project**: Agent runtime configured

### Installation

```bash
# Clone repository
git clone https://github.com/mossabweda02/FDT_Agent.git
cd FDT_Agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your Azure credentials
```

### Your First Query

```bash
# Test database connection
python test_data.py

# Start the agent
python agent/fdt_agent.py

# Ask questions in French:
# "Quels sont les projets avec plus de 1000 heures?"
# "Combien de ressources travaillent sur le projet PRJ-00329?"
```

---

## 📁 Project Structure

```
FDT_Agent/
├── agent/
│   ├── create_agent.py      # Agent initialization & tool setup
│   └── fdt_agent.py         # Main agent runtime loop
├── core/
│   ├── prompts.py           # System prompts & domain knowledge
│   └── exceptions.py        # Custom exception classes
├── database/
│   └── connection.py        # Azure Synapse connectivity
├── tools/
│   ├── functions_tools.py   # SQL query tools (list_tables, execute_query, etc.)
│   └── tools_runner.py      # Tool dispatcher & executor
├── update_agent.py          # Agent update utility script
├── requirements.txt         # Python dependencies
├── test_data.py            # Database connection tester
├── README.md               # This file (English)
└── README.fr.md            # French documentation
```

---

## � Agent Updates

### Automatic Agent Synchronization

When you modify the agent's behavior by changing:

- **`core/prompts.py`** - System instructions and domain knowledge
- **`tools/functions_tools.py`** - Available tools and functions

You need to update the agent in Azure Foundry to reflect these changes:

#### Quick Update (Recommended)
```bash
python update_agent.py
```

#### Manual Update
```bash
python agent/create_agent.py update
```

#### What Gets Updated
- **Instructions**: Latest system prompt from `core/prompts.py`
- **Tools**: Latest tool definitions from the code
- **Agent ID**: Uses `AGENT_ID` from your `.env` file

#### When to Update
- ✅ After modifying prompts or system instructions
- ✅ After adding/removing/changing tools
- ✅ After updating domain knowledge or schemas
- ❌ Not needed for code refactoring (unless it affects tool definitions)

---

## �🛠️ Development

### Setup Development Environment

```bash
# Install in development mode
pip install -e .

# Optional: Install dev dependencies
pip install pytest black flake8 mypy
```

### Common Commands

```bash
# Run database tests
python test_data.py

# Launch agent (interactive)
python agent/fdt_agent.py

# Quick test
python -c "from database.connection import get_engine; print('✅ Database connected')"
```

### Debugging

```bash
# Check environment
python -c "import os; print(os.getenv('AGENT_ID', 'NOT SET'))"

# Verify dependencies
pip list | grep azure

# Test Azure credentials
az account show
```

---

## 📋 Essential Commands

### Environment Setup
```bash
python -m venv venv               # Create environment
venv\Scripts\activate              # Activate (Windows)
pip install -r requirements.txt    # Install dependencies
```

### Configuration
```bash
copy .env.example .env             # Create config
# Edit .env with:
# AZURE_AI_PROJECT_ENDPOINT=...
# AGENT_ID=...
# AZURE_USERNAME=...
# AZURE_PASSWORD=...
```

### Usage
```bash
python test_data.py                # Test connection
python agent/fdt_agent.py          # Run agent
python update_agent.py             # Update agent after code changes
```

### Update Agent After Changes
When you modify `core/prompts.py` or `tools/functions_tools.py`, update the agent in Azure Foundry:

```bash
# Quick update
python update_agent.py

# Or use the create_agent script
python agent/create_agent.py update
```

### Code Example
```python
import asyncio
from agent.fdt_agent import ask

async def main():
    result = await ask("Quels projets dépassent 500 heures?")
    print(result)

asyncio.run(main())
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```bash
# Azure AI Agent
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com
AGENT_ID=agent-xxxxxxxxxxxxx

# Azure Synapse
AZURE_USERNAME=your-username@domain.com
AZURE_PASSWORD=your-secure-password
SYNAPSE_DATABASE=SilverLayer

# Performance (optional)
QUERY_TIMEOUT_SECONDS=300
```

### Database Connection

Edit `database/connection.py` to customize:
- Connection pool size
- Query timeouts
- SSL/TLS settings
- Proxy configuration

---

## 🤝 Contributing

We welcome contributions! Here's how:

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
python test_data.py

# Commit with clear message
git commit -m "feat: add new capability"

# Push to GitHub
git push origin feature/your-feature

# Open Pull Request
```

### Guidelines
- Follow PEP 8 style guide
- Add docstrings to functions
- Test new features
- Update documentation
- Keep commits focused

---

## 📚 Documentation

- [Setup Guide](docs/setup.md)
- [API Reference](docs/api.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Architecture](docs/architecture.md)

---

## ❓ Troubleshooting

### Connection Issues
```bash
# Verify Azure credentials
az login
az account show

# Check database connectivity
python test_data.py
```

### Agent Errors
```bash
# Verify environment variables
python -c "import os; print(os.getenv('AGENT_ID'))"

# Check dependencies
pip list | grep azure
```

### Query Timeouts
Edit `database/connection.py`:
```python
Connection Timeout=600  # Increase from 300 seconds
```

---

## 💬 Community & Support

- **Issues**: [GitHub Issues](https://github.com/mossabweda02/FDT_Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mossabweda02/FDT_Agent/discussions)
- **Email**: support@fdt.io

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
- [Azure Synapse Analytics](https://azure.microsoft.com/en-us/services/synapse-analytics/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- Open source community