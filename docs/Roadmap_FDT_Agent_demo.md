# Roadmap consolidée — FDT Agent

> **Objectif principal :** disposer d'une démonstration métier complète et stable le **31 juillet 2026**.
>
> **Hypothèses indispensables :** `Get List Timesheet` et `GetCategoryByTask` doivent être disponibles et suffisamment stables au plus tard le **24 juillet 2026**. Les phases peuvent être menées en parallèle lorsque leurs dépendances le permettent. Les améliorations non indispensables à la démonstration seront poursuivies après le 31 juillet.

## Légende des statuts

* ✅ **Réalisé**
* 🔄 **En cours**
* ⏳ **À faire**
* 🔍 **À valider par les tests**

---
# Phase 1 — Authentification et propagation du contexte utilisateur

**Statut :** ✅ Réalisé

**Date de fin estimée :** **Terminée avant le 21 juillet 2026**
## Objectif

Garantir que toutes les opérations effectuées par l’agent utilisent le contexte de l’utilisateur authentifié.

## Tâches réalisées

* Intégration de l’authentification Microsoft.
* Récupération du contexte utilisateur.
* Propagation sécurisée du contexte vers Integration Hub.
* Utilisation du contexte utilisateur pendant :

  * la recherche des projets ;
  * la recherche des tâches ;
  * la recherche des livrables ;
  * la recherche des catégories ;
  * la consultation des feuilles de temps ;
  * la création ou la modification des données.

## Fichiers concernés

* `user_context.py`
* `api_server.py`
* `agent.py`
* composants communiquant avec Integration Hub.

## Critères de validation

* Aucune donnée d’un autre utilisateur ne peut être utilisée.
* Chaque appel à Integration Hub est associé au contexte utilisateur approprié.

---

# Phase 2 — Architecture métier et orchestration des workflows

**Statut :** ✅ Réalisé

**Date de fin estimée :** **Terminée avant le 21 juillet 2026**
## Objectif

Mettre en place une architecture claire séparant la compréhension assurée par le LLM de la logique métier déterministe du backend.

## Tâches réalisées

* Séparation entre :

  * la compréhension du langage naturel ;
  * l’extraction des données ;
  * la résolution métier ;
  * la validation ;
  * la confirmation ;
  * l’exécution.
* Mise en place du gestionnaire de workflows.
* Mise en place d’un état persistant du workflow.
* Mise en place des exécutors métier.
* Orchestration des différents scénarios.
* Centralisation du catalogue des intentions.
* Structuration des transitions entre les différentes étapes du traitement.

## Fichiers concernés

* `workflow_manager.py`
* `workflow_state.py`
* `executors.py`
* `intent_catalog.py`
* `agent.py`
* `api_server.py`

## Critères de validation

* Le LLM ne déclenche pas directement les actions métier.
* Les actions sont exécutées uniquement après résolution, validation et confirmation.
* Le workflow peut reprendre après une demande de clarification.

--- 

# Phase 3 — Diagnostic et cartographie des erreurs

**Statut :** ✅ Réalisé, à maintenir pendant les corrections

**Date de fin estimée :** **21 juillet 2026**
## Objectif

Établir une cartographie complète des scénarios valides et invalides afin d’identifier précisément l’étape du backend responsable de chaque échec.

## Tâches

* Analyser l’ensemble des scénarios de test.
* Associer chaque échec à l’étape technique concernée :

  * classification de l’intention ;
  * détection du scénario ;
  * extraction structurée ;
  * résolution des dates et des périodes ;
  * résolution des données métier ;
  * recherche des feuilles de temps ;
  * validation des données ;
  * génération de la confirmation ;
  * exécution métier.
* Construire une matrice de couverture des scénarios.
* Identifier les causes racines.
* Prioriser les corrections.
* Mettre à jour la cartographie à chaque nouvelle campagne de tests.

## Fichiers concernés

Aucun changement fonctionnel obligatoire.

Analyse transversale de l’ensemble des composants existants.

## Tests concernés

Tous les scénarios fournis.

## Critères de validation

* Chaque scénario invalide est associé à une cause technique clairement identifiée.
* Chaque correction est rattachée à une phase de la roadmap.
* Les priorités de correction sont définies.

---


# Phase 4 — Classification et compréhension du langage naturel

**Statut :** 🔄 Partiellement validée — corrections ciblées restantes

**Progression estimée :** 75 %

**Date de fin estimée :** **22 juillet 2026**
## Objectif

Améliorer la compréhension des formulations naturelles et assurer une classification correcte des intentions et des scénarios.

## Tâches

* Corriger la classification des intentions.
* Différencier correctement :

  * la création d’une feuille de temps ;
  * l’ajout d’une ou de plusieurs lignes ;
  * la modification d’une ligne ;
  * la consultation d’une feuille ;
  * la consultation de plusieurs feuilles ;
  * la suppression ou l’annulation d’une opération.
