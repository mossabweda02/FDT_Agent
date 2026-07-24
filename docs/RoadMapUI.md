# FDT Agent — Admin Dashboard Roadmap

## 1. Contexte projet

FDT Agent est un agent conversationnel IA spécialisé dans l’analyse des feuilles de temps.  
Il permet aux utilisateurs de poser des questions en langage naturel et interroge Azure Synapse via des tools SQL sécurisés.

L’objectif de cette nouvelle tâche est de créer une UI Admin simplifiée pour suivre :
- l’audit trail des échanges avec l’agent ;
- la consommation des tokens ;
- les coûts LLM ;
- les performances globales de l’agent.

Cette UI ne remplace pas Aspire ou Logfire.  
Aspire/Logfire restent dédiés à l’observabilité technique, alors que l’Admin Dashboard est destiné au suivi métier.

---

## 2. Architecture globale utile

```text
Utilisateur
   ↓
Frontend React
   ↓
Backend FastAPI
   ↓
Pydantic AI Agent
   ↓
Tools SQL
   ↓
Azure Synapse

En parallèle :
Backend / Agent / Tools
   ↓
Logfire + OpenTelemetry
   ↓
Aspire Dashboard
```
Pour l’Admin Dashboard cible :
``` text
FDT Agent
   ↓
Audit / Metrics Layer
   ↓
Admin Dashboard UI
```

## 3. Structure des Dossiers

```text
FDT_AGENT/
├── backend/                  # Backend Python
│   ├── agent/                # Cœur IA + serveur API
│   │   ├── pydantic_agent/           # ✅ ACTIF — Agent Pydantic AI + Azure OpenAI
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # Création agent Pydantic AI + ask()
│   │   │   └── tools.py              # Enregistrement 6 outils via @agent.tool_plain
│   │   ├── ia_foundry/               # ⛔ LEGACY — Historique Azure AI Foundry
│   │   │   ├── fdt_agent.py          # Boucle agent Azure AI Foundry (ancien)
│   │   │   ├── create_agent.py       # Script création agent Azure (ancien)
│   │   │   └── update_agent.py       # Sync prompt/tools Azure (ancien)
│   │   ├── scrubbing/                # ✅ Observabilité & données sensibles
│   │   │   ├── observability.py      # Logfire + OTel + Scrubbing
│   │   │   └── question_sanitizer.py # Détection PII
│   ├── server/
│   │   └── api_server.py             # Backend FastAPI (endpoints /ask, /suggest, /health)
│   ├── core/                         # Intelligence de l'agent
│   │   ├── prompts/
│   │   │   ├── role_prompt.py        # Bloc 1 : identité, langue, protocole
│   │   │   ├── rules_prompt.py       # Bloc 3 : règles SQL, jointures
│   │   │   ├── schema_prompt.py      # Bloc 2 : description métier tables
│   │   │   └── system_prompt.py      # Assembleur final : build_system_prompt()
│   │   ├── training_examples.py      # Base Few-Shot (Q→SQL exemples)
│   │   └── exceptions.py             # Exceptions métier personnalisées
│   ├── database/
│   │   └── connection.py             # Synapse via DefaultAzureCredential
│   ├── tools/
│   │   ├── functions_tool.py         # Implémentation 6 outils + TOOL_FUNCTIONS
│   │   ├── sql_validator.py          # Sécurité SQL : anti-DML, anti-injection
│   │   └── tools_runner.py           # Parser JSON + dispatcher (legacy)
│   ├── check_corrections.py          # Validation d'intégrité avant déploiement
│   ├── test_agent.py                 # Suite tests métier (pydantic_agent.ask)
│   ├── test_data.py                  # Données tests
│   └── .env                          # Variables d'environnement (non versionné)
├── frontend/                 # Frontend React
│   ├── src/
│   │   ├── App.jsx           # Composant principal (SPA ~1300 lignes)
│   │   ├── main.jsx          # Point d'entrée React
│   │   ├── styles/
│   │   │   │   ├── App.css       # Traductions anglais
│   │   │   │   └── index.css 
│   │   ├── i18n/
│   │   │   ├── en.json       # Traductions anglais
│   │   │   ├── fr.json         # Traductions français
│   │   │   └── useTranslation.js        
│   │   ├── pages/
│   │   │   └── ChatPage.css 
│   │   ├── api/
│   │   │   └── agentApi.js #appels à l'API backend pour interagir avec l'agent 
│   │   └── assets/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── tests/                    # Suite tests complète
│   ├── test_agent.py
│   ├── test_data.py
│   ├── check_corrections.py
│   └── scrubbing/           # Tests observabilité
├── docs/
│   ├── FDT-Agent.md         # Cette documentation
│   └── agent_analysis.md
├── scripts/
│   └── export_tool_outputs_anonymized.py  # Export anonymisé traces
├── README.md
├── requirements.txt
└── .env                      # Configuration locale
```

