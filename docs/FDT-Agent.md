# FDT Agent (Chronos-FDT) — Contexte Local IA

---

## 📝 Description Générale

**FDT Agent** est un agent conversationnel IA conçu pour assister les utilisateurs dans l'analyse et la gestion des feuilles de temps.

Le projet repose sur un backend **FastAPI**, un agent **Pydantic AI** connecté à **Azure OpenAI**, une base analytique **Azure Synapse Silver Layer**, un frontend **React + Vite**, une authentification **Microsoft Entra ID / MSAL**, ainsi que des APIs métier exposées par l'**Integration Hub**.

L'agent couvre deux grands types de besoins :

1. **Consultation analytique**
   - interrogation des données de feuilles de temps ;
   - analyse des heures, projets, tâches, ressources, coûts et rentabilité ;
   - génération de réponses en langage naturel à partir de données Synapse ;
   - exécution de requêtes T-SQL strictement en lecture seule.

2. **Actions métier**
   - création de feuilles de temps ;
   - ajout d'une ou plusieurs lignes de temps ;
   - préparation des modifications et suppressions de lignes ;
   - récupération des projets, tâches, catégories, livrables et périodes via l'Integration Hub ;
   - clarification active lorsque des informations sont manquantes ou ambiguës ;
   - confirmation explicite avant toute écriture ;
   - protection contre les doubles confirmations et les exécutions multiples.

L'objectif principal est de simplifier l'accès aux données et aux opérations liées aux feuilles de temps, sans exiger de compétences SQL ou techniques côté utilisateur.

---

## 🏗 Architecture Globale

```text
                [ Utilisateur ]
                        │ (Questions / UI)
                        ▼
                Microsoft Entra ID
                        │
                Authentication (MSAL)
                        │
                        ▼
                React + Vite Frontend
       (Chat • Questionnaire • Settings • Admin)
                        │
          POST /ask   POST /clarify   POST /suggest
                        ▼
                FastAPI Backend
                        │
       ┌────────────────┼─────────────────────┐
       │                │                     │
       ▼                ▼                     ▼
Workflow métier   Pydantic AI Agent    User Context Resolver
       │          (Azure OpenAI)        (JWT claims + resource)
       │                │                     │
       ├────────────────┼──────────────┐      │
       │                │              │      │
       ▼                ▼              ▼      ▼
Clarification     Outils SQL      Outils Hub / Executors
& Confirmation    lecture seule   actions métier confirmées
       │                │              │
       │                ▼              ▼
       │        Azure Synapse     Integration Hub
       │        Silver Layer      (Operate / ERP)
       └───────────────────────────────┘
```

## ✅ État Actuel du Projet

Le projet utilise actuellement :

- **Pydantic AI** pour l'orchestration de l'agent ;
- **Azure OpenAI GPT-4.1-nano** comme modèle LLM ;
- **Azure Synapse Silver Layer** pour les requêtes analytiques ;
- **FastAPI 1.1.0** pour exposer les endpoints backend ;
- **React + Vite** pour l'interface utilisateur ;
- **Microsoft Entra ID / MSAL** pour l'authentification frontend ;
- **Microsoft Graph** avec le scope `User.Read` pour récupérer la photo de profil ;
- **Bearer token propagation** pour sécuriser les appels vers le backend et l'Integration Hub ;
- **Integration Hub** pour les actions métier liées aux timesheets ;
- un **UserContext** partagé entre l'API, l'agent et les outils ;
- un **workflow métier en mémoire** par `conversation_id` ;
- une **clarification active** structurée et validée côté backend ;
- une **confirmation obligatoire** avant toute action d'écriture ;
- une protection contre la **double exécution** grâce aux transitions d'état ;
- une résolution simple des dates relatives (`aujourd'hui`, `hier`, `demain`) ;
- une résolution des périodes de feuilles de temps et une recherche par chevauchement ;
- **OpenTelemetry + Logfire + Aspire Dashboard** pour l'observabilité locale ;
- un **scrubbing des données sensibles** pour éviter l'exposition de données RH, financières ou techniques ;
- un thème **clair / sombre / système** persistant côté frontend ;
- des préférences de chat persistantes dans `localStorage`.

Les anciens fichiers liés à **Azure AI Foundry Agent** sont conservés comme éléments **legacy** pour rollback ou comparaison, mais ils ne représentent plus le chemin actif du projet.

---

## 🔁 Flux Fonctionnel Principal

### 1. Flux Analytique

```text
Utilisateur
   │
   ▼
Frontend React
   │ POST /ask + Bearer token + historique
   ▼
Backend FastAPI
   │
   ├── résolution du UserContext
   ├── vérification du workflow en cours
   └── appel de l'agent si aucun workflow prioritaire
          │
          ▼
Pydantic AI Agent
   │
   ▼
Outils SQL locaux
   │
   ▼
Validation SQL
   │
   ▼
Azure Synapse Silver Layer
   │
   ▼
Réponse Markdown à l'utilisateur
```

### Étapes

1. L'utilisateur pose une question dans l'interface de chat.
2. Le frontend transmet la question, l'identifiant de conversation et l'historique récent.
3. Le backend valide le Bearer token.
4. Le backend construit le `UserContext` et tente de résoudre l'utilisateur Entra ID vers une ressource métier.
5. Le backend vérifie si un workflow métier est déjà en attente de confirmation, de clarification ou de retry.
6. Si la requête est analytique, l'agent choisit les outils SQL nécessaires.
7. Les requêtes sont validées par `sql_validator.py`.
8. Les données sont récupérées depuis Azure Synapse.
9. L'agent synthétise une réponse métier claire en Markdown.
10. Le frontend peut proposer des suggestions contextuelles après la réponse.

---

## ⚙️ Flux d'Action Métier via Integration Hub

```text
Utilisateur
   │
   ▼
Frontend React authentifié
   │ POST /ask + Bearer token
   ▼
FastAPI
   │
   ├── UserContext
   ├── Intent Classifier
   ├── Scenario Detector
   ├── Structured Extractor
   ├── BusinessRequest Normalizer
   └── Execution Plan Builder
          │
          ▼
Clarification Validator
   │
   ├── informations manquantes
   │        │
   │        ▼
   │   POST /clarify
   │        │
   │        ▼
   │   questionnaire en cascade
   │
   └── demande complète
            │
            ▼
      WAITING_CONFIRMATION
            │
       utilisateur confirme
            │
            ▼
         EXECUTING
            │
            ▼
        Executors Hub
            │
            ▼
      Integration Hub / ERP
            │
            ▼
    COMPLETED ou FAILED
```

