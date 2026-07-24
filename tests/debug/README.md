# Scripts de debug

Ce dossier contient des scripts temporaires utilisés pour examiner le
comportement interne du projet pendant le développement.

Ces fichiers ne constituent pas nécessairement des tests automatisés.

## Exemples d'utilisation

Les scripts peuvent servir à inspecter :

- les métadonnées des projets ;
- les informations des tâches ;
- la résolution d'une feuille de temps ;
- les appels vers Integration Hub ;
- les données intermédiaires du workflow.

## Règles

Les scripts de debug :

- ne doivent pas être exécutés dans la suite Pytest standard ;
- ne doivent pas commencer par `test_` ;
- ne doivent pas contenir de secrets ;
- doivent être supprimés lorsqu'ils ne sont plus utiles ;
- doivent avoir un nom décrivant clairement leur objectif.

Exemple :

```text
debug_project_metadata.py
debug_timesheet_resolution.py