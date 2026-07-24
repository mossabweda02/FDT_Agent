from __future__ import annotations

from datetime import date

from backend.core.business.business_request import BusinessRequest


def normalize_business_request(request: BusinessRequest,*,resolved_common_date: str | None = None,) -> BusinessRequest:
    """Complète les informations communes à plusieurs entrées."""

    common_date = (
        request.timesheet.explicit_date
        or resolved_common_date
    )

    if common_date:
        for entry in request.entries:
            if not entry.date:
                entry.date = common_date

    return request