* Éviter que la présence du mot « feuille » déclenche automatiquement une création.
* Prendre en charge les formulations naturelles et leurs variantes.
* Comprendre les formulations imprécises lorsque le contexte permet de déduire l’intention.
* Renforcer les règles des prompts sans déplacer la logique métier dans le LLM.
* Gérer les formulations en français naturel, y compris les fautes mineures et les formulations non techniques.

## Exemples attendus

* « Affiche ma feuille de cette semaine. »
* « Ajoute 8 heures aujourd’hui sur le projet Atlas. »
* « Crée la feuille du mois prochain. »
* « Combien d’heures ai-je enregistrées ce mois-ci ? »
* « Mets 4 heures sur la tâche de développement. »

## Fichiers concernés

* `intent_classifier.py`
* `scenario_detector.py`
* `role_prompt.py`
* `rules_prompt.py`
* `intent_catalog.py`

## Tests concernés

* 1.2
* 1.3
* 2
* 6
* 7.2
* 10
* variantes supplémentaires en langage naturel.

## Critères de validation

* L’intention détectée correspond à l’action réellement demandée.
* Les formulations naturelles conduisent au même scénario que les formulations explicites.
* Le mot « feuille » ne suffit pas à déclencher une création.
* L’utilisateur n’a pas besoin de connaître le vocabulaire technique du système.

---

# Phase 5 — Extraction structurée et normalisation

**Statut :** ✅ Validée au niveau composant — intégration end-to-end à confirmer

**Progression estimée :** 90 %

**Date de fin estimée :** **23 juillet 2026**
## Objectif

Fiabiliser l’extraction des informations avant toute résolution métier ou exécution.

## Tâches

* Extraire correctement :

  * les projets ;
  * les tâches ;
  * les catégories ;
  * les livrables ;
  * les heures ;
  * les dates ;
  * les périodes ;
  * les commentaires éventuels.
* Gérer :

  * plusieurs lignes ;
  * plusieurs projets ;
  * plusieurs tâches ;
  * plusieurs livrables ;
  * plusieurs dates ;
  * plusieurs quantités d’heures.
* Propager les informations communes entre plusieurs lignes.
* Distinguer les informations communes des informations propres à chaque ligne.
* Préserver les noms fournis par l’utilisateur.
* Préserver les identifiants déjà résolus.
* Normaliser les formats de dates et d’heures.
* Éviter toute perte d’information entre l’extraction et le workflow métier.
* Détecter les incohérences avant la résolution métier.

## Fichiers concernés

* `structured_extractor.py`
* `business_request.py`
* `business_request_normalizer.py`
* modèles structurés utilisés par l’agent.

## Tests concernés

* 4.2
* 5.2
* 9.1
* 9.2
* cas multi-projets ;
* cas multi-tâches ;
* cas multi-dates.

## Critères de validation

* Toutes les informations exprimées par l’utilisateur sont conservées.
* Les lignes multiples sont séparées correctement.
* Les informations communes sont propagées sans écraser les valeurs spécifiques.
* La sortie de l’extraction est exploitable directement par la résolution métier.

---

# Phase 6 — Résolution des dates et des périodes

**Statut :** 🔄 En cours

**Date de fin estimée :** **24 juillet 2026**
## Objectif

Comprendre les expressions temporelles naturelles et déterminer les dates ou périodes réellement demandées.

## Tâches

Résoudre notamment :

* aujourd’hui ;
* hier ;
* demain ;
* cette semaine ;
* la semaine dernière ;
* la semaine prochaine ;
* le mois courant ;
* le mois précédent ;
* le mois prochain ;
* une date explicite ;
* une plage de dates ;
* une semaine définie par une date ;
* une période exprimée en langage naturel.

## Règles attendues

* Utiliser la date courante et le fuseau horaire de l’utilisateur.
* Normaliser les dates avant toute recherche de feuille.
* Gérer les dates ambiguës.
* Demander une clarification uniquement lorsqu’aucune interprétation fiable n’est possible.
* Conserver la formulation initiale et la période résolue dans le workflow.

## Fichiers concernés

* `date_resolver.py`
* `period_resolver.py`
* `models.py`
* composants de normalisation des requêtes.

## Tests concernés

* 1.2
* 1.3
* 2
* 3.1
* 7.2
* 10

## Critères de validation

* Chaque expression temporelle est convertie en date ou période exploitable.
* Les dates résolues sont cohérentes avec le calendrier métier.
* L’utilisateur n’a pas besoin de fournir systématiquement une date au format technique.

---

# Phase 7 — Recherche et résolution des feuilles de temps

**Statut :** 🔄 En cours — dépend de `Get List Timesheet`

**Date de fin estimée :** **27 juillet 2026**
## Objectif

