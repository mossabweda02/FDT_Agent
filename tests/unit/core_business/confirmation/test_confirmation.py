from backend.core.business.confirmation import is_confirmation, is_cancellation, is_retry


class TestIsConfirmation:
    def test_simple_oui(self):
        assert is_confirmation("oui") is True

    def test_oui_je_confirme(self):
        assert is_confirmation("oui je confirme") is True

    def test_oui_confirme_avec_accent(self):
        assert is_confirmation("oui confirmé") is True

    def test_ok_fais_le(self):
        assert is_confirmation("ok fais-le") is True

    def test_vas_y(self):
        assert is_confirmation("vas-y") is True

    def test_negation_bloque_confirmation(self):
        assert is_confirmation("non je ne confirme pas") is False

    def test_je_ne_confirme_pas(self):
        assert is_confirmation("je ne confirme pas") is False

    def test_message_vide(self):
        assert is_confirmation("") is False

    def test_message_hors_sujet(self):
        assert is_confirmation("combien d'heures ce mois-ci ?") is False


class TestIsCancellation:
    def test_simple_non(self):
        assert is_cancellation("non") is True

    def test_annule_ca(self):
        assert is_cancellation("annule ça") is True

    def test_non_merci(self):
        assert is_cancellation("non merci") is True

    def test_ne_confond_pas_avec_confirmation(self):
        assert is_cancellation("oui je confirme") is False


class TestIsRetry:
    def test_reessayer(self):
        assert is_retry("réessayer") is True

    def test_retente(self):
        assert is_retry("retente") is True

    def test_essaie_encore(self):
        assert is_retry("essaie encore") is True

    def test_not_a_retry(self):
        assert is_retry("oui je confirme") is False