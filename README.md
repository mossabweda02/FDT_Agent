# Agent FDT - Analyse Intelligente des Feuilles de Temps

## Introduction

L'Agent FDT est un assistant conversationnel alimenté par l'IA permettant d'interagir avec des données de feuilles de temps à l'aide du langage naturel.

L'objectif du projet est de simplifier l'accès aux données métier pour les utilisateurs non techniques. Au lieu d'écrire des requêtes SQL complexes, les utilisateurs peuvent poser leurs questions en français ou en anglais et obtenir des réponses pertinentes générées par l'agent.

Le projet s'appuie sur une architecture moderne combinant un backend Python, un frontend React et des services Azure afin d'offrir une expérience conversationnelle sécurisée et évolutive.

### Fonctionnalités principales

- **Questions en langage naturel** pour interroger les données.
- **Génération sécurisée de requêtes SQL** avec validation des requêtes.
- **Contexte conversationnel** permettant de conserver les échanges récents.
- **Authentification Microsoft Entra ID (Azure AD)** pour sécuriser l'accès à l'application.
- **Architecture moderne** basée sur FastAPI, React/Vite et Azure OpenAI.
- **Observabilité** grâce à OpenTelemetry, Logfire et Aspire Dashboard.

---

# Pour Commencer (Getting Started)

## Prérequis

Assurez-vous d'avoir installé :

- Python 3.10+
- Node.js 18+
- Docker (optionnel, pour l'observabilité locale)
- ODBC Driver 18 for SQL Server
- Azure CLI

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/mossabweda02/FDT_Agent.git
cd FDT_Agent
```

### 2. Configurer les variables d'environnement

Créer un fichier `.env` à la racine du projet.

Exemple :

```env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=

VITE_ENTRA_CLIENT_ID=
VITE_ENTRA_TENANT_ID=
VITE_API_SCOPE=
```

Les valeurs dépendent de votre environnement Azure.

---

### 3. Installer le Backend

```bash
python -m venv venv
```

Windows

```bash
.\venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

### 4. Installer le Frontend

```bash
cd Frontend
npm install
```

---

# API

Le backend expose principalement les endpoints suivants :

| Endpoint | Description |
|-----------|-------------|
| POST `/ask` | Envoie une question à l'agent IA |
| POST `/suggest` | Retourne des suggestions de questions |
| GET `/health` | Vérifie l'état de l'API |

---

# Exécution

## 1. Démarrer le Backend

Depuis la racine du projet :

```bash
uvicorn backend.api:app --reload --port 8000
```

---

## 2. Démarrer le Frontend

Depuis le dossier Frontend :

```bash
npm run dev
```

Application disponible sur :

```
http://localhost:3000
```

---

## 3. Observabilité (optionnel)

Pour exécuter Aspire Dashboard :

```bash
docker run --rm -it \
-p 18888:18888 \
-p 4317:18889 \
-p 4318:18890 \
-e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true \
--name aspire-dashboard \
mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

Dashboard disponible sur :

```
http://localhost:18888
```

---

# Architecture

Le projet est organisé autour des composants suivants :

- **Frontend**
  - React
  - Vite
  - Microsoft Entra ID (MSAL)

- **Backend**
  - FastAPI
  - Pydantic AI
  - Azure OpenAI

- **Base de données**
  - Azure Synapse Analytics

- **Observabilité**
  - OpenTelemetry
  - Logfire
  - Aspire Dashboard

---

# Tests

Pour exécuter les principaux tests :

```bash
python test_agent.py
```

Selon les besoins, d'autres scripts de tests peuvent être exécutés depuis le dossier `tests/`.

---

# Contribution

Les contributions sont les bienvenues.

1. Forkez le dépôt.
2. Créez une branche :

```bash
git checkout -b feature/ma-feature
```

3. Effectuez vos modifications.
4. Vérifiez que les tests passent.
5. Commitez vos changements avec un message explicite.
6. Ouvrez une Pull Request.

Merci de respecter le style de code du projet et de documenter les nouvelles fonctionnalités lorsque cela est nécessaire.