### Principes

- Les actions métier ne passent pas par SQL.
- Les outils Hub utilisent les APIs REST de l'Integration Hub.
- Le Bearer token utilisateur est propagé depuis le frontend jusqu'aux fonctions Hub.
- Le `resource_id` de l'utilisateur connecté est résolu automatiquement lorsque possible.
- Les actions d'écriture doivent être précédées d'une confirmation explicite.
- Les données métier sont conservées entre la préparation, la clarification et la confirmation.
- Les transitions d'état empêchent une double confirmation d'exécuter deux fois la même action.
- Les réponses des APIs Hub sont standardisées en JSON string.
- Une erreur est marquée comme récupérable uniquement lorsqu'aucune écriture n'a eu lieu.
- Une écriture partielle bloque le retry automatique afin d'éviter les doublons.

### Exemples d'actions couvertes

- lister les projets ;
- récupérer les tâches d'un projet ;
- rechercher une ressource ;
- récupérer les catégories timesheet ;
- créer une feuille de temps vide ;
- ajouter une ligne d'heures ;
- ajouter plusieurs lignes sur une même journée ;
- ajouter plusieurs tâches sur un même projet ;
- répéter une saisie sur une période ;
- modifier une ligne d'heures ;
- supprimer une ligne d'heures ;
- récupérer les périodes timesheet ;
- récupérer les livrables d'un projet ou d'une tâche.

---

## 🔐 Authentification Microsoft Entra ID

Le frontend utilise **MSAL** pour authentifier l'utilisateur avec Microsoft Entra ID.

### Flux d'authentification

```text
Utilisateur
   │
   ▼
AuthPage.jsx
   │ loginRedirect()
   ▼
Microsoft Entra ID
   │ callback
   ▼
main.jsx
   │ initialize() + handleRedirectPromise()
   ▼
MSAL active account
   │
   ▼
App.jsx
   │ Auth gate
   ▼
ChatPage.jsx
```

### Fonctionnement

1. L'utilisateur clique sur **Continuer avec Microsoft**.
2. `AuthPage.jsx` déclenche `loginRedirect(loginRequest)`.
3. Microsoft Entra ID redirige vers `/authentication/login-callback`.
4. `main.jsx` initialise MSAL, traite le retour de redirection et restaure le compte actif.
5. `App.jsx` affiche `AuthPage` si l'utilisateur n'est pas connecté.
6. Si l'utilisateur est authentifié, `ChatPage` devient accessible.
7. Les appels backend utilisent `getAccessToken()`.
8. Les appels Microsoft Graph utilisent `getGraphAccessToken()` avec le scope `User.Read`.
9. `agentApi.js` ajoute automatiquement `Authorization: Bearer <token>` aux appels backend.
10. `graphApi.js` récupère la photo de profil via `GET /me/photo/$value`.

### Contexte utilisateur backend

Le backend construit un `UserContext` contenant :

- `auth_header` ;
- `email` ;
- `fullname` ;
- `object_id` ;
- `resource_id` ;
- `role` ;
- `resource_resolution_status`.

En V1, les claims JWT sont décodés sans validation cryptographique complète. La validation de la signature, de l'issuer, de l'audience, de l'expiration et des scopes est prévue pour une phase ultérieure.

Le backend tente ensuite une résolution `email -> resource_id` via l'Integration Hub.

Statuts possibles :

- `resolved` ;
- `not_found` ;
- `missing_email_claim` ;
- `hub_error` ;
- `not_attempted`.

---

## 🧠 Contexte Conversationnel

Le projet supporte un contexte conversationnel court et un état de workflow métier par conversation.

Chaque requête `/ask` peut contenir :

- `question` : message courant de l'utilisateur ;
- `conversation_id` : identifiant de la conversation ;
- `history` : derniers messages de la conversation.

Le backend utilise deux mécanismes complémentaires :

1. **Historique court injecté dans le prompt**
   - les huit derniers messages sont ajoutés au contexte de l'agent ;
   - cette logique aide pour les questions de suivi et les échanges analytiques.

2. **WorkflowState par `conversation_id`**
   - stocke l'intention, le scénario, la demande structurée et le plan d'exécution ;
   - conserve les questions de clarification et les réponses collectées ;
   - protège les confirmations et les retries ;
   - est prioritaire pour les messages courts comme `oui`, `annuler` ou `réessayer`.

### États du workflow

```text
IDLE
 ├── WAITING_CLARIFICATION
 │      ├── WAITING_CONFIRMATION
 │      └── CANCELLED
 └── WAITING_CONFIRMATION
        ├── EXECUTING
        │      ├── COMPLETED
        │      └── FAILED
        │             ├── EXECUTING (retry récupérable)
        │             └── CANCELLED
        ├── WAITING_CLARIFICATION
        └── CANCELLED
```

Le stockage actuel est en mémoire :

- il est perdu au redémarrage du serveur ;
- il n'est pas partagé entre plusieurs instances FastAPI ;
- il est accepté pour la V1 ;
- une future évolution pourra utiliser Redis ou une base de données.

---

## 📁 Structure des Dossiers

