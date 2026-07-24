from pathlib import Path

import pytest


def pytest_collection_modifyitems(items):
    """
    Applique automatiquement un marqueur selon le dossier du test.
    """

    for item in items:
        path = Path(str(item.path))

        if "unit" in path.parts:
            item.add_marker(pytest.mark.unit)

        elif "integration" in path.parts:
            item.add_marker(pytest.mark.integration)

        elif "diagnostics" in path.parts:
            item.add_marker(pytest.mark.diagnostic)

        if "llm" in path.parts:
            item.add_marker(pytest.mark.live)