Permettre à l’agent de retrouver automatiquement la ou les feuilles concernées sans exiger leur numéro.

## Tâches

* Rechercher une feuille à partir :

  * d’un numéro, lorsqu’il est fourni ;
  * d’une date ;
  * d’une semaine ;
  * d’un mois ;
  * d’une période naturelle.
* Gérer les cas suivants :

  * aucune feuille trouvée ;
  * une seule feuille trouvée ;
  * plusieurs feuilles trouvées.
* Récupérer automatiquement une feuille lorsqu’une correspondance unique existe.
* Proposer la création d’une feuille lorsqu’aucune feuille appropriée n’existe.
* Demander à l’utilisateur de choisir lorsque plusieurs feuilles correspondent réellement à la demande.
* Ne pas demander un numéro de feuille lorsque la période suffit à la retrouver.
* Vérifier qu’une feuille n’existe pas déjà avant de proposer sa création.
* Éviter les créations en double.

## Fichiers concernés

* `period_resolver.py`
* `timesheet_finder.py`
* `resolution_service.py`
* `models.py`
* outils de communication avec Integration Hub.

## Tests concernés

* 1.2
* 1.3
* 2
* 3.1
* 7.2
* 10

## Critères de validation

* Le numéro de feuille de temps n’est plus obligatoire.
* Une feuille existante est récupérée automatiquement lorsqu’elle correspond à la période demandée.
* La création est proposée uniquement lorsqu’aucune feuille appropriée n’existe.
* Aucun doublon n’est créé.

---

# Phase 8 — Résolution des données métier

**Statut :** 🔄 En cours — dépend de `GetCategoryByTask`

**Date de fin estimée :** **27 juillet 2026**
## Objectif

Résoudre automatiquement les noms métier exprimés en langage naturel vers les identifiants utilisés par Integration Hub.

## Tâches

* Résoudre :

  * nom du projet → `Project ID` ;
  * nom de la tâche → `Task ID` ;
  * nom de la catégorie → `Category ID` ;
  * nom du livrable → `Deliverable ID`.
* Utiliser exclusivement les données disponibles dans Integration Hub.
* Respecter les relations métier :

  * une tâche doit appartenir au projet sélectionné ;
  * un livrable doit être associé à la tâche sélectionnée ;
  * une catégorie doit être compatible avec l’opération.
* Détecter :

  * une correspondance exacte ;
  * une correspondance unique approchante ;
  * plusieurs correspondances possibles ;
  * une valeur inconnue ;
  * une valeur incompatible avec le contexte.
* Ne jamais inventer un identifiant.
* Ne jamais demander un identifiant technique à l’utilisateur.
* Conserver le nom lisible et l’identifiant résolu dans l’état du workflow.
* Résoudre les éléments dans l’ordre de dépendance :

  1. projet ;
  2. tâche ;
  3. catégorie ;
  4. livrable.

## Fichiers concernés

* `resolution_service.py`
* `tools.py`
* `workflow_execution_helpers.py`
* modèles métier associés.

## Tests concernés

* 3.3
* 4.2
* 5.2
* cas contenant des noms proches ou ambigus.

## Critères de validation

* Les noms métier sont automatiquement convertis vers les identifiants réels.
* Toutes les relations projet, tâche et livrable sont vérifiées.
* Aucun identifiant inventé ou non résolu n’est transmis à l’exécution.

---

# Phase 9 — Clarification Active et assistance conversationnelle intelligente

**Statut :** 🔄 En cours

**Date de fin estimée :** **28 juillet 2026**
## Objectif

Guider intelligemment l’utilisateur lorsque certaines informations obligatoires sont absentes, ambiguës ou incompatibles.

La clarification ne doit pas être une simple validation de champs obligatoires. Elle doit exploiter les données métier disponibles afin de proposer des choix pertinents.

## Champs nécessaires pour une ligne de temps

Selon le scénario métier, les informations nécessaires sont notamment :

* le projet ;
* la tâche associée au projet ;
* la catégorie ;
* le livrable associé à la tâche ;
* le nombre d’heures ;
* la date ou la période concernée ;
* la feuille de temps cible.

## Tâches

* Identifier les informations réellement absentes.
* Distinguer :

  * une valeur manquante ;
  * une valeur ambiguë ;
  * une valeur inconnue ;
  * une valeur incompatible ;
  * une valeur pouvant être déduite automatiquement.
