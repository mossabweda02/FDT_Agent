<div align="center">
    <h1>FDT Agent - Analyseur IA de Feuilles de Temps</h1>
    <p>Agent autonome pour l'analyse intelligente des feuilles de temps et le business intelligence sur Azure Synapse</p>
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
        <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Version Python" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/blob/main/LICENSE" target="_blank">
        <img src="https://img.shields.io/badge/licence-MIT-blue.svg" alt="Licence" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/pulls" target="_blank">
        <img src="https://img.shields.io/badge/PRs-bienvenues-brightgreen.svg" alt="PRs Bienvenues" />
    </a>
    <a href="https://github.com/mossabweda02/FDT_Agent/issues" target="_blank">
        <img src="https://img.shields.io/badge/Issues-ouvertes-brightgreen.svg" alt="Issues Ouvertes" />
    </a>
    </p>
</div>

---

## ⚠️ Avis Important

Ce projet est en développement actif et peut contenir des changements majeurs. Il nécessite des identifiants Azure et un accès Synapse pour fonctionner.

---

## 🎯 FDT Agent - La Vision

FDT Agent est un **système IA autonome** qui transforme les questions en langage naturel en analyses intelligentes de feuilles de temps. Utilisant Azure AI Services et Azure Synapse Analytics, il découvre automatiquement votre schéma de données, génère des requêtes SQL optimisées, et fournit des insights sans nécessiter de connaissances techniques en SQL.

Posez des questions en français, obtenez des réponses en secondes.

### Capacités Clés
- 💬 **Requêtes en Langage Naturel** : Posez en français, obtenez des résultats SQL instantanés
- 🧠 **Découverte de Schéma** : Apprentissage automatique de la structure de base de données
- ⚡ **Architecture Async-First** : Architecture non-bloquante haute-concurrence
- 🔒 **Sécurité Entreprise** : Intégration Azure AD, requêtes paramétrées
- 🔧 **Design Modulaire** : Système d'outils extensible pour analyses personnalisées

---

## 🌟 Fonctionnalités

- **Requêtes en Langage Naturel** - Questions françaises simples deviennent automatiquement des requêtes SQL
- **Auto-Découverte de Schéma** - L'agent apprend votre structure de base de données sans configuration
- **Design Français-First** - Prompts, réponses et documentation en français
- **Intégration Azure** - Support natif Synapse Analytics et Azure AI Agent
- **Architecture Asynchrone** - E/S haute-performance non-bloquantes
- **Sécurisé par Défaut** - Requêtes paramétrées, pas de vulnérabilités SQL injection
- **Outils Extensibles** - Ajoutez des fonctions personnalisées pour analyses métier spécifiques

---

## 🚀 Démarrage Rapide

### Prérequis

- **Python 3.10+**
- **Azure CLI** installé : `az login`
- **ODBC Driver 18 for SQL Server** (dépendance système)
- **Identifiants Azure** : Accès à la base SilverLayer Synapse
- **Projet Azure AI** : Runtime agent configuré

### Installation

```bash
# Cloner le repository
git clone https://github.com/mossabweda02/FDT_Agent.git
cd FDT_Agent

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
copy .env.example .env
# Éditer .env avec vos identifiants Azure
```

### Votre Première Requête

```bash
# Tester la connexion à la base de données
python test_data.py

# Démarrer l'agent
python agent/fdt_agent.py

# Posez des questions en français :
# "Quels sont les projets avec plus de 1000 heures ?"
# "Combien de ressources travaillent sur le projet PRJ-00329 ?"
```

---

## 📁 Structure du Projet

```
FDT_Agent/
├── agent/
│   ├── create_agent.py      # Initialisation et configuration des outils de l'agent
│   └── fdt_agent.py         # Boucle principale d'exécution de l'agent
├── core/
│   ├── prompts.py           # Prompts système et connaissances métier
│   └── exceptions.py        # Classes d'exceptions personnalisées
├── database/
│   └── connection.py        # Connectivité Azure Synapse
├── tools/
│   ├── functions_tools.py   # Outils de requêtes SQL (list_tables, execute_query, etc.)
│   └── tools_runner.py      # Dispatcher et exécuteur d'outils
├── update_agent.py          # Script utilitaire de mise à jour de l'agent
├── requirements.txt         # Dépendances Python
├── test_data.py            # Testeur de connexion base de données
├── README.md               # Documentation anglaise
└── README.fr.md            # Ce fichier (Français)
```

---

## � Mises à Jour de l'Agent

### Synchronisation Automatique de l'Agent

Quand vous modifiez le comportement de l'agent en changeant :

- **`core/prompts.py`** - Instructions système et connaissances métier
- **`tools/functions_tools.py`** - Outils et fonctions disponibles

Vous devez mettre à jour l'agent dans Azure Foundry pour refléter ces changements :

#### Mise à Jour Rapide (Recommandée)
```bash
python update_agent.py
```

#### Mise à Jour Manuelle
```bash
python agent/create_agent.py update
```

