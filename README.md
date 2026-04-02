# FDT Agent

Un agent intelligent pour l'automatisation et l'exécution de tâches basées sur des prompts et des outils.

## Description

Le FDT Agent est un système modulaire conçu pour traiter des requêtes utilisateur via des prompts intelligents, interagir avec une base de données, et exécuter des outils personnalisés. Il est organisé en modules pour faciliter la maintenance et l'extension.

## Structure du projet

- `agent/` : Contient l'agent principal (`fdt_agent.py`)
- `core/` : Logique centrale (prompts, exceptions)
- `database/` : Gestion de la connexion à la base de données
- `tools/` : Outils et exécuteurs de fonctions

## Installation

1. Clonez le repository :
   ```bash
   git clone https://github.com/mossabweda02/FDT_Agent.git
   cd FDT_Agent
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurez la base de données dans `database/connection.py`.

## Utilisation

Lancez l'agent principal :
```bash
python agent/fdt_agent.py
```

## Contribution

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonction`)
3. Commitez vos changements (`git commit -am 'Ajout de nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonction`)
5. Ouvrez une Pull Request

## Licence

MIT
