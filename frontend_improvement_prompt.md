# Spécifications Techniques Finales : Refonte Full-Stack "Agent-FDT"

## 1. Rôles et Objectifs
**Rôle :** Expert Full-Stack UI/UX Engineer & Architecte React.
**Objectif :** Refondre l'interface utilisateur pour créer l'application **"Agent-FDT"** (anciennement Chronos-FDT). L'interface doit être premium, ultra-réactive, et corriger les bugs fonctionnels actuels tout en intégrant des animations modernes.

---

## 2. Architecture et Structure (Phase 1)

### 2.1 Modularité et Nettoyage
- **Composant Principal :** Le fichier `App.jsx` doit être allégé (max 100-150 lignes). Toute la logique métier, les appels API et les sous-composants doivent être déportés dans `/components`, `/hooks` et `/services`.
- **Mise en Page :** L'interface ne doit pas s'étaler sur toute la largeur. Utiliser un conteneur centré (`max-w-6xl mx-auto`) pour une lecture confortable.

### 2.2 Navigation et Identité
- **Nom de l'Application :** Remplacer partout "Chronos-FDT" par **"Agent-FDT"**.
- **Barre de Navigation (Navbar) :** Remplacer l'indicateur "Connecté" basique par une section profil plus élégante (ex: Avatar utilisateur avec menu déroulant, statut de connexion stylisé avec une pastille lumineuse).
- **Icônes :** Utiliser exclusivement la bibliothèque **Lucide-React**. Si elle n'est pas installée, indiquer la commande : `npm install lucide-react`.

---

## 3. Fonctionnalités et Corrections

### 3.1 Paramètres et Langue (Settings)
- **Correction Langue :** Fixer le sélecteur de langue (FR/EN). S'assurer que le changement d'état (state) déclenche bien la traduction de l'interface (utiliser un contexte ou un hook de traduction).
- **Thèmes :** Améliorer les modes Clair et Sombre.
  - *Mode Sombre :* Utiliser des gris profonds (#0f172a) avec des accents cyan.
  - *Mode Clair :* Utiliser des blancs cassés avec des ombres douces pour un aspect papier premium.
- **Nouveaux Paramètres (Total 4) :**
  1. **Thème** (Clair/Sombre/Système).
  2. **Langue** (Français/English) - *À FIXER*.
  3. **Densité de l'UI** (Compact/Confortable).
  4. **Notifications Sonores** (Activé/Désactivé).

### 3.2 Messagerie et Suggestions
- **Horodatage et Copie :** Afficher l'heure pour chaque message et ajouter un bouton "Copier" stylisé.
- **Suggestions Automatiques :** Activer l'affichage de **3 questions suggestions** immédiatement après chaque réponse de l'agent. Ces suggestions doivent être cliquables et envoyer directement le texte dans le chat.
- **Nommage des Conversations :** Implémenter un nommage statique dans la Sidebar avec un commentaire : *"TODO: Rendre dynamique après intégration de la base de données"*.

---

## 4. Spécifications Backend (Suggestions)
- **Endpoint :** `/api/suggest_questions` (FastAPI/Python).
- **Logique :** Analyser le dernier message pour retourner 3 questions cohérentes extraites de `training_examples.py`.

---

## 5. Esthétique et Animations (Phase 2)

### 5.1 Glassmorphism et 3D
- **Effets :** Utiliser `backdrop-blur-md` et des bordures `border-white/10` pour un effet de verre.
- **Animations :** Utiliser **Framer Motion** (`npm install framer-motion`).
  - Apparition des messages en "fade-in slide-up".
  - Micro-animations 3D sur les cartes de suggestions (léger tilt au survol).
  - Transition fluide (0.3s) lors du changement de thème.

---

## 6. Contraintes et Livrables
- **Installation :** Si des packages manquent (framer-motion, lucide-react), les lister clairement au début de la réponse.
- **Code :** Fournir une structure de fichiers propre.
- **Commentaires :** Indiquer explicitement les zones de code statiques qui devront être liées à la base de données plus tard.