```text
FDT_AGENT/
├── backend/
│   ├── agent/
│   │   ├── pydantic_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── tools.py
│   │   ├── ia_foundry/                 # LEGACY
│   │   │   ├── fdt_agent.py
│   │   │   ├── create_agent.py
│   │   │   └── update_agent.py
│   │   └── scrubbing/
│   │       ├── observability.py
│   │       └── question_sanitizer.py
│   │
│   ├── core/
│   │   ├── auth/
│   │   │   └── user_context.py
│   │   │
│   │   ├── business/
│   │   │   ├── handlers/
│   │   │   │   ├── base.py
│   │   │   │   ├── create_timesheet_handler.py
│   │   │   │   ├── multi_project_same_day_handler.py
│   │   │   │   ├── multi_task_same_project_handler.py
│   │   │   │   ├── repeat_entry_handler.py
│   │   │   │   └── single_time_entry_handler.py
│   │   │   ├── timesheet_resolution/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   ├── period_resolver.py
│   │   │   │   ├── resolution_service.py   # présent mais vide
│   │   │   │   └── timesheet_finder.py
│   │   │   ├── business_request.py
│   │   │   ├── business_request_normalizer.py
│   │   │   ├── business_types.py
│   │   │   ├── clarification_builder.py
│   │   │   ├── clarification_types.py
│   │   │   ├── clarification_validator.py
│   │   │   ├── confirmation.py
│   │   │   ├── confirmation_messages.py
│   │   │   ├── execution_plan.py
│   │   │   ├── executors.py
│   │   │   ├── intent_catalog.py
│   │   │   ├── intent_classifier.py
│   │   │   ├── scenario_detector.py
│   │   │   ├── structured_extractor.py
│   │   │   ├── workflow_execution_helpers.py
│   │   │   ├── workflow_manager.py
│   │   │   └── workflow_state.py
│   │   │
│   │   ├── datetime/
│   │   │   └── date_resolver.py
│   │   │
│   │   ├── prompts/
│   │   │   ├── role_prompt.py
│   │   │   ├── rules_prompt.py
│   │   │   ├── schema_prompt.py
│   │   │   ├── system_prompt.py
│   │   │   └── tools_definitions.py
│   │   ├── training_examples.py
│   │   └── exceptions.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   ├── server/
│   │   └── api_server.py
│   │
│   └── tools/
│       ├── functions_tool.py
│       ├── hub_functions.py
│       ├── sql_validator.py
│       └── tools_runner.py
│
├── frontend/
│   ├── public/
│   │   ├── icons.svg
│   │   └── favicon.svg
│   │
│   ├── src/
│   │   ├── api/
│   │   │   ├── agentApi.js
│   │   │   └── graphApi.js
│   │   │
│   │   ├── assets/
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   │
│   │   ├── auth/
│   │   │   ├── getAccessToken.js
│   │   │   ├── getGraphAccessToken.js
│   │   │   ├── msalConfig.js
│   │   │   └── msalInstance.js
│   │   │
│   │   ├── components/
│   │   │   ├── admin/
│   │   │   │   ├── AdminSidebar.jsx
│   │   │   │   ├── AuditTrailTable.jsx
│   │   │   │   └── MetricCard.jsx
│   │   │   ├── chat/
│   │   │   │   ├── messages/
│   │   │   │   │   ├── AgentMessage.jsx
│   │   │   │   │   ├── EmptyConversation.jsx
│   │   │   │   │   ├── ErrorMessage.jsx
│   │   │   │   │   ├── MessageActions.jsx
│   │   │   │   │   ├── MessageTimestamp.jsx
│   │   │   │   │   ├── QuestionnaireMessage.jsx
│   │   │   │   │   ├── TypingMessage.jsx
│   │   │   │   │   └── UserMessage.jsx
│   │   │   │   ├── MarkdownRenderer.jsx
│   │   │   │   ├── ToolCallRow.jsx
│   │   │   │   ├── ToolCallsCard.jsx       # présent mais vide
│   │   │   │   ├── ToolGroup.jsx
│   │   │   │   └── ToolGroup.css
│   │   │   ├── settings/
│   │   │   │   ├── SettingsPanel.jsx
│   │   │   │   └── SettingsPanel.css
│   │   │   ├── sidebar/
│   │   │   │   ├── ConversationItem.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Sidebar.css
│   │   │   │   ├── SidebarHeader.jsx
│   │   │   │   ├── SidebarItem.jsx
│   │   │   │   ├── SidebarSection.jsx
│   │   │   │   └── UserSessionCard.jsx
│   │   │   ├── ui/
│   │   │   │   ├── button.jsx
│   │   │   │   └── ThemeToggle.jsx
│   │   │   ├── DotField.jsx
│   │   │   └── DotField.css
│   │   │
│   │   ├── context/
│   │   │   └── ThemeContext.jsx
│   │   │
│   │   ├── data/
│   │   │   └── adminMockData.js
│   │   │
│   │   ├── hooks/
│   │   │   ├── useChatPreferences.js
│   │   │   ├── useCopy.js
│   │   │   ├── useMicrosoftProfilePhoto.js
│   │   │   ├── usePersistentState.js
│   │   │   └── useSmartAutoScroll.js
│   │   │
│   │   ├── i18n/
│   │   │   ├── en.json
│   │   │   ├── fr.json
│   │   │   └── useTranslation.js
│   │   │
│   │   ├── lib/
│   │   │   └── utils.js
│   │   │
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx
│   │   │   ├── AuthPage.jsx
│   │   │   └── AdminDashboard.jsx
│   │   │
│   │   ├── styles/
│   │   │   ├── App.css
│   │   │   ├── AuthPage.css
│   │   │   ├── ChatPage.css
│   │   │   ├── index.css
│   │   │   └── theme.css
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── components.json
│   ├── jsconfig.json
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── index.html
│
├── tests/
│   ├── test_agent.py
│   ├── test_question_sanitize.py
│   ├── test_data.py
│   ├── check_agent_integrity.py
│   └── scrubbing/
│
├── docs/
│   ├── FDT-Agent.md
│   ├── agent_analysis.md
│   ├── CODING_STYLE_GUIDE.md
│   └── RoadMapUI.md
│
├── scripts/
│   └── export_tool_outputs_anonymized.py
├── README.md
├── requirements.txt
├── .gitignore
└── .env
```

---

## 📄 Détail par Fichier

### Backend — Modules Principaux

### `backend/agent/pydantic_agent/agent.py`

**Rôle** : initialise Azure OpenAI, crée l'agent Pydantic AI, prépare la demande métier et délègue au workflow ou à l'agent conversationnel.

**Responsabilités principales** :

- charger les variables d'environnement Azure OpenAI ;
- initialiser `AsyncAzureOpenAI` ;
- créer le modèle `OpenAIChatModel` ;
- instancier `Agent` avec `SYSTEM_PROMPT` et `AgentDeps` ;
- enregistrer les outils via `register_tools(agent)` ;
- sanitiser la question utilisateur ;
- créer un span Logfire `fdt.agent.ask` ;
- reconstruire un contexte conversationnel court ;
- construire le contexte temporel relatif ;
- récupérer les informations du `UserContext` ;
- classifier l'intention métier ;
- détecter le scénario métier ;
- extraire un `BusinessRequest` structuré avec Pydantic AI ;
- normaliser les identifiants et dates communes ;
- construire un `ExecutionPlan` ;
- déléguer les actions nécessitant confirmation à `handle_pending_business_action()` ;
- injecter `auth_header` et `user_context` dans `AgentDeps`.