* Déduire automatiquement une information lorsqu’une seule valeur valide est disponible.
* Proposer les projets disponibles lorsqu’aucun projet n’est fourni.
* Proposer les tâches du projet sélectionné.
* Proposer les catégories disponibles.
* Proposer les livrables associés à la tâche.
* Proposer les feuilles correspondant à la période lorsque plusieurs résultats existent.
* Mémoriser les réponses dans l’état du workflow.
* Reprendre le workflow exactement à l’étape interrompue.
* Ne pas recommencer toute l’analyse après chaque réponse.
* Poser une question à la fois lorsque les choix dépendent les uns des autres.
* Regrouper les questions lorsque les informations sont indépendantes et que cela améliore l’expérience utilisateur.
* Éviter les messages génériques tels que :

  * « champ obligatoire manquant » ;
  * « valeur invalide » ;
  * « veuillez fournir un identifiant ».
* Afficher des valeurs lisibles, jamais uniquement des identifiants techniques.

## Exemple attendu

Au lieu de répondre :

> Le champ livrable est manquant.

L’agent doit répondre :

> Pour la tâche « Développement backend », les livrables disponibles sont :
>
> 1. Développement de l’API
> 2. Tests d’intégration
> 3. Documentation technique
>
> Quel livrable souhaitez-vous utiliser ?

## Comportement intelligent attendu

* S’il existe un seul projet possible, le sélectionner automatiquement.
* S’il existe plusieurs projets possibles, les proposer.
* Après sélection du projet, charger uniquement ses tâches.
* Après sélection de la tâche, charger uniquement ses livrables.
* Ne jamais proposer une tâche ou un livrable hors contexte.
* Conserver toutes les informations déjà validées.
* Éviter de redemander une information déjà fournie.

## Fichiers concernés

* `workflow_manager.py`
* `workflow_state.py`
* `resolution_service.py`
* composants de questionnaires interactifs ;
* prompts conversationnels ;
* modèles de clarification.

## Tests concernés

Tous les scénarios incomplets, ambigus ou contenant des valeurs non résolues.

## Critères de validation

* Les clarifications sont pertinentes et contextualisées.
* Les choix proposés proviennent des données réelles d’Integration Hub.
* Les réponses de l’utilisateur sont mémorisées correctement.
* Le workflow reprend sans perte d’information.
* Aucun identifiant technique n’est demandé à l’utilisateur.
* Aucun message générique de champ manquant n’est affiché lorsqu’une proposition intelligente est possible.

---

# Phase 10 — Validation des données et construction du plan d’exécution

**Statut :** 🔄 En cours

**Date de fin estimée :** **28 juillet 2026**
## Objectif

Garantir qu’aucune opération d’écriture n’est préparée avec des données incomplètes, ambiguës ou non résolues.

## Tâches

* Vérifier que tous les champs obligatoires sont présents.
* Vérifier que toutes les références métier sont résolues.
* Vérifier les relations entre :

  * projet ;
  * tâche ;
  * catégorie ;
  * livrable ;
  * feuille de temps.
* Vérifier les dates et les périodes.
* Vérifier le format et la validité du nombre d’heures.
* Détecter les doublons potentiels.
* Construire un plan d’exécution complet et déterministe.
* Séparer clairement :

  * les opérations de création ;
  * les opérations de mise à jour ;
  * les opérations de consultation.
* Bloquer toute exécution lorsque le plan contient :

  * `None` ;
  * un identifiant non résolu ;
  * une valeur ambiguë ;
  * une relation métier invalide.

## Fichiers concernés

* `execution_plan.py`
* `workflow_manager.py`
* `resolution_service.py`
* `executors.py`

## Tests concernés

Tous les scénarios d’écriture.

## Critères de validation

* Le plan contient toutes les informations nécessaires.
* Aucune valeur non résolue n’atteint l’executor.
* Chaque action prévue correspond exactement à la demande de l’utilisateur.

---

# Phase 11 — Confirmation, modification et annulation

**Statut :** 🔄 En cours

**Date de fin estimée :** **29 juillet 2026**
## Objectif

Présenter à l’utilisateur un récapitulatif clair avant toute opération d’écriture et gérer sa décision de manière fiable.

## Tâches

* Générer une confirmation lisible.
* Afficher les noms métier plutôt que les identifiants.
* Présenter :

  * la feuille concernée ;
  * la date ;
  * le projet ;
  * la tâche ;
  * la catégorie ;
  * le livrable ;
  * les heures ;
  * le nombre total d’opérations.
* Gérer :

  * la confirmation ;
  * l’annulation ;
  * la modification ;
  * la correction partielle d’une ligne.
* Conserver le plan d’exécution pendant la confirmation.
* Ne pas relancer une nouvelle classification complète pour une réponse comme :

  * « oui » ;
  * « confirme » ;
  * « annule » ;
  * « change les heures à 6 ».
* Empêcher toute confirmation contenant une valeur `None`, inconnue ou ambiguë.
* Ne pas demander de confirmation pour les opérations de consultation sans effet de bord.

## Fichiers concernés

* `confirmation.py`
* `execution_plan.py`
* `workflow_manager.py`
* `workflow_state.py`
* `executors.py`

## Tests concernés

