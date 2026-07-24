from backend.core.business.business_types import BusinessScenario
from backend.core.business.scenario_detector import detect_business_scenario


def test_create_empty_timesheet_scenario():
    result = detect_business_scenario(
        "Créer ma feuille de temps cette semaine",
        "CREATE_TIMESHEET",
    )
    assert result.scenario == BusinessScenario.CREATE_EMPTY_TIMESHEET


def test_single_time_entry_scenario():
    result = detect_business_scenario(
        "Ajoute 5h lundi sur PRJ-00042 tâche TSK-00062",
        "ADD_TIME_ENTRY",
    )
    assert result.scenario == BusinessScenario.SINGLE_TIME_ENTRY


def test_repeat_entry_over_date_range_scenario():
    result = detect_business_scenario(
        "Ajoute 5h du lundi au vendredi sur PRJ-00042 tâche TSK-00062",
        "ADD_MULTIPLE_TIME_ENTRIES",
    )
    assert result.scenario == BusinessScenario.REPEAT_ENTRY_OVER_DATE_RANGE


def test_multi_project_same_day_scenario():
    result = detect_business_scenario(
        "Lundi 2h PRJ-00042 et 3h PRJ-00051",
        "ADD_MULTIPLE_TIME_ENTRIES",
    )
    assert result.scenario == BusinessScenario.MULTI_PROJECT_SAME_DAY


def test_multi_task_same_project_scenario():
    result = detect_business_scenario(
        "Ajoute lundi 2h sur TSK-00062 et 3h sur TSK-00063 pour PRJ-00042",
        "ADD_MULTIPLE_TIME_ENTRIES",
    )
    assert result.scenario == BusinessScenario.MULTI_TASK_SAME_PROJECT


def test_unknown_scenario():
    result = detect_business_scenario(
        "Bonjour",
        None,
    )
    assert result.scenario == BusinessScenario.UNKNOWN_SCENARIO