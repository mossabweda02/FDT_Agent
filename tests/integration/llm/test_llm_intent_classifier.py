import pytest

from backend.core.business.llm_intent_classifier import (
    LLMIntentClassificationError,
    classify_intent_with_llm,
    parse_llm_intent_response,
)


@pytest.mark.asyncio
async def test_classify_create_timesheet_with_mocked_llm():
    async def fake_llm_call(system_prompt: str, message: str) -> str:
        assert "CREATE_TIMESHEET" in system_prompt
        assert "feuilles de temps" in message

        return """
        {
            "intent": "CREATE_TIMESHEET",
            "confidence": 0.99,
            "reason": "Création de plusieurs feuilles."
        }
        """

    result = await classify_intent_with_llm(
        (
            "Créer 3 feuilles de temps : une pour cette semaine, "
            "une pour le 14 juin 2026 et l'autre pour la semaine prochaine."
        ),
        llm_call=fake_llm_call,
    )

    assert result.intent == "CREATE_TIMESHEET"
    assert result.confidence == 0.99


@pytest.mark.asyncio
async def test_classify_natural_language_with_typo():
    async def fake_llm_call(system_prompt: str, message: str) -> str:
        return """
        {
            "intent": "CREATE_TIMESHEET",
            "confidence": 0.94,
            "reason": "Demande de création malgré les fautes."
        }
        """

    result = await classify_intent_with_llm(
        "Genere moi une feille de temp pour demain",
        llm_call=fake_llm_call,
    )

    assert result.intent == "CREATE_TIMESHEET"


def test_parse_valid_response():
    result = parse_llm_intent_response(
        """
        {
            "intent": "CONSULT_TIMESHEET",
            "confidence": 0.91,
            "reason": "Consultation du total des heures."
        }
        """
    )

    assert result.intent == "CONSULT_TIMESHEET"
    assert result.confidence == 0.91


def test_parse_markdown_json_response():
    result = parse_llm_intent_response(
        """```json
        {
            "intent": "ADD_TIME_ENTRY",
            "confidence": 0.88,
            "reason": "Ajout d'une seule saisie."
        }
        ```"""
    )

    assert result.intent == "ADD_TIME_ENTRY"


def test_reject_unknown_intent_value():
    with pytest.raises(LLMIntentClassificationError):
        parse_llm_intent_response(
            """
            {
                "intent": "CREATE_PROJECT",
                "confidence": 0.90
            }
            """
        )


def test_reject_invalid_json():
    with pytest.raises(LLMIntentClassificationError):
        parse_llm_intent_response("CREATE_TIMESHEET")