Tous les scénarios d’écriture et de modification.

## Critères de validation

* La confirmation correspond exactement au plan d’exécution.
* Une annulation ne déclenche aucune opération.
* Une modification met à jour le plan sans perdre les autres informations.
* Les consultations restent sans confirmation.

---

# Phase 12 — Exécution sécurisée et déterministe

**Statut :** 🔄 Sécurisation en cours

**Date de fin estimée :** **29 juillet 2026**
## Objectif

Exécuter les actions métier de manière déterministe et produire un résultat basé sur la réponse réelle d’Integration Hub.

## Tâches

* Vérifier une dernière fois les paramètres transmis.
* Exécuter uniquement un plan validé et confirmé.
* Sécuriser :

  * les créations ;
  * les mises à jour ;
  * les opérations multiples ;
  * les créations de feuilles suivies d’ajouts de lignes.
* Respecter l’ordre des opérations.
* Éviter les doubles exécutions.
* Ajouter des mécanismes d’idempotence lorsque cela est possible.
* Vérifier les réponses d’Integration Hub.
* Gérer les échecs partiels.
* Gérer les erreurs techniques.
* Ne pas annoncer un succès lorsque l’appel métier a échoué.
* Construire le message final à partir du résultat réel.
* Conserver une trace de l’opération exécutée.

## Fichiers concernés

* `executors.py`
* `workflow_execution_helpers.py`
* outils de communication avec Integration Hub.
* `workflow_state.py`

## Tests concernés

Tous les scénarios d’écriture.

## Critères de validation

* Aucune opération incorrecte ou dupliquée.
* Le résultat affiché correspond à la réponse réelle d’Integration Hub.
* Les erreurs partielles sont clairement identifiées.
* Une même confirmation ne peut pas déclencher plusieurs fois la même opération.

---

# Phase 13 — Consultation des feuilles de temps

**Statut :** 🔄 En cours — dépend de `Get List Timesheet`

**Date de fin estimée :** **29 juillet 2026**
## Objectif

Compléter tous les scénarios de consultation sans imposer de confirmation inutile.

## Tâches

* Lister les feuilles de temps.
* Consulter une feuille par :

  * numéro ;
  * date ;
  * semaine ;
  * mois ;
  * période naturelle.
* Afficher :

  * les informations de la feuille ;
  * les lignes enregistrées ;
  * les projets ;
  * les tâches ;
  * les livrables ;
  * les heures par ligne ;
  * le total des heures.
* Gérer plusieurs feuilles sur une même période.
* Afficher clairement les résultats lorsqu’aucune feuille n’existe.
* Proposer la création uniquement lorsque cela est cohérent avec la demande.
* Ne pas demander de confirmation pour une simple consultation.
* Distinguer clairement une consultation d’une création ou d’une modification.

## Fichiers concernés

* `executors.py`
* `resolution_service.py`
* `tools.py`
* `timesheet_finder.py`

## Tests concernés

* 6
* 7.2
* 8
* 10
* variantes de consultation en langage naturel.

## Critères de validation

* Toutes les consultations fonctionnent sans confirmation.
* Les périodes naturelles sont correctement résolues.
* Les résultats affichés correspondent aux données réelles.
* Le total des heures est calculé correctement.

---

# Phase 14 — Gestion avancée des opérations multiples

**Statut :** ⏳ À finaliser pour les scénarios de démonstration

**Date de fin estimée :** **30 juillet 2026**
## Objectif

Fiabiliser les demandes contenant plusieurs lignes, projets, tâches, dates ou feuilles de temps.

## Tâches

* Gérer plusieurs lignes dans une seule demande.
* Gérer plusieurs projets dans une même demande.
* Gérer plusieurs tâches pour un même projet.
* Gérer plusieurs dates ou plusieurs feuilles de temps.
* Propager correctement les valeurs communes.
* Clarifier uniquement les lignes incomplètes ou ambiguës.
* Construire un plan d’exécution indépendant pour chaque ligne.
* Générer un récapitulatif global avant confirmation.
* Gérer les succès et échecs partiels.
* Empêcher qu’une erreur sur une ligne entraîne une duplication des lignes déjà exécutées.

## Fichiers concernés

* `structured_extractor.py`
* `business_request_normalizer.py`
* `workflow_manager.py`
* `execution_plan.py`
* `executors.py`

## Tests concernés

* 4.2
* 5.2
* 9.1
* 9.2
* scénarios multi-projets ;
* scénarios multi-tâches ;
* scénarios multi-feuilles.

## Critères de validation

* Chaque ligne est extraite, résolue, validée et exécutée correctement.
* Les clarifications ciblent uniquement les éléments problématiques.
* Les résultats partiels sont correctement présentés.

---

# Phase 15 — Gestion des erreurs et résilience Integration Hub

**Statut :** ⏳ À finaliser sur les erreurs critiques

