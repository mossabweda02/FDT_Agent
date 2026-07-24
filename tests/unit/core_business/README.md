# Tests unitaires

Ce dossier contient les tests unitaires du projet.

Un test unitaire doit vérifier une unité de comportement isolée sans
dépendre d'un service externe.

## Règles

Les tests unitaires ne doivent pas effectuer de vrais appels vers :

- Azure OpenAI ;
- Azure Synapse ;
- Integration Hub ;
- une API HTTP ;
- le système de fichiers externe.

Les dépendances externes doivent être remplacées par des mocks, des
fakes ou des fixtures.

## Organisation

```text
unit/
└── core_business/
    ├── clarification/
    ├── confirmation/
    ├── execution/
    ├── intent/
    ├── request/
    ├── timesheet_resolution/
    └── workflow/