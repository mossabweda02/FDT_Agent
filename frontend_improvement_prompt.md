# Prompt pour l'Amélioration du Frontend de l'Interface Chatbot

## Objectif
Refondre l'interface utilisateur (UI) du chatbot pour la rendre moderne, modulaire et fonctionnelle, en mettant l'accent sur l'expérience utilisateur (UX) et la clarté des processus de réflexion de l'agent.

---

## 1. Architecture des Composants
Décomposer l'interface actuelle en composants réutilisables et isolés pour faciliter la maintenance et l'évolution :
- **ChatContainer** : Gestionnaire principal de la vue.
- **Sidebar** : Navigation et historique.
- **MessageList** : Affichage des échanges.
- **ThinkingProcess** : Nouveau composant dédié à la visualisation des étapes de l'agent.
- **SettingsModal** : Panneau de configuration utilisateur.

## 2. Visualisation du "Thinking Process" (Réflexion de l'Agent)
Améliorer la section de réflexion pour qu'elle soit plus intuitive et professionnelle :
- **Suppression des icônes clavier** : Remplacer les logos génériques par des icônes vectorielles dédiées (ex: loupe pour la recherche, engrenage pour le traitement, base de données pour les requêtes).
- **Étapes Séquentielles** : Afficher clairement les étapes suivies par l'agent (ex: "Analyse de la question", "Recherche dans la base de données", "Synthèse des résultats").
- **Confidentialité** : Masquer les détails techniques bruts (requêtes SQL, appels API) pour ne montrer que l'intention et l'état d'avancement.

## 3. Fonctionnalités de Messagerie
Améliorer l'interactivité et l'information des messages :
- **Option de Copie** : Ajouter une icône ou un bouton permettant de copier facilement le texte des prompts de l'utilisateur et des réponses de l'agent.
- **Horodatage** : Afficher l'heure d'envoi pour chaque prompt utilisateur et l'heure de réception pour chaque message de l'agent.

## 4. Paramètres et Personnalisation (Settings)
Implémenter un panneau de réglages accessible (maximum 4 options clés) :
- **Thème** : Sélecteur de mode Clair (Light) et Sombre (Dark).
- **Langue** : Choix entre le Français (par défaut) et l'Anglais.
- **Préférences d'affichage** : (Optionnel) Taille de la police ou densité de l'interface.
- **Sécurité** : Gestion simplifiée de la session.

## 5. Gestion de l'Historique et "Latest Prompts"
Ajouter une section "Derniers Prompts" (Latest) en Français :
- **Accès Rapide** : En cliquant sur cette section, l'utilisateur voit ses 5 dernières requêtes.
- **Isolation des Données** : Chaque utilisateur ne doit voir que son propre historique. La sécurité et la non-distribution de l'historique entre utilisateurs sont des priorités absolues pour les étapes futures.

## 6. Suggestions Contextuelles
Après chaque prompt utilisateur, afficher 3 suggestions de questions en lien avec le contexte :
- **Pertinence** : Les suggestions doivent être pertinentes par rapport à la dernière interaction de l'utilisateur.
- **Source d'inspiration** : S'inspirer du fichier `training_examples.py` pour la génération de ces suggestions.
- **Implémentation Frontend** : Le frontend se contentera d'afficher les suggestions reçues du backend sous forme de boutons cliquables.

## 7. Spécifications Backend pour les Suggestions Contextuelles
Pour la génération des suggestions contextuelles, le backend doit implémenter la logique suivante :
- **Endpoint API** : Créer un endpoint API (ex: `/api/suggest_questions`) qui accepte le dernier prompt de l'utilisateur en entrée (format JSON).
- **Analyse Contextuelle** : À la réception d'un prompt utilisateur, le backend doit analyser son contenu pour en extraire le thème principal ou les entités clés.
- **Recherche d'Exemples** : Utiliser le fichier `training_examples.py` comme base de connaissances. Parcourir les exemples (`BASIC_EXAMPLES`, `INTERMEDIATE_EXAMPLES`, `ADVANCED_EXAMPLES`) pour trouver des `user_question` ayant un contexte similaire au prompt actuel.
- **Génération de Suggestions** : Sélectionner 3 questions pertinentes et variées issues de `training_examples.py` ou générer des variantes si nécessaire, en s'assurant qu'elles sont grammaticalement correctes et qu'elles offrent des pistes d'exploration intéressantes pour l'utilisateur.
- **Format de Réponse** : L'API doit retourner une liste de 3 chaînes de caractères (les questions suggérées) au format JSON.
- **Logique d'Appel** : Le frontend appellera cet endpoint API après chaque réponse de l'agent pour obtenir les nouvelles suggestions.

## 8. Design et Esthétique
- **Style Moderne & Minimaliste** : Utiliser des espacements généreux et une typographie claire.
- **Effet Glassmorphism** : Appliquer un effet de "background glass" (fond flouté semi-transparent) sur les composants principaux (ex: Sidebar ou bulles de message) pour un aspect premium.
- **Identité Visuelle** : Intégrer le nouveau logo professionnel (disponible en modes Dark et Light dans les assets).

---

## Instructions Techniques
- Utiliser des bibliothèques d'icônes modernes (ex: Lucide-React, FontAwesome).
- Implémenter le changement de thème via des variables CSS ou un framework comme Tailwind CSS.
- Assurer la réactivité (Responsive Design) pour une utilisation sur mobile et desktop.
- Pour les suggestions contextuelles, prévoir une API backend qui prend en entrée le dernier prompt utilisateur et retourne une liste de 3 questions suggérées.
