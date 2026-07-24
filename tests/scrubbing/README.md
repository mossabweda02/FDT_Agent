# Tests de scrubbing

Ce dossier vérifie la protection des données sensibles avant leur
utilisation dans les logs, les prompts ou les outils.

## Périmètre

Les tests couvrent notamment :

- les secrets ;
- les informations RH ;
- les informations financières ;
- les champs SQL et LLM ;
- les faux positifs ;
- les expressions régulières ;
- les attributs OpenTelemetry ;
- le score de scrubbing ;
- la sanitisation des questions.

## Objectifs

Le scrubbing doit :

- détecter les données sensibles ;
- éviter d'exposer les secrets dans les logs ;
- limiter les faux positifs ;
- conserver suffisamment de contexte pour le diagnostic ;
- retourner des attributs compatibles avec l'observabilité.

## Exécution

```powershell
python -m pytest tests/scrubbing -v