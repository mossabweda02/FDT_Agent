# APIs Timesheet

## Consultation

GET /api/timesheet-lines

Objectif :
Consulter les lignes de feuille de temps.

---

## Création

POST /api/timesheet-line

Objectif :
Créer une ligne de feuille de temps.

### Champs affichés à l’utilisateur
- Projet*
- Tâche*
- Catégorie*
- Livrable
- Heure*
- Date *
- Note externe
- Note interne

### Payload API attendu
{
  "timesheetNbr": "TS-******", (il doit la crée automatiquement en consultant la derniere TS de la base et incremente la valeur de la nouvelle créer par exempel si la derno)
  "projId": "....", (recupere tous les ID des projets existant)
  "activityNumber": "....", (recupere tous les ID des taches reliée au projet séléctionné par le user)
  "categoryId": "......", (recupere tous les categories)
  "transDate": "2026-05-20", (par defaut mettre la date d'ajourd'hui)
  "qty": 8, (maximum 8 heures, et s'il essayer de entrer 2 fois la feuille de temps la somme des qty ne doit pas depasser 8 (8 heures))
  "externalNote": "...", 
  "internalNote": "..."
}

### Notes :
- l’utilisateur saisit uniquement les données métier
- les IDs techniques sont récupérés automatiquement
- le numéro de feuille de temps est généré automatiquement
---

## Modification

PUT /api/timesheet-line/{recId}

Objectif :
Modifier une ligne existante.

---

## Suppression

DELETE /api/timesheet-line/{recId}

Objectif :
Supprimer une ligne existante.

---

## Référentiels utilisés

- Projets
- Tâches
- Catégories
- Livrables

Les valeurs doivent être récupérées dynamiquement depuis les APIs métier.