**Date de fin estimée :** **30 juillet 2026**
## Objectif

Garantir un comportement fiable et compréhensible lorsque les services externes ne répondent pas normalement.

## Tâches

* Gérer :

  * les délais d’attente ;
  * les erreurs réseau ;
  * les réponses invalides ;
  * les erreurs d’authentification ;
  * les données absentes ;
  * les erreurs métier ;
  * les échecs partiels.
* Distinguer les erreurs temporaires des erreurs fonctionnelles.
* Éviter de perdre l’état du workflow.
* Permettre une nouvelle tentative sans duplication.
* Générer des messages compréhensibles pour l’utilisateur.
* Conserver les détails techniques dans les logs et non dans le message utilisateur.
* Vérifier que les erreurs Integration Hub ne sont pas interprétées comme des données métier vides.

## Fichiers concernés

* `tools.py`
* `executors.py`
* `workflow_execution_helpers.py`
* gestionnaires d’erreurs ;
* composants de journalisation.

## Critères de validation

* Une erreur externe ne produit pas de faux succès.
* Une nouvelle tentative ne crée pas de doublon.
* Le workflow peut être repris lorsque l’erreur est temporaire.
* Les messages utilisateur restent clairs et non techniques.

---

# Phase 16 — Amélioration des prompts et alignement LLM/backend

**Statut :** 🔄 En cours

**Date de fin estimée :** **30 juillet 2026**
## Objectif

Aligner les instructions du LLM avec l’architecture métier existante sans déplacer les règles déterministes dans les prompts.

## Tâches

* Clarifier le rôle du LLM :

  * comprendre ;
  * classifier ;
  * extraire ;
  * reformuler ;
  * générer des réponses conversationnelles.
* Clarifier le rôle du backend :

  * résoudre les données métier ;
  * rechercher les feuilles ;
  * valider ;
  * planifier ;
  * confirmer ;
  * exécuter.
* Interdire au LLM :

  * d’inventer des identifiants ;
  * d’inventer des projets ou des tâches ;
  * d’annoncer une réussite sans résultat backend ;
  * de contourner la validation ou la confirmation.
* Ajouter des exemples positifs et négatifs.
* Harmoniser `role_prompt.py` et `rules_prompt.py`.
* Éliminer les règles contradictoires.
* Réduire les comportements dépendant uniquement de mots-clés.
* Ajouter les règles de Clarification Active.
* Ajouter les règles de reprise du workflow après une réponse courte.

## Fichiers concernés

* `role_prompt.py`
* `rules_prompt.py`
* prompts d’extraction ;
* prompts de classification ;
* prompts de génération des réponses.

## Critères de validation

* Les prompts sont cohérents avec l’architecture backend.
* Les règles métier critiques restent vérifiées par le code.
* Le LLM n’invente aucune donnée absente des sources disponibles.
* Les réponses sont naturelles et adaptées au contexte.

---


# Phase 17 — Migration vers le modèle de production et revalidation LLM

**Statut :** ⏳ À faire

**Date de fin estimée :** **30 juillet 2026**

## Objectif

Remplacer `gpt-4.1-nano` par le modèle de production retenu, **Claude Haiku 4.5**, sans modifier la logique métier déterministe, puis vérifier que les scénarios de démonstration restent stables.

## Positionnement dans la roadmap

Cette phase intervient après la stabilisation des principales fonctions métier et avant la campagne finale de non-régression. Le changement de modèle ne doit pas être réalisé pendant que les erreurs API ou métier principales sont encore en cours de diagnostic.

## Tâches

* Centraliser le fournisseur et le nom du modèle dans la configuration.
* Permettre le retour rapide à `gpt-4.1-nano` en cas de blocage.
* Configurer Claude Haiku 4.5 comme modèle cible de production.
* Rejouer exactement les mêmes scénarios avec les deux modèles.
* Comparer :

  * la classification des intentions ;
  * la détection des scénarios ;
  * l’extraction des projets, tâches, catégories et livrables ;
  * l’extraction des heures, dates et périodes ;
  * le respect du schéma `BusinessRequest` ;
  * la stabilité des réponses conversationnelles.
* Ajuster uniquement les prompts et la configuration lorsque cela est nécessaire.
* Ne pas déplacer de logique métier déterministe vers le nouveau modèle.
* Documenter les différences observées et les corrections appliquées.

## Fichiers concernés

* configuration du fournisseur LLM ;
* `agent.py` ;
* `structured_extractor.py` ;
* `intent_classifier.py` ;
* `role_prompt.py` ;
* `rules_prompt.py` ;
* fixtures et tests comparatifs des modèles.

## Tests concernés

* Tous les scénarios retenus pour la démonstration.
* Tests de conformité du `BusinessRequest`.
* Tests comparatifs `gpt-4.1-nano` / Claude Haiku 4.5.
* Tests de repli vers le modèle précédent.