#### Ce qui est Mis à Jour
- **Instructions** : Derniers prompts système depuis `core/prompts.py`
- **Outils** : Dernières définitions d'outils depuis le code
- **ID Agent** : Utilise `AGENT_ID` depuis votre fichier `.env`

#### Quand Mettre à Jour
- ✅ Après modification des prompts ou instructions système
- ✅ Après ajout/suppression/modification d'outils
- ✅ Après mise à jour des connaissances métier ou schémas
- ❌ Pas nécessaire pour la refactorisation de code (sauf si cela affecte les définitions d'outils)

---

## �🛠️ Développement

### Configuration Environnement Développement

```bash
# Installer en mode développement
pip install -e .

# Optionnel : Installer dépendances dev
pip install pytest black flake8 mypy
```

### Commandes Courantes

```bash
# Exécuter les tests base de données
python test_data.py

# Lancer l'agent (interactif)
python agent/fdt_agent.py

# Test rapide
python -c "from database.connection import get_engine; print('✅ Base de données connectée')"
```

### Débogage

```bash
# Vérifier l'environnement
python -c "import os; print(os.getenv('AGENT_ID', 'NON DÉFINI'))"

# Vérifier les dépendances
pip list | grep azure

# Tester les identifiants Azure
az account show
```

---

## 📋 Commandes Essentielles

### Configuration Environnement
```bash
python -m venv venv               # Créer environnement
venv\Scripts\activate              # Activer (Windows)
pip install -r requirements.txt    # Installer dépendances
```

### Configuration
```bash
copy .env.example .env             # Créer config
# Éditer .env avec :
# AZURE_AI_PROJECT_ENDPOINT=...
# AGENT_ID=...
# AZURE_USERNAME=...
# AZURE_PASSWORD=...
```

### Utilisation
```bash
python test_data.py                # Tester connexion
python agent/fdt_agent.py          # Lancer agent
python update_agent.py             # Mettre à jour l'agent après modifications
```

### Mettre à Jour l'Agent Après Modifications
Quand vous modifiez `core/prompts.py` ou `tools/functions_tools.py`, mettez à jour l'agent dans Azure Foundry :

```bash
# Mise à jour rapide
python update_agent.py

# Ou utiliser le script create_agent
python agent/create_agent.py update
```

### Exemple Code
```python
import asyncio
from agent.fdt_agent import ask

async def main():
    result = await ask("Quels projets dépassent 500 heures ?")
    print(result)

asyncio.run(main())
```

---

## 🔧 Configuration

### Variables d'Environnement

Créer un fichier `.env` avec :

```bash
# Agent Azure AI
AZURE_AI_PROJECT_ENDPOINT=https://votre-projet.cognitiveservices.azure.com
AGENT_ID=agent-xxxxxxxxxxxxx

# Azure Synapse
AZURE_USERNAME=votre-utilisateur@domaine.com
AZURE_PASSWORD=votre-mot-de-passe-securise
SYNAPSE_DATABASE=SilverLayer

# Performance (optionnel)
QUERY_TIMEOUT_SECONDS=300
```

### Connexion Base de Données

Éditer `database/connection.py` pour personnaliser :
- Taille du pool de connexions
- Timeouts de requêtes
- Paramètres SSL/TLS
- Configuration proxy

---

## 🤝 Contribution

Nous accueillons les contributions ! Voici comment :

### Workflow Développement

```bash
# Créer une branche feature
git checkout -b feature/votre-fonctionnalite

# Faire les changements et tester
python test_data.py

# Commiter avec message clair
git commit -m "feat: ajouter nouvelle capacité"

# Pousser vers GitHub
git push origin feature/votre-fonctionnalite

# Ouvrir Pull Request
```

### Directives
- Suivre le guide de style PEP 8
- Ajouter des docstrings aux fonctions
- Tester les nouvelles fonctionnalités
- Mettre à jour la documentation
- Garder les commits focalisés

---

## 📚 Documentation

- [Guide Configuration](docs/setup.md)
- [Référence API](docs/api.md)
- [Dépannage](docs/troubleshooting.md)
- [Architecture](docs/architecture.md)

---

## ❓ Dépannage

### Problèmes de Connexion
```bash
# Vérifier les identifiants Azure
az login
az account show

# Vérifier la connectivité base de données
python test_data.py
```

### Erreurs Agent
```bash
# Vérifier les variables d'environnement
python -c "import os; print(os.getenv('AGENT_ID'))"

# Vérifier les dépendances
pip list | grep azure
```

### Timeouts Requêtes
Éditer `database/connection.py` :
```python
Connection Timeout=600  # Augmenter de 300 secondes
```

---

## 💬 Communauté & Support

- **Issues** : [GitHub Issues](https://github.com/mossabweda02/FDT_Agent/issues)
- **Discussions** : [GitHub Discussions](https://github.com/mossabweda02/FDT_Agent/discussions)
- **Email** : support@fdt.io

---

## 📄 Licence

Licence MIT - Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

Construit avec :
- [Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
- [Azure Synapse Analytics](https://azure.microsoft.com/en-us/services/synapse-analytics/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- Communauté open source