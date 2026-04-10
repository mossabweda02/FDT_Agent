"""
Bloc 2 — Schéma complet de la Silver Layer.
Modifie ce fichier quand une table est ajoutée ou que des colonnes changent.

"""

SCHEMA_PROMPT = """
## Schéma Silver Layer — Vues utiles

⚠️ IMPORTANT : Toutes les tables sont dans le schéma **dbo**, pas silver.
Exemple : `dbo.timesheet_header`, `dbo.timesheet_line`, `dbo.ga_resource`

### timesheet_header — En-têtes des feuilles de temps
| Colonne            | Type     | Description                                       |
|--------------------|----------|---------------------------------------------------|
| TIMESHEETNBR       | varchar  | Identifiant unique (ex: TS-0000106)               |
| PERIODFROM         | date     | ⭐ Début de la semaine — filtrer par mois ici     |
| PERIODTO           | date     | Fin de la semaine                                 |
| APPROVALSTATUS     | int      | ⚠️⚠️ Ne JAMAIS filtrer par défaut - voir note    |
| RESOURCE           | int      | ID employé → jointure ga_resource.RECID           |
| Approver           | varchar  | Approbateur                                       |
| DATAAREAID         | varchar  | Entité légale (USSI)                              |
| RECID              | int      | Clé primaire interne                              |
| CREATEDDATE        | datetime | Date de création                                  |

**⚠️ NOTE CRITIQUE SUR APPROVALSTATUS** :
- Valeurs possibles : 1=Draft, 2=Submitted, 3=Approved, 4=Returned, 5=Ready, 6=Ledger, 9=Pending, 10=Transferred
- ❌ NE JAMAIS filtrer par APPROVALSTATUS par défaut
- ✅ Filtrer UNIQUEMENT si l'utilisateur demande explicitement "approuvées" (APPROVALSTATUS = 3)
- ⚠️ INCOHÉRENCE : header.APPROVALSTATUS ≠ ligne.APPROVALSTATUS
  Exemple : TS-0000106 a APPROVALSTATUS = 3 dans header, mais APPROVALSTATUS = 1 dans ses lignes
- Répartition 2026 : Status 1 (70%), Status 2 (11%), Status 3 (19%)

### timesheet_line — Lignes de détail (heures)
| Colonne        | Type    | Description                                           |
|----------------|---------|-------------------------------------------------------|
| TIMESHEETNBR   | varchar | ⭐ Jointure avec timesheet_header                     |
| PROJID         | varchar | Code projet → jointure prj_proj_table.PROJID          |
| ACTIVITYNUMBER | varchar | Code tâche → jointure ga_task.ACTIVITYNUMBER          |
| CATEGORYID     | varchar | Development, QA, Analysis, Support, Vacation          |
| APPROVALSTATUS | int     | ⚠️ Peut être différent de header.APPROVALSTATUS       |
| RESOURCE       | int     | ID employé → jointure ga_resource.RECID               |
| Date           | date    | ⭐ Date exacte de l'entrée d'heures                   |
| QTY            | decimal | ⭐⭐ Heures saisies — toujours SUM(QTY)               |
| INTERNALNOTE   | varchar | Note interne                                          |
| StandardCost   | decimal | Coût standard unitaire                                |
| SalePrice      | decimal | Prix de vente unitaire                                |
| TotalSalePrice | decimal | Prix de vente total                                   |

### ga_resource — Référentiel des employés
| Colonne         | Type    | Description                                          |
|-----------------|---------|------------------------------------------------------|
| RECID           | int     | ⭐ Clé de jointure (= RESOURCE dans les timesheets)  |
| RESOURCEID      | varchar | Code ressource (ex: RES-2924)                        |
| NAME            | varchar | ⭐ Nom complet (ex: Adrien Carduner)                 |
| ACTIVE          | bit     | True = actif                                         |
| PERSONNELNUMBER | varchar | Numéro personnel                                     |

### prj_proj_table — Référentiel des projets
| Colonne           | Type    | Description                                        |
|-------------------|---------|----------------------------------------------------|
| PROJID            | varchar | ⭐ Code projet — clé de jointure (ex: PRJ-00329)   |
| PROJNAME          | varchar | ⭐ Nom du projet (ex: Operate Implémentation)      |
| CUSTACCOUNT       | varchar | Compte client                                      |
| STARTDATE         | date    | Date début projet                                  |
| ENDDATE           | date    | Date fin projet                                    |
| STATUS            | int     | ⚠️ Valeurs : 0=Created, 1=Estimated, 2=Scheduled, 3=InProcess, 4=Completed |
| WORKERRESPONSIBLE | int     | Chef de projet (→ ga_resource.RECID)               |
| PROGRESSION       | decimal | Avancement (%)                                     |

**Projets actifs** : Généralement STATUS IN (1, 2, 3) (Estimated, Scheduled, InProcess)

### ga_task — Référentiel des tâches
| Colonne        | Type     | Description                                           |
|----------------|----------|-------------------------------------------------------|
| ACTIVITYNUMBER | varchar  | ⭐ Clé de jointure (ex: TSK-00130)                    |
| TASKNAME       | varchar  | ⭐ Nom de la tâche (ex: Development, Analysis)        |
| TASKCATEGORY   | varchar  | Development, Analysis, QA, Vacation                   |
| TASKSTATUS     | int      | Statut de la tâche                                    |
| TASKSTARTDATE  | datetime | Date début planifiée                                  |
| TASKFINISHDATE | datetime | Date fin planifiée                                    |
| TASKEFFORT     | decimal  | Effort planifié                                       |
| WORKEDHOURES   | decimal  | Heures travaillées cumulées                           |
| PROGRESSION    | decimal  | Avancement (%)                                        |

### prj_project_assigned_resources — Affectations projet/ressource
| Colonne          | Type     | Description                                         |
|------------------|----------|-----------------------------------------------------|
| PROJID           | varchar  | Code projet                                         |
| RESOURCE         | int      | ID ressource (→ ga_resource.RECID)                  |
| NAME             | varchar  | Nom de la ressource                                 |
| PSAROLESTARTDATE | datetime | Début affectation                                   |
| PSAROLEENDDATE   | datetime | Fin affectation                                     |

### acp_expense_card — Notes de frais
| Colonne               | Type     | Description                                      |
|-----------------------|----------|--------------------------------------------------|
| RecId                 | int      | Clé primaire                                     |
| ResourceRecId         | int      | Employé (→ ga_resource.RECID)                    |
| ProjectRecID          | int      | Projet (→ prj_proj_table.RECID)                  |
| Description           | varchar  | Nature de la dépense                             |
| Date                  | datetime | Date de la dépense                               |
| Status                | int      | Statut de la note de frais                       |
| TotalAmountCompanyCur | decimal  | ⭐ Montant total en devise société               |
| Billable              | bit      | Facturable (True/False)                          |

### hrm_working_day — Calendrier ouvrable
| Colonne                 | Type    | Description                                       |
|-------------------------|---------|---------------------------------------------------|
| DATE                    | date    | ⭐ Jour concerné                                  |
| CLOSED                  | bit     | False = ouvrable, True = fermé                    |
| DAY / WEEK / MONTH      | int     | Numéro jour / semaine / mois                      |
| HCMWORKINGCALENDARRECID | int     | Référence calendrier                              |
""".strip()