## Critères de validation

* Le changement de modèle se fait uniquement par configuration.
* Tous les scénarios de démonstration passent avec Claude Haiku 4.5.
* Aucune donnée métier ou aucun identifiant n’est inventé par le modèle.
* Le schéma structuré reste compatible avec le backend.
* Un retour à `gpt-4.1-nano` reste possible sans modification fonctionnelle.

---

# Phase 18 — Tests automatisés, non-régression et stabilisation

**Statut :** 🔄 En cours, campagne finale le 31 juillet

**Date de fin estimée :** **31 juillet 2026**
## Objectif

Garantir la stabilité de l’ensemble du backend et prévenir les régressions.

## Tâches

* Transformer tous les scénarios fonctionnels en tests automatisés `pytest`.
* Ajouter des tests unitaires pour :

  * la classification ;
  * la détection des scénarios ;
  * l’extraction ;
  * la normalisation ;
  * la résolution des dates ;
  * la recherche des feuilles ;
  * la résolution métier ;
  * la Clarification Active ;
  * la validation ;
  * la confirmation ;
  * l’exécution.
* Ajouter des tests d’intégration avec des réponses simulées d’Integration Hub.
* Ajouter des variantes en langage naturel.
* Tester les cas :

  * ambigus ;
  * incomplets ;
  * multi-projets ;
  * multi-tâches ;
  * multi-dates ;
  * multi-feuilles ;
  * erreurs Integration Hub ;
  * confirmations répétées ;
  * interruptions et reprises du workflow.
* Tester les valeurs limites concernant les heures et les dates.
* Vérifier la compatibilité avec le frontend.
* Ajouter les scénarios corrigés à la suite de chaque anomalie.
* Exécuter la suite complète après chaque phase.

## Fichiers concernés

* dossier `tests/`
* fixtures ;
* mocks Integration Hub ;
* données de tests ;
* tests API ;
* tests des workflows.

## Tests concernés

Tous les scénarios existants et leurs variantes.

## Critères de validation

* Tous les scénarios valides passent.
* Les scénarios précédemment invalides sont corrigés.
* Aucune régression n’est détectée.
* Les workflows incomplets reprennent correctement après clarification.
* Les opérations ne sont jamais exécutées deux fois.

---

# Phase 19 — Validation frontend et expérience utilisateur

**Statut :** ⏳ À finaliser pour la démonstration

**Date de fin estimée :** **31 juillet 2026**
## Objectif

Vérifier que les comportements backend et les mécanismes de clarification sont correctement pris en charge par l’interface utilisateur.

## Tâches

* Vérifier l’affichage des questionnaires de clarification.
* Vérifier la sélection des choix proposés.
* Vérifier l’affichage des récapitulatifs.
* Vérifier les confirmations, annulations et modifications.
* Vérifier l’affichage des erreurs.
* Vérifier les scénarios contenant plusieurs lignes.
* Vérifier la conservation du contexte conversationnel.
* Vérifier que les réponses courtes de l’utilisateur sont associées au bon workflow.
* Vérifier l’affichage des résultats de consultation.
* Tester le parcours complet depuis le frontend jusqu’à Integration Hub.

## Composants concernés

* frontend conversationnel ;
* API backend ;
* gestion de session ;
* affichage des questionnaires ;
* affichage des confirmations ;
* affichage des résultats.

## Critères de validation

* Les questionnaires sont utilisables et compréhensibles.
* Le contexte n’est pas perdu entre deux messages.
* Le frontend affiche les résultats réels du backend.
* Aucun identifiant technique inutile n’est visible par l’utilisateur.

---

# Ordre recommandé d’exécution jusqu’à la démonstration

## 21 juillet

1. Finaliser la cartographie des erreurs encore ouvertes.
2. Geler le périmètre exact des scénarios présentés pendant la démonstration.

## 22 juillet

1. Finaliser la classification des intentions.
2. Corriger la détection des scénarios prioritaires.
3. Relancer les tests de diagnostic correspondants.

## 23 juillet

1. Finaliser l’extraction structurée.
2. Valider les demandes simples et multiples.
3. Vérifier la normalisation du `BusinessRequest`.

## 24 juillet

1. Finaliser la résolution des dates et périodes.
2. Valider la disponibilité des API bloquantes.
3. Préparer les mocks de secours pour les tests internes, sans les utiliser pour simuler un succès pendant la démonstration officielle.

## 25 au 27 juillet

1. Intégrer la recherche automatique des feuilles de temps.
2. Intégrer la résolution des projets, tâches, catégories et livrables.
3. Finaliser les clarifications nécessaires aux scénarios de démonstration.

## 28 juillet

1. Finaliser la validation des données.
2. Construire et vérifier le plan d’exécution.
3. Tester la reprise du workflow après une information manquante.

