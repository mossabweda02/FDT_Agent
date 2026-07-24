import pytest

from backend.core.business.intent_service import resolve_business_intent


@pytest.mark.asyncio
async def test_uses_deterministic_classifier_before_llm():
    llm_was_called = False

    async def fake_llm_call(system_prompt: str, message: str) -> str:
        nonlocal llm_was_called
        llm_was_called = True

        return """
        {
            "intent": "UNKNOWN",
            "confidence": 0.0
        }
        """

    result = await resolve_business_intent(
        "Créer une feuille de temps pour cette semaine",
        llm_call=fake_llm_call,
        enable_llm_fallback=True,
    )

    assert result == "CREATE_TIMESHEET"
    assert llm_was_called is False


@pytest.mark.asyncio
async def test_uses_llm_when_deterministic_classifier_returns_none():
    async def fake_llm_call(system_prompt: str, message: str) -> str:
        return """
        {
            "intent": "CREATE_TIMESHEET",
            "confidence": 0.96,
            "reason": "Demande de génération d'une feuille."
        }
        """

    result = await resolve_business_intent(
        "Fabrique-moi mon document de temps pour demain",
        llm_call=fake_llm_call,
        enable_llm_fallback=True,
    )

    assert result == "CREATE_TIMESHEET"


@pytest.mark.asyncio
async def test_does_not_call_llm_when_fallback_is_disabled():
    async def fake_llm_call(system_prompt: str, message: str) -> str:
        raise AssertionError("Le LLM ne doit pas être appelé.")

    result = await resolve_business_intent(
        "Message actuellement non reconnu",
        llm_call=fake_llm_call,
        enable_llm_fallback=False,
    )

    assert result is None


@pytest.mark.asyncio
async def test_rejects_low_confidence_llm_result():
    async def fake_llm_call(system_prompt: str, message: str) -> str:
        return """
        {
            "intent": "CREATE_TIMESHEET",
            "confidence": 0.40,
            "reason": "Demande ambiguë."
        }
        """

    result = await resolve_business_intent(
        "Fais-moi quelque chose pour demain",
        llm_call=fake_llm_call,
        enable_llm_fallback=True,
    )

    assert result is None


@pytest.mark.asyncio
async def test_llm_failure_does_not_break_workflow():
    async def failing_llm_call(system_prompt: str, message: str) -> str:
        raise TimeoutError("Timeout du modèle")

    result = await resolve_business_intent(
        "Demande non reconnue",
        llm_call=failing_llm_call,
        enable_llm_fallback=True,
    )

    assert result is None

@pytest.mark.asyncio
async def test_llm_fallback_with_generation_synonym():
    async def fake_azure_call(
        system_prompt: str,
        user_message: str,
    ) -> str:
        assert "intentions métier" in system_prompt
        assert "fabrique" in user_message.lower()

        return """
        {
            "intent": "CREATE_TIMESHEET",
            "confidence": 0.97,
            "reason": "L'utilisateur demande la création d'une feuille."
        }
        """

    result = await resolve_business_intent(
        "Fabrique-moi une feuille pour la semaine prochaine",
        llm_call=fake_azure_call,
        enable_llm_fallback=True,
        minimum_confidence=0.75,
    )

    assert result == "CREATE_TIMESHEET"