from backend.core.business.execution_plan import build_execution_plan


def test_create_timesheet_plan():
    plan = build_execution_plan(
        "Créer ma feuille cette semaine",
        "CREATE_TIMESHEET",
        "CREATE_EMPTY_TIMESHEET",
    )

    assert plan.requires_confirmation is True
    assert plan.steps[0].tool == "hub_create_timesheet"


def test_repeat_entry_with_timesheet_number_plan():
    plan = build_execution_plan(
        "Ajoute 5h du lundi au vendredi sur PRJ-00042 pour la feuille TS-0000319",
        "ADD_MULTIPLE_TIME_ENTRIES",
        "REPEAT_ENTRY_OVER_DATE_RANGE",
    )

    assert plan.requires_confirmation is True
    assert plan.steps[0].tool == "hub_get_timesheet"
    assert plan.steps[0].params["timesheet_nbr"] == "TS-0000319"
    assert plan.steps[1].tool == "hub_create_timesheet_line"


def test_single_entry_plan():
    plan = build_execution_plan(
        "Ajoute 5h lundi sur PRJ-00042 tâche TSK-00062",
        "ADD_TIME_ENTRY",
        "SINGLE_TIME_ENTRY",
    )

    assert plan.requires_confirmation is True
    assert plan.steps[0].tool == "hub_create_timesheet_line"