## 29 juillet

1. Finaliser confirmation, annulation et modification.
2. Valider l’exécution complète avec Integration Hub.
3. Finaliser les scénarios de consultation retenus.

## 30 juillet

1. Finaliser les scénarios multiples indispensables à la démonstration.
2. Corriger les erreurs Integration Hub critiques.
3. Finaliser les prompts.
4. Passer à Claude Haiku 4.5.
5. Rejouer la totalité du catalogue de démonstration.

## 31 juillet

1. Exécuter la campagne finale de non-régression.
2. Tester le parcours depuis le frontend.
3. Corriger uniquement les anomalies bloquantes.
4. Effectuer une répétition générale.
5. Réaliser la démonstration officielle.

---

# Jalons de livraison

| Jalon | Date cible | Condition de réussite |
|---|---:|---|
| Compréhension et extraction stabilisées | 23 juillet 2026 | Tests de classification, scénarios et extraction validés |
| Résolution temporelle terminée | 24 juillet 2026 | Dates et périodes naturelles correctement résolues |
| Résolution API et métier intégrée | 27 juillet 2026 | Feuilles, projets, tâches et catégories retrouvés automatiquement |
| Workflow d’écriture complet | 29 juillet 2026 | Validation, confirmation et exécution de bout en bout |
| Modèle de production validé | 30 juillet 2026 | Scénarios de démonstration validés avec Claude Haiku 4.5 |
| Backend et frontend prêts pour la démo | 31 juillet 2026 | Tests finaux, répétition générale et absence de blocage critique |

---

# Priorités recommandées

## Priorité 1 — Compréhension et extraction

* Phase 4 : classification et langage naturel.
* Phase 5 : extraction et normalisation.

Sans une compréhension fiable, les étapes suivantes reçoivent des données incorrectes.

## Priorité 2 — Résolution

* Phase 6 : dates et périodes.
* Phase 7 : recherche des feuilles.
* Phase 8 : données métier.

Ces phases doivent être stabilisées avant d’enrichir les clarifications.

## Priorité 3 — Clarification Active

* Phase 9 : propositions intelligentes et reprise du workflow.

La Clarification Active doit intervenir après les tentatives automatiques de résolution. Elle ne doit demander à l’utilisateur que les informations qui ne peuvent pas être déduites.

## Priorité 4 — Validation et exécution

* Phase 10 : validation et planification.
* Phase 11 : confirmation.
* Phase 12 : exécution sécurisée.

## Priorité 5 — Fonctionnalités complémentaires

* Phase 13 : consultation.
* Phase 14 : opérations multiples.
* Phase 15 : résilience Integration Hub.
* Phase 16 : finalisation des prompts.

## Priorité 6 — Stabilisation

* Phase 17 : tests automatisés.
* Phase 18 : validation frontend et tests end-to-end.

---

# Périmètre obligatoire pour la démonstration du 31 juillet

La démonstration doit prioritairement valider les parcours suivants :

1. Création d’une feuille de temps pour une période naturelle.
2. Ajout d’une ligne simple avec projet, tâche, catégorie, date et heures.
3. Ajout de plusieurs lignes dans une même demande.
4. Résolution des noms métier sans demander les identifiants techniques.
5. Recherche automatique d’une feuille sans demander son numéro.
6. Clarification d’une information réellement manquante ou ambiguë.
7. Présentation du récapitulatif et confirmation avant écriture.
8. Exécution réelle via Integration Hub et affichage du résultat réel.
9. Consultation d’une feuille et affichage du total des heures.
10. Fonctionnement des mêmes parcours avec Claude Haiku 4.5.

Les optimisations avancées, les variantes rares et le durcissement complet de production pourront continuer après la démonstration, à condition qu’ils ne compromettent pas la sécurité ou l’intégrité des données.

---

# Critères globaux de fin de roadmap

La roadmap pourra être considérée comme finalisée lorsque :

* l’utilisateur peut s’exprimer entièrement en langage naturel ;
* aucun identifiant technique n’est obligatoire ;
* les dates et périodes naturelles sont automatiquement résolues ;
* les feuilles de temps sont retrouvées sans numéro ;
* les projets, tâches, catégories et livrables sont résolus depuis Integration Hub ;
* les informations manquantes donnent lieu à des propositions intelligentes ;
* le workflow reprend correctement après clarification ;
* aucune opération d’écriture n’est exécutée sans validation et confirmation ;
* aucune valeur `None` ou non résolue n’est envoyée à Integration Hub ;
* aucune opération n’est exécutée en double ;
* les consultations ne demandent pas de confirmation ;
* tous les scénarios fonctionnels et leurs variantes passent dans la suite de tests automatisés ;
* le frontend est compatible avec les questionnaires, les confirmations et les résultats générés par le backend.