## 4. Fichiers importants
`backend/server/api_server.py`

Point d’entrée FastAPI.
Expose les endpoints principaux :

* `POST /ask`
* `POST /suggest`
* `GET /health`
C’est ici que l’agent est appelé.

`backend/agent/pydantic_agent/agent.py`
Contient l’agent Pydantic AI et la fonction ask().

`backend/agent/pydantic_agent/tools.py`
Enregistre les tools SQL utilisés par l’agent.

`backend/tools/functions_tool.py`
Contient l’implémentation des outils :
list tables
describe table
get schema
get sample data
get relationships
execute query

`backend/agent/scrubbing/observability.py`
Configure : 
Logfire
OpenTelemetry
Aspire export
scrubbing des données sensibles
instrumentation FastAPI / Pydantic AI

`backend/agent/scrubbing/question_sanitizer.py`
Anonymise les questions utilisateur avant logging.

`frontend/src/`
Contient l’interface React actuelle.

## 5. Séparation des responsabilités
### Aspire / Logfire
Utilisés pour :
* traces techniques 
* debugging développeur 
* spans 
* erreurs backend 
* analyse technique détaillée.

### Admin Dashboard
Utilisé pour :
* suivi métier 
* audit trail simplifié 
* consommation tokens 
* coûts LLM 
* performance globale 
* suivi des échanges anonymisés.

Le dashboard ne doit pas afficher :
* prompts bruts 
* SQL brut 
* outputs tools bruts 
* données sensibles 
traces OTLP complexes.

## 6. Phases du dashboard
### Phase 1 — Frontend Demo UI

Objectif :
Créer une première version visuelle du dashboard admin avec des données mockées.

Cette phase sert à :

* valider le design 
* valider les pages 
* valider les KPIs 
* préparer une démo 
ne pas dépendre d’une base de données.

Aucune vraie donnée backend n’est nécessaire dans cette phase.

Pages attendues :
- Overview
- Audit Trail
- Token & Cost Analytics

### Phase 2 — Backend Metrics Layer

Objectif :
Créer les endpoints backend et préparer le modèle de données.

Exemples :

* `GET /admin/overview`
* `GET /admin/audit-events`
* `GET /admin/costs`
* `GET /admin/tools`

Cette phase n’est pas concernée maintenant.

### Phase 3 — Intégration réelle

Objectif :
Brancher le dashboard sur les vraies données :

* audit events 
* tokens 
* coûts 
* latence 
* erreurs 
* tools utilisés.

Cette phase nécessite un stockage durable.

### 7. Tâche actuelle — Phase 1

Créer uniquement le frontend du dashboard admin.

Contraintes :
* utiliser des données mockées 
* ne pas créer de backend 
* ne pas créer de DB 
* ne pas connecter Aspire 
* respecter un design moderne inspiré de l’image fournie 
* garder uniquement les sections utiles au monitoring agent.

Contenu attendu :
* sidebar moderne 
* header 
* cards KPI 
* graphiques tokens/coûts 
* audit trail table 
* statut agent 
* performance agent 
* design responsive.

KPIs mockés recommandés :
* total requests 
* success rate 
* average latency 
* P95 latency 
* total tokens 
* input tokens 
* output tokens 
* estimated cost 
* failed requests 
* active users.

Visualisations recommandées :
* requests over time 
* token usage over time 
* cost over time 
* latency by category 
* top question categories 
* recent audit trail.

## 8. Contraintes de confidentialité
Toutes les données affichées doivent être anonymisées ou agrégées.

Utiliser :
* question_preview
* question_category
* status
* latency_ms
* tokens
* cost
* tools_used

Ne jamais afficher :
* question brute 
* réponse brute 
* SQL brut 
* tool output brut 
* données RH ou financières non anonymisées.