from backend.core.business.intent_classifier import classify_business_intent


def test_create_timesheet_intent():
    assert classify_business_intent("Créer ma feuille de temps cette semaine") == "CREATE_TIMESHEET"


def test_add_single_time_entry_intent():
    assert classify_business_intent("Ajoute 5h lundi sur PRJ-00042") == "ADD_TIME_ENTRY"


def test_add_multiple_entries_week_intent():
    assert classify_business_intent("Ajoute 5h du lundi au vendredi sur PRJ-00042") == "ADD_MULTIPLE_TIME_ENTRIES"


def test_add_multiple_entries_projects_intent():
    assert classify_business_intent("Lundi 2h PRJ-00042 et 3h PRJ-00051") == "ADD_MULTIPLE_TIME_ENTRIES"


def test_update_entry_intent():
    assert classify_business_intent("Modifie la ligne de lundi à 6h") == "UPDATE_TIME_ENTRY"


def test_delete_entry_intent():
    assert classify_business_intent("Supprime la ligne de vendredi") == "DELETE_TIME_ENTRY"


def test_confirm_intent():
    assert classify_business_intent("continuer") == "CONFIRM_ACTION"


def test_cancel_intent():
    assert classify_business_intent("annuler") == "CANCEL_ACTION"