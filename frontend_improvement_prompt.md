# Spécifications Techniques : Refonte Full-Stack de l'Interface FDT Agent

## 1. Rôles et Objectifs
**Rôle :** Expert Full-Stack UI/UX Engineer & Architecte React.
**Objectif :** Transformer l'interface actuelle du chatbot en une application web premium, modulaire et performante. L'accent doit être mis sur la clarté du "Thinking Process", l'interactivité utilisateur et une esthétique moderne (Glassmorphism).

---

## 2. Architecture et Structure (Phase 1)

### 2.1 Modularité du Code
- **Décomposition des Composants :** Extraire la logique de `App.jsx` vers des composants atomiques situés dans `/components`.
- **Composants Clés :** `Sidebar`, `ChatContainer`, `MessageItem`, `ThinkingStep`, `SettingsModal`, `SuggestionBar`.
- **Gestion d'État :** Utiliser des hooks React (`useState`, `useEffect`, `useContext`) pour une gestion fluide sans alourdir le composant principal.

### 2.2 Mise en Page et UX
- **Résolution :** L'interface ne doit pas occuper toute la largeur de l'écran sur les grands moniteurs. Utiliser un conteneur avec une largeur maximale (ex: `max-w-5xl` ou `max-w-6xl`) et un centrage automatique (`mx-auto`).
- **Nommage des Conversations :** Implémenter une fonction de nommage statique pour les conversations dans la Sidebar.
  - *Note technique :* Ajouter un commentaire dans le code indiquant que ce nommage deviendra dynamique lors de l'intégration de la persistance en base de données.
- **Horodatage et Copie :** Chaque message (User/Agent) doit afficher l'heure d'envoi et inclure un bouton "Copier" discret mais accessible.

---

## 3. Fonctionnalités Avancées

### 3.1 Visualisation du "Thinking Process"
- **Remplacement des Icônes :** Éliminer les icônes de clavier. Utiliser des icônes vectorielles (Lucide-React) :
  - Loupe pour l'analyse.
  - Base de données pour les requêtes SQL.
  - Check-circle pour la finalisation.
- **Étapes Séquentielles :** Afficher les étapes de réflexion de manière chronologique, en masquant les requêtes techniques brutes pour l'utilisateur final.

### 3.2 Système de Suggestions Contextuelles (Back-to-Front)
- **Backend :** Créer un endpoint `/api/suggest_questions` qui analyse le dernier prompt.
- **Logique :** Extraire 3 questions pertinentes depuis `training_examples.py` basées sur le contexte actuel.
- **Frontend :** Afficher ces suggestions sous forme de "pills" cliquables à la fin de chaque réponse de l'agent.

### 3.3 Paramètres (Settings)
- **Interface :** Modal de réglages avec 4 options maximum :
  1. Switch Thème (Clair/Sombre).
  2. Sélecteur de Langue (FR par défaut, EN).
  3. Gestion de session/sécurité.
  4. Préférences d'affichage.

---

## 4. Esthétique et Animations (Phase 2)

### 4.1 Design Visuel
- **Glassmorphism :** Appliquer des effets de flou d'arrière-plan (`backdrop-blur`) et des bordures semi-transparentes sur la Sidebar et les bulles de message.
- **Identité :** Utiliser les logos officiels (`assets/logo_light.png` et `assets/logo_dark.png`) selon le thème actif.

### 4.2 Animations 3D et Transitions
- **Bibliothèques :** Utiliser `Framer Motion` ou `Three.js` (si nécessaire) pour des transitions fluides.
- **Animations Recommandées :**
  - Entrée progressive des messages avec un léger effet d'élévation.
  - Transition fluide entre les thèmes (Dark/Light).
  - Micro-interactions sur les boutons et les suggestions (hover effects, scale).
  - Animation de chargement "Thinking" élégante et non intrusive.

---

## 5. Contraintes et Livrables

### 5.1 Contraintes Techniques
- **Performance :** Le fichier `App.jsx` doit rester léger (moins de 150 lignes), toute la logique doit être déportée.
- **Responsive :** Parfaitement fonctionnel sur Mobile, Tablette et Desktop.
- **Sécurité :** Prévoir l'isolation des données par utilisateur (préparation pour la phase d'historisation).

### 5.2 Livrables Attendus
1. **Code Source :** Structure de dossiers organisée (`/components`, `/hooks`, `/assets`, `/services`).
2. **Backend :** Script Python/FastAPI pour l'endpoint de suggestions.
3. **Documentation :** Commentaires clairs dans le code pour les parties statiques destinées à devenir dynamiques.