**Points importants** :

- `auth_header` propage le token utilisateur aux outils Integration Hub ;
- `user_context` rend le `resource_id` disponible sans le redemander ;
- `conversation_id` est la clé du workflow métier ;
- les actions d'écriture ne sont pas exécutées directement par le LLM ;
- les actions confirmables passent par le workflow backend.

---

### `backend/agent/pydantic_agent/tools.py`

**Rôle** : enregistre les outils SQL et Integration Hub sur l'agent Pydantic AI.

**Responsabilités principales** :

- définir `AgentDeps` avec `auth_header` et `user_context` ;
- enregistrer les outils SQL avec `@agent.tool_plain` ;
- enregistrer les outils contextualisés avec `@agent.tool` ;
- exposer un diagnostic sécurisé du contexte utilisateur ;
- résoudre automatiquement le `resource_id` depuis le `UserContext` ;
- propager `ctx.deps.auth_header` aux fonctions Hub ;
- déléguer l'implémentation à `TOOL_FUNCTIONS` et `HUB_FUNCTIONS`.

**Pourquoi deux types de décorateurs ?**

- `@agent.tool_plain` : outils sans dépendances runtime ;
- `@agent.tool` : outils nécessitant le token, le contexte utilisateur ou le `resource_id` connecté.

**Outils SQL exposés** :

- `list_tables` ;
- `get_database_schema` ;
- `get_table_relationships` ;
- `describe_table` ;
- `get_sample_data` ;
- `execute_query` ;
- `get_auth_runtime_status`.

**Outils contextualisés** :

- `get_current_user_context` ;
- projets ;
- tâches ;
- ressources ;
- catégories ;
- feuilles de temps ;
- lignes timesheet ;
- livrables ;
- périodes timesheet.

---

## Backend — API

### `backend/server/api_server.py`

**Rôle** : expose l'API HTTP principale du projet.

**Endpoints actifs** :

| Endpoint | Méthode | Rôle |
|---|---:|---|
| `/ask` | POST | Envoyer une question à l'agent ou poursuivre un workflow |
| `/clarify` | POST | Envoyer les réponses d'un questionnaire de clarification |
| `/suggest` | POST | Générer des suggestions contextuelles |
| `/health` | GET | Vérifier l'état du service |

**Responsabilités principales** :

- créer l'application FastAPI version `1.1.0` ;
- configurer CORS pour le frontend local ;
- valider les payloads avec Pydantic ;
- récupérer le Bearer token depuis `Authorization` ;
- construire le `UserContext` ;
- récupérer le `WorkflowState` de la conversation ;
- traiter en priorité confirmation, annulation et retry ;
- transmettre la demande à l'agent si aucun workflow ne l'intercepte ;
- appliquer les réponses de clarification ;
- générer des suggestions à partir des exemples d'entraînement.

**Sécurité** :

`require_bearer_token()` exige le format :

```text
Bearer <token>
```

---

## Backend — Workflow Métier

### `backend/core/business/workflow_state.py`

**Rôle** : définit l'état persistant en mémoire d'une action métier.

Le `WorkflowState` conserve :

- l'intention et le scénario ;
- le `BusinessRequest` ;
- le plan d'exécution ;
- les champs manquants ;
- les questions en attente ;
- les réponses collectées ;
- l'erreur et son caractère récupérable ;
- le nombre de retries ;
- la date de dernière mise à jour.

`ALLOWED_TRANSITIONS` est la source de vérité des transitions et empêche notamment les doubles exécutions.

---

### `backend/core/business/workflow_manager.py`

**Rôle** : point d'entrée unique pour les décisions métier avant exécution.

**Responsabilités principales** :

- détecter confirmation, annulation et retry ;
- empêcher une nouvelle exécution si l'action est déjà en cours ;
- valider l'état avant exécution ;
- basculer vers la clarification si l'état est incomplet ;
- sauvegarder le workflow ;
- construire le questionnaire ;
- appliquer et revalider les réponses frontend ;
- poser les questions en cascade ;
- proposer l'ajout d'une autre ligne ;
- construire le message de confirmation ;
- appeler l'executor après confirmation ;
- gérer `COMPLETED`, `FAILED`, les retries et le nettoyage.

---

### `backend/core/business/business_request.py`

**Rôle** : définit le contrat Pydantic structuré d'une demande métier.

**Objets principaux** :

- `TimesheetReference` ;
- `TimeEntryRequest` ;
- `ActionContext` ;
- `BusinessRequest`.

**Intentions supportées** :

- `CREATE_TIMESHEET` ;
- `ADD_TIME_ENTRY` ;
- `ADD_MULTIPLE_TIME_ENTRIES` ;
- `UPDATE_TIME_ENTRY` ;
- `DELETE_TIME_ENTRY` ;
- `CONSULT_TIMESHEET` ;
- `CONFIRM_ACTION` ;
- `CANCEL_ACTION` ;
- `UNKNOWN`.

**Scénarios structurés** :

- `CREATE_EMPTY_TIMESHEET` ;
- `SINGLE_TIME_ENTRY` ;
- `REPEAT_ENTRY_OVER_DATE_RANGE` ;
- `MULTI_PROJECT_SAME_DAY` ;
- `MULTI_TASK_SAME_PROJECT` ;
- `UNKNOWN_SCENARIO`.

---

### `backend/core/business/structured_extractor.py`

**Rôle** : utiliser le LLM comme extracteur structuré, sans lui déléguer la décision d'exécution.

**Responsabilités principales** :

- créer un agent d'extraction avec `output_type=BusinessRequest` ;
- injecter l'intention et le scénario détectés ;
- injecter le contexte utilisateur et temporel ;
- interdire l'invention d'identifiants ;
- extraire séparément les identifiants `PRJ-*` et `TSK-*` ;
- gérer les dates communes à plusieurs entrées ;
- laisser les dates à `null` pour les répétitions basées sur la période réelle d'une feuille TS.

---

### `backend/core/business/intent_classifier.py`

**Rôle** : classifier une intention métier probable avec des règles déterministes.

Il reconnaît notamment :

- création de feuille ;
- ajout d'une ou plusieurs lignes ;
- modification ;
- suppression ;
- consultation ;
- confirmation ;
- annulation.

---

### `backend/core/business/scenario_detector.py`

**Rôle** : détecter le scénario opérationnel à partir de l'intention et du texte.

Il distingue :

- création d'une feuille vide ;
- saisie unique ;
- répétition sur une période ;
- plusieurs projets le même jour ;
- plusieurs tâches sur le même projet.

---

### `backend/core/business/execution_plan.py`

**Rôle** : associer un scénario à un handler et produire un `ExecutionPlan`.

Le registre `SCENARIO_HANDLERS` centralise les handlers disponibles.

---

### `backend/core/business/executors.py`

**Rôle** : traduire un scénario confirmé en appels Integration Hub réels.

**Contrat de retour** :

```json
{
  "answer": "message utilisateur",
  "ok": true,
  "recoverable": false
}
```

**Comportements importants** :

- création d'une feuille vide ;
- création d'une ligne unique ;
- expansion indépendante de chaque entrée sur une ou plusieurs dates ;
- répétition sur jours ouvrables ou tous les jours ;
- détection des écritures partielles ;
- retry autorisé uniquement si aucune écriture n'a réussi ;
- registre central `SCENARIO_EXECUTORS`.

---

## Backend — Clarification Active

### `backend/core/business/clarification_types.py`

**Rôle** : définir le contrat entre backend et frontend pour les questionnaires.

Types de questions supportés :

- `single_choice` ;
- `multi_choice` ;
- `date_picker` ;
- `number_input` ;
- `multiline_text`.

Modèles principaux :

- `ClarificationOption` ;
- `ClarificationQuestion` ;
- `QuestionnaireResponse` ;
- `ClarificationAnswer` ;
- `ClarificationAnswerBatch`.

---

### `backend/core/business/clarification_validator.py`

**Rôle** : valider la demande métier et produire uniquement les questions nécessaires.

**Validations principales** :

- numéro de feuille ;
- projet ;
- tâche ;
- date ;
- catégorie ;
- ajout éventuel d'une autre ligne.

Les tâches et catégories proposées proviennent de l'Integration Hub. Le backend ne doit pas inventer d'options.

Le filtrage est en cascade :

- le projet doit être connu avant de charger les tâches ;
- le projet et le `resource_id` doivent être connus avant de charger les catégories.

---

### `backend/core/business/clarification_builder.py`

**Rôle** : ordonner et mettre en forme les questions.

Ordre prioritaire :

1. numéro de feuille ;
2. projet ;
3. tâche ;
4. date ;
5. catégorie.

---

## Backend — Confirmation

### `backend/core/business/confirmation.py`

**Rôle** : détecter en langage naturel :

- confirmation ;
- annulation ;
- retry.

La détection est tolérante aux variantes françaises et anglaises, tout en tenant compte des négations.

---

### `backend/core/business/confirmation_messages.py`

**Rôle** : construire un récapitulatif spécifique au scénario.

Le message indique selon le cas :

- la feuille concernée ;
- le projet ;
- la tâche ;
- la catégorie ;
- les heures ;
- la date ;
- le nombre de lignes.

---

## Backend — Handlers de Scénarios

### `backend/core/business/handlers/base.py`

Classe abstraite `ScenarioHandler` avec la méthode :

```python
build(message, intent, scenario) -> ExecutionPlan
```

### Handlers disponibles

- `CreateTimesheetHandler` : création d'une feuille vide ;
- `SingleTimeEntryHandler` : création d'une ligne unique ;
- `RepeatEntryHandler` : résolution de période puis création de plusieurs lignes ;
- `MultiProjectSameDayHandler` : une ligne par projet ;
- `MultiTaskSameProjectHandler` : une ligne par tâche.

Les handlers construisent un plan déclaratif. L'écriture réelle est effectuée par les executors après confirmation.

---

## Backend — Résolution des Feuilles de Temps

### `backend/core/business/timesheet_resolution/models.py`

**Rôle** : définir les contrats de résolution.

Objets principaux :

- `ResolvedTimesheetPeriod` ;
- `TimesheetSummary` ;
- `TimesheetLookupResult` ;
- `TimesheetPeriodGranularity`.

---

### `backend/core/business/timesheet_resolution/period_resolver.py`

**Rôle** : transformer un mode temporel structuré en dates absolues, sans appeler d'API.

Modes actuellement gérés :

- `current_week` ;
- `last_week` ;
- `last_month` ;
- `explicit_date` ;
- `explicit_range`.

Le module calcule également :

- les bornes lundi-dimanche ;
- les jours ouvrables ;
- la granularité ;
- le besoin éventuel de clarification ;
- si plusieurs feuilles peuvent être attendues.

---

### `backend/core/business/timesheet_resolution/timesheet_finder.py`

**Rôle** : rechercher les feuilles de l'utilisateur qui chevauchent une période métier.

**Responsabilités principales** :

- appeler `hub_list_timesheets` ;
- normaliser différents formats de réponse Hub ;
- extraire numéro, dates et statut ;
- filtrer par chevauchement de périodes ;
- retourner une feuille sélectionnée automatiquement si une seule correspondance existe.

---

### `backend/core/business/timesheet_resolution/resolution_service.py`

**Statut actuel** : fichier présent mais vide.

Il est réservé à une future orchestration entre :

- la résolution calendaire ;
- la recherche des feuilles ;
- la clarification ;
- la création éventuelle d'une feuille.

---

## Backend — Dates Relatives

### `backend/core/datetime/date_resolver.py`

**Rôle** : résoudre les expressions temporelles relatives les plus fréquentes.

Il construit un `RelativeDateContext` contenant :

- le fuseau horaire ;
- aujourd'hui ;
- hier ;
- demain ;
- début de semaine ;
- fin de semaine.

Le fuseau par défaut est défini par :

```env
FDT_TIMEZONE=Europe/Paris
```

En cas de fuseau invalide, le fallback est `UTC`.

---

## Backend — Outils Métier et SQL

### `backend/tools/functions_tool.py`

**Rôle** : implémenter les outils SQL utilisés par l'agent.

**Responsabilités principales** :

- exécuter des lectures SQL sur Azure Synapse ;
- retourner systématiquement des réponses JSON string ;
- retirer les colonnes techniques de pipeline ;
- fournir le schéma métier simplifié ;
- fournir les jointures validées ;
- exécuter uniquement des requêtes validées ;
- retourner des hints en cas d'erreur SQL.

`get_auth_runtime_status()` fournit un diagnostic sécurisé du mode d'authentification Hub sans exposer de token ou secret.

---

### `backend/tools/hub_functions.py`

**Rôle** : regrouper les fonctions d'appel à l'Integration Hub.

**Responsabilités principales** :

- construire les headers HTTP ;
- utiliser le Bearer token utilisateur lorsqu'il est fourni ;
- récupérer un token technique en fallback ;
- standardiser les réponses API ;
- exécuter les requêtes GET, POST, PUT et DELETE ;
- exposer les fonctions via `HUB_FUNCTIONS`.

```text
auth_header utilisateur disponible
        │
        ├── Oui → utiliser ce token
        └── Non → fallback HUB_BEARER_TOKEN ou DefaultAzureCredential
```

---

### `backend/tools/sql_validator.py`

**Rôle** : protéger Azure Synapse contre les requêtes dangereuses.

**Règles principales** :

- seules les requêtes `SELECT` ou `WITH` sont autorisées ;
- les opérations d'écriture sont bloquées ;
- les commentaires SQL sont interdits ;
- les multi-statements sont interdits ;
- les logs SQL sont sanitizés.

---

### `backend/tools/tools_runner.py`

**Rôle** : parser les arguments JSON et dispatcher les appels vers les outils.

**Statut** : principalement utile pour les anciens chemins d'exécution ou les tests.

---

## Backend — Prompts et Raisonnement Agent

### `backend/core/prompts/system_prompt.py`

**Rôle** : assembler le prompt système final.

Il combine :

- `ROLE_PROMPT` ;
- `RULES_PROMPT` ;
- `SCHEMA_PROMPT` ;
- les exemples few-shot de `training_examples.py`.

---

### `backend/core/prompts/role_prompt.py`

**Rôle** : définir l'identité, le scope et le protocole d'interaction de l'agent.

**Évolutions actuelles** :

- distinction entre analytique et actions métier ;
- utilisation prioritaire du `UserContext` ;
- utilisation automatique du `resource_id` connecté ;
- interprétation des dates relatives ;
- gestion des confirmations et annulations ;
- priorité à la période réelle d'une feuille TS ;
- interdiction d'écrire sans confirmation ;
- règles de réponse Markdown ;
- listes et tableaux obligatoires lorsque la structure le justifie ;
- présentation enrichie des identifiants métier.

---

### `backend/core/prompts/rules_prompt.py`

**Rôle** : définir les règles SQL et les règles d'utilisation des actions métier.

**Points clés** :

- SQL en lecture seule ;
- jointures validées ;
- interdiction de `LIMIT` ;
- `TOP N` uniquement si la question le demande ;
- pas de filtre `APPROVALSTATUS` par défaut ;
- validation des colonnes ;
- correction et retry SQL ;
- actions métier via Integration Hub uniquement ;
- confirmation obligatoire avant écriture ;
- aucun détail technique dans la réponse par défaut.

---

### `backend/core/prompts/schema_prompt.py`

**Rôle** : décrire les tables et concepts métier accessibles à l'agent.

---

### `backend/core/training_examples.py`

**Rôle** : fournir des exemples few-shot pour guider les requêtes SQL.

Ces exemples servent également au système de suggestions contextuelles du backend.

---

## Backend — Observabilité et Sécurité des Données

### `backend/agent/scrubbing/observability.py`

**Rôle** : configurer l'observabilité locale.

**Responsabilités principales** :

- configurer Logfire ;
- activer OpenTelemetry ;
- exporter les traces vers Aspire Dashboard ;
- définir les patterns sensibles ;
- masquer les données RH, financières et techniques ;
- éviter l'exposition du contenu brut des prompts et réponses.

---

### `backend/agent/scrubbing/question_sanitizer.py`

**Rôle** : anonymiser et classifier les questions avant observabilité.

**Sortie typique** :

- hash stable ;
- aperçu anonymisé ;
- catégorie métier ;
- indicateur de détection PII.

---

## Backend — Base de Données

### `backend/database/connection.py`

**Rôle** : centraliser la connexion à Azure Synapse.

**Responsabilités principales** :

- utiliser `DefaultAzureCredential` ;
- obtenir un token Azure pour Synapse ;
- créer un engine SQLAlchemy ;
- injecter le token dans la connexion ODBC ;
- éviter le pooling long terme avec `NullPool`.

---

## Backend — Legacy Azure AI Foundry

### `backend/agent/ia_foundry/create_agent.py`

**Statut** : legacy.

### `backend/agent/ia_foundry/fdt_agent.py`

**Statut** : legacy.

### `backend/agent/ia_foundry/update_agent.py`

**Statut** : legacy.

Avec Pydantic AI, le prompt est chargé localement au démarrage. Ces scripts ne sont plus dans le flux actif.

---

## Frontend — Shell et Authentification

### `frontend/src/main.jsx`

**Rôle** : point d'entrée React.

**Responsabilités principales** :

- importer les styles globaux et le thème ;
- initialiser MSAL ;
- gérer le retour de redirection Microsoft ;
- restaurer le compte actif ;
- monter l'application React ;
- envelopper `App` avec `MsalProvider` ;
- envelopper l'application avec `ThemeProvider`.

---

### `frontend/src/App.jsx`

**Rôle** : shell applicatif.

**Responsabilités principales** :

- vérifier l'état d'authentification via MSAL ;
- afficher `AuthPage` si l'utilisateur n'est pas connecté ;
- afficher `ChatPage` si l'utilisateur est connecté ;
- afficher `AdminDashboard` via `#admin` ;
- gérer la déconnexion avec `logoutRedirect()` ;
- transmettre le nom et l'email du compte actif à `ChatPage`.

---

### `frontend/src/auth/msalConfig.js`

**Rôle** : configurer MSAL.

**Responsabilités principales** :

- charger `VITE_ENTRA_CLIENT_ID` ;
- charger `VITE_ENTRA_TENANT_ID` ;
- charger `VITE_API_SCOPE` ;
- définir `/authentication/login-callback` comme redirect URI ;
- définir le retour après déconnexion ;
- utiliser `sessionStorage` ;
- demander le scope backend et `User.Read`.

---

### `frontend/src/auth/msalInstance.js`

**Rôle** : créer l'instance MSAL partagée.

---

### `frontend/src/auth/getAccessToken.js`

