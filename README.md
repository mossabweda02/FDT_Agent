# Agent FDT - Analyse Intelligente des Feuilles de Temps

## Introduction
L'Agent FDT est un agent conversationnel autonome alimenté par l'IA, conçu pour interroger, analyser et synthétiser de manière transparente les données de feuilles de temps stockées dans une base de données Azure Synapse Analytics (Silver Layer).

La motivation principale de ce projet est de démocratiser la Business Intelligence (BI) pour les utilisateurs non techniques. Au lieu de nécessiter des connaissances complexes en SQL, les utilisateurs peuvent poser des questions en langage naturel (en français ou en anglais) concernant les projets, les heures des employés, les tâches et la rentabilité. L'agent traduit intelligemment ces questions en requêtes T-SQL sécurisées et optimisées et renvoie des informations claires et exploitables.

Les principales fonctionnalités incluent :
- **Requêtage en Langage Naturel** : Traduit les questions complexes en requêtes T-SQL précises.
- **Validation SQL Sécurisée** : Applique strictement un accès en lecture seule (en bloquant les opérations DML telles que INSERT/UPDATE/DELETE).
- **Architecture Moderne** : Utilise FastAPI pour un backend hautement performant, Pydantic AI pour la logique de l'agent, et un frontend dynamique en React/Vite.
- **Observabilité et Sécurité** : Intègre Logfire et OpenTelemetry avec un masquage (scrubbing) robuste des données sensibles (PII, secrets), visualisé localement via Aspire Dashboard.

## Pour Commencer (Getting Started)
Suivez ces étapes pour lancer l'Agent FDT sur votre environnement de développement local.

### Dépendances Logicielles
Assurez-vous que les éléments suivants sont installés sur votre système :
- **Python 3.10+**
- **Node.js 18+**
- **ODBC Driver 18 for SQL Server** (Requis pour la connexion à Azure Synapse)
- **Azure CLI** (`az login` est requis pour s'authentifier via `DefaultAzureCredential`)
- **Docker** (Requis pour exécuter l'Aspire Dashboard pour l'observabilité)

### Processus d'Installation
1. **Clonez le dépôt :**
   ```bash
   git clone https://github.com/mossabweda02/FDT_Agent.git
   cd FDT_Agent
   ```

2. **Configurez l'environnement :**
   Créez un fichier `.env` à la racine du projet et configurez vos identifiants Azure et Synapse :
   ```env
   AZURE_OPENAI_ENDPOINT=https://votre-endpoint.openai.azure.com/
   AZURE_OPENAI_API_KEY=votre_cle_api
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   SYNAPSE_DATABASE=SilverLayer
   ```

3. **Configuration du Backend :**
   ```bash
   # Créez et activez un environnement virtuel
   python -m venv venv
   
   # Sous Windows :
   .\venv\Scripts\Activate.ps1
   # Sous macOS/Linux :
   source venv/bin/activate
   
   # Installez les dépendances Python
   pip install -r requirements.txt
   ```

4. **Configuration du Frontend :**
   ```bash
   cd Frontend
   npm install
   ```

### Références API
Le backend expose un serveur FastAPI avec les endpoints principaux suivants :
- `POST /ask` : Accepte une question de l'utilisateur et renvoie la réponse de l'agent IA.
- `POST /suggest` : Analyse le contexte et renvoie 3 suggestions de questions de suivi.
- `GET /health` : Renvoie le statut de l'API.
- `GET /test-scrubbing` : Endpoint de test pour vérifier le masquage des données sensibles dans les logs.

Vous pouvez accéder à la documentation interactive de l'API (Swagger UI) à l'adresse `http://localhost:8000/docs` lorsque le backend est en cours d'exécution.

## Build et Tests

### Exécution de l'Application
Vous devez exécuter simultanément les serveurs backend et frontend.

**1. Démarrer le Backend FastAPI :**
```bash
# À partir de la racine du projet
uvicorn agent.api_server:app --port 8000 --reload
```

**2. Démarrer le Frontend React :**
```bash
# Dans un nouveau terminal, depuis le dossier /Frontend
npm run dev
```
L'application sera accessible à l'adresse `http://localhost:3000`.

**3. Démarrer l'Observabilité (Aspire Dashboard) :**
Pour visualiser les traces et les logs en local avec le masquage des données activé :
```bash
# Dans un nouveau terminal
docker run --rm -it -p 18888:18888 -p 4317:18889 -p 4318:18890 -e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:latest
```
Le tableau de bord sera accessible à l'adresse `http://localhost:18888`.

### Exécution des Tests
Le projet inclut une suite de tests robuste qui valide la logique de l'agent en comparant ses réponses avec des requêtes SQL directes à la base de données Synapse.

Pour exécuter la suite de tests de l'agent :
```bash
# À partir de la racine du projet
python test_agent.py
```
Ce script exécutera différents cas de test (Facile, Moyen, Avancé, Analytique et Hors Contexte) et fournira un score basé sur la précision de la génération SQL et de la récupération des données par l'agent.

## Contribuer
Nous accueillons les contributions pour rendre l'Agent FDT encore meilleur ! Si vous souhaitez contribuer, veuillez suivre ces étapes :

1. **Forkez le dépôt** et créez une nouvelle branche de fonctionnalité (`git checkout -b feature/nom-de-votre-fonctionnalite`).
2. **Faites vos modifications**. Si vous modifiez les invites de l'agent (`core/prompts.py` ou `core/prompts/`) ou les outils SQL (`tools/functions_tools.py`), assurez-vous de tester minutieusement vos changements.
3. **Exécutez la suite de tests** (`python test_agent.py`) pour vous assurer qu'aucune logique existante n'est cassée et que la validation SQL reste sécurisée.
4. **Commitez vos changements** avec des messages de commit descriptifs.
5. **Poussez vers votre branche** et ouvrez une Pull Request (demande de tirage).

Veuillez vous assurer que votre code respecte les conventions de style existantes et inclut des commentaires appropriés pour la logique complexe.