**Rôle** : récupérer le token destiné au backend FDT Agent.

**Stratégie** :

- compte actif ou premier compte disponible ;
- `acquireTokenSilent()` ;
- fallback `acquireTokenRedirect()` si une interaction est requise.

---

### `frontend/src/auth/getGraphAccessToken.js`

**Rôle** : récupérer un token Microsoft Graph avec `User.Read`.

---

## Frontend — API

### `frontend/src/api/agentApi.js`

**Rôle** : client HTTP vers le backend.

**Fonctions principales** :

- `callAgent()` → `POST /ask` ;
- `callClarify()` → `POST /clarify` ;
- `fetchSuggestions()` → `POST /suggest`.

`callAgent()` et `callClarify()` retournent :

- une string pour une réponse conversationnelle classique ;
- un objet `type: "questionnaire"` lorsqu'une clarification est nécessaire.

---

### `frontend/src/api/graphApi.js`

**Rôle** : récupérer la photo de profil Microsoft.

Le fichier appelle :

```text
GET https://graph.microsoft.com/v1.0/me/photo/$value
```

- `404` retourne `null` ;
- une réponse valide est convertie en URL objet ;
- les autres erreurs HTTP lèvent une exception.

---

## Frontend — Page de Chat

### `frontend/src/pages/ChatPage.jsx`

**Rôle** : page principale de l'interface conversationnelle.

**Responsabilités principales** :

- gérer les sessions et messages ;
- persister les conversations et l'identifiant actif ;
- créer, sélectionner, renommer, supprimer et épingler des conversations ;
- envoyer les questions au backend ;
- transmettre l'historique récent ;
- gérer l'annulation avec `AbortController` ;
- régénérer la dernière réponse ;
- afficher les réponses de l'agent ;
- afficher les questionnaires de clarification ;
- afficher les erreurs et permettre un retry ;
- récupérer les suggestions contextuelles ;
- distinguer les messages conversationnels et analytiques ;
- afficher `TypingMessage` ou `ToolGroup` ;
- gérer la sidebar repliable ;
- charger la photo Microsoft ;
- appliquer les préférences de chat ;
- gérer le défilement intelligent ;
- afficher le panneau de paramètres ;
- exposer la déconnexion.

### Types de messages gérés

- `user` ;
- `agent` ;
- `error` ;
- `questionnaire`.

---

## Frontend — Messages du Chat

### `AgentMessage.jsx`

Affiche :

- l'avatar de l'agent ;
- le contenu Markdown ;
- l'heure ;
- les actions Copier et Régénérer.

### `UserMessage.jsx`

Affiche le message utilisateur, l'heure et l'action Copier.

### `ErrorMessage.jsx`

Affiche une erreur lisible avec un bouton Réessayer lorsqu'un callback est disponible.

### `TypingMessage.jsx`

Affiche un indicateur de saisie animé pour les requêtes conversationnelles ou lorsque les Tool Calls sont désactivés.

### `QuestionnaireMessage.jsx`

**Rôle** : afficher et soumettre les questions de clarification.

**Types supportés** :

- choix unique ;
- choix multiple ;
- date ;
- nombre ;
- texte multiligne ;
- saisie libre lorsque le backend l'autorise.

Le composant :

- affiche la progression ;
- valide la présence d'une valeur requise ;
- construit le payload `ClarificationAnswer` ;
- appelle `callClarify()` ;
- accepte un nouveau questionnaire en cascade ou une confirmation finale.

### `MessageActions.jsx`

Utilise `useCopy()` et expose :

- Copier ;
- Régénérer, lorsque demandé.

### `MessageTimestamp.jsx`

Affiche l'heure du message.

### `EmptyConversation.jsx`

Affiche un état vide réutilisable avec un exemple de question.

---

## Frontend — Markdown et Identifiants Métier

### `frontend/src/components/chat/MarkdownRenderer.jsx`

**Rôle** : rendre les réponses de l'agent avec `react-markdown` et `remark-gfm`.

**Fonctionnalités** :

- rendu Markdown standard ;
- support des tableaux et listes GFM ;
- normalisation des identifiants isolés en listes ;
- badges visuels pour :
  - `TSK-*` ;
  - `PRJ-*` ;
  - `EMP-*` ;
  - `MAT-*` ;
  - `RES-*` ;
  - `CAT-*`.

---

## Frontend — Tool Calls

### `ToolGroup.jsx`

**Rôle** : afficher un bloc repliable représentant les étapes de traitement.

Étapes affichées :

1. analyse de la demande ;
2. consultation des données ;
3. traitement des informations ;
4. génération de la réponse.

Le bloc est piloté par `thinkStep` dans `ChatPage`.

### `ToolCallRow.jsx`

Affiche une étape avec :

- icône ;
- libellé ;
- statut `pending`, `running` ou `success` ;
- résultat court.

### `ToolGroup.css`

Gère les animations, les statuts, le responsive et les thèmes clair/sombre.

### `ToolCallsCard.jsx`

**Statut actuel** : fichier présent mais vide.

---

## Frontend — Sidebar

### `Sidebar.jsx`

**Rôle** : orchestrer la navigation latérale.

Fonctionnalités :

- nouveau chat ;
- liste des conversations ;
- groupe des conversations épinglées ;
- conversations récentes ;
- suppression de tout l'historique ;
- accès aux paramètres ;
- affichage de la session utilisateur ;
- mode replié et réouverture au clic.

### `ConversationItem.jsx`

**Rôle** : représenter une conversation.

Actions :

- sélectionner ;
- épingler / désépingler ;
- renommer ;
- supprimer ;
- fermer automatiquement le menu lors d'un clic extérieur.

### `SidebarHeader.jsx`

Affiche le logo, le nom **FDT Agent** et la mention **Assistant IA**.

### `SidebarItem.jsx`

Composant générique pour les actions de sidebar, avec variantes :

- `default` ;
- `primary` ;
- `danger`.

### `SidebarSection.jsx`

Affiche un titre de section lorsque la sidebar n'est pas repliée.

### `UserSessionCard.jsx`

Affiche :

- le nom ;
- l'email ;
- la photo Microsoft ou les initiales ;
- le bouton de déconnexion ;
- un popover de profil en mode replié.

---

## Frontend — Paramètres

### `frontend/src/components/settings/SettingsPanel.jsx`

**Rôle** : afficher une modale de paramètres.

Préférences disponibles :

- thème clair, sombre ou système ;
- langue automatique, français ou anglais ;
- suggestions contextuelles ;
- affichage du bloc Tool Calls ;
- comportement Entrée pour envoyer.

Le composant utilise :

- `ThemeContext` pour l'apparence ;
- `useChatPreferences` pour les préférences de chat.

### `SettingsPanel.css`

Gère :

- la modale ;
- la navigation ;
- les switches ;
- les segments de thème ;
- le menu de langue ;
- les versions clair et sombre ;
- le responsive mobile.

---

## Frontend — Thème

### `frontend/src/context/ThemeContext.jsx`

**Rôle** : fournir un thème global.

Valeurs supportées :

- `light` ;
- `dark` ;
- `system`.

Le contexte :

- persiste le choix dans `localStorage` sous `fdt-agent-theme` ;
- met à jour `data-theme` sur `<html>` ;
- ajoute ou retire la classe `dark` ;
- écoute les changements du thème système.

### `frontend/src/components/ui/ThemeToggle.jsx`

Bouton rapide permettant d'alterner entre clair et sombre selon le thème résolu.

---

## Frontend — Hooks

### `useChatPreferences.js`

Persiste :

- `contextSuggestions` ;
- `showToolCalls` ;
- `enterToSend` ;
- `language`.

Clé :

```text
fdt-agent-chat-preferences
```

### `useCopy.js`

Copie un texte avec `navigator.clipboard` et maintient l'état `copied` pendant deux secondes.

### `useMicrosoftProfilePhoto.js`

Charge la photo Microsoft Graph et révoque l'URL objet au démontage.

### `usePersistentState.js`

Hook générique synchronisant un état React avec `localStorage`.

### `useSmartAutoScroll.js`

- détecte si l'utilisateur est proche du bas ;
- fait défiler automatiquement uniquement dans ce cas ;
- expose un bouton manuel de retour en bas.

---

## Frontend — Composants UI

### `frontend/src/components/ui/button.jsx`

Bouton réutilisable basé sur :

- `class-variance-authority` ;
- `radix-ui` ;
- `cn()` ;
- plusieurs variantes et tailles.

### `frontend/src/components/DotField.jsx`

**Rôle** : fond animé interactif sur canvas.

Fonctionnalités :

- grille dynamique de points ;
- interaction avec le curseur ;
- effet de bulge ou de force ;
- glow SVG ;
- onde optionnelle ;
- adaptation au redimensionnement ;
- optimisation via `memo` et `requestAnimationFrame`.

### `frontend/src/components/DotField.css`

Positionne le canvas et le SVG en fond, sans intercepter les interactions utilisateur.

---

## Frontend — Page d'Administration

### `frontend/src/pages/AdminDashboard.jsx`

**Rôle** : interface d'administration accessible via `#admin`.

**Responsabilités principales** :

- afficher les indicateurs KPI ;
- afficher l'état des services ;
- afficher le journal d'audit ;
- structurer la future interface d'administration.

### Composants associés

- `AdminSidebar.jsx` ;
- `MetricCard.jsx` ;
- `AuditTrailTable.jsx`.

---

## 🔑 Variables d'Environnement

### Backend `.env`

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano

# Azure Synapse
SYNAPSE_DATABASE=SilverLayer

# Integration Hub
HUB_BASE_URL=
OPERATE_BASE_URL=
HUB_SCOPE=
HUB_DATA_AREA_ID=USSI

# Token de test temporaire, si utilisé localement
HUB_BEARER_TOKEN=

# Fuseau utilisé par le résolveur de dates relatives
FDT_TIMEZONE=Europe/Paris
```

### Frontend `.env`

```env
VITE_ENTRA_CLIENT_ID=
VITE_ENTRA_TENANT_ID=
VITE_API_SCOPE=
```

---

## ⚙️ Règles Critiques (Résumé)

| Règle | Détail |
|---|---|
| **T-SQL uniquement** | Utiliser `TOP N`, jamais `LIMIT N` |
| **Lecture seule** | `sql_validator` bloque les écritures SQL |
| **APPROVALSTATUS** | Ne jamais filtrer sans demande explicite |
| **Actions métier** | Passent uniquement par l'Integration Hub |
| **Confirmation** | Obligatoire avant toute écriture |
| **Double confirmation** | Bloquée par les transitions du `WorkflowState` |
| **Clarification** | Les réponses sont revalidées côté backend |
| **Options de questionnaire** | Proviennent du Hub, jamais inventées |
| **resource_id** | Utiliser automatiquement celui du `UserContext` si disponible |
| **Feuille TS fournie** | Sa période réelle est prioritaire |
| **Retry** | Autorisé seulement lorsqu'aucune écriture n'a eu lieu |
| **Écriture partielle** | Aucun retry automatique pour éviter les doublons |
| **Stockage workflow** | In-memory en V1, non distribué et non persistant |
| **Prompt local** | Redémarrer le serveur après modification des prompts |
| **Few-Shot** | Ne pas supprimer les exemples existants |
| **Legacy** | Ne pas modifier `ia_foundry/` sauf rollback |
| **Observabilité** | Aucune donnée sensible brute dans les traces |
| **Markdown** | Réponses structurées en listes ou tableaux si nécessaire |
| **Frontend `/clarify`** | Utilisé pour les réponses de questionnaire |
| **Microsoft Graph** | Scope `User.Read` uniquement pour la photo de profil |
| **Theme** | Clair, sombre ou système, persisté localement |
| **Docstrings** | Google-style sur modules, classes et fonctions publiques |
| **Commentaires** | Français professionnel et sections bien délimitées |

---

## 🚀 Commandes de Référence

### Backend

```bash
uvicorn backend.server.api_server:app --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

Le frontend doit être accessible sur :

```text
http://localhost:3000
```

### Dashboard Admin

```text
http://localhost:3000/#admin
```

### Health Check

```text
http://127.0.0.1:8000/health
```

### Tests

```bash
python -m pytest tests/
python -m pytest tests/ -k "test_agent"
```

### Exploration de données

```bash
python -m tests.test_data
```

### Aspire Dashboard

```bash
docker run --rm -it \
  -p 18888:18888 \
  -p 4317:18889 \
  -p 4318:18890 \
  -e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true \
  --name aspire-dashboard \
  mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

UI Aspire :

```text
http://localhost:18888
```

---