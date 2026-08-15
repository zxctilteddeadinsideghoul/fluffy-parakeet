"""Payment gateway abstraction.

The real provider will be plugged in behind this protocol later; today only
the stub is implemented and it simply marks operations as succeeded.
"""

from __future__ import annotations

import uuid


class PaymentGateway:
    """Stub gateway: every operation succeeds and returns a reference."""

    provider: str = "stub"

    async def authorize(self, *, idempotency_key: str) -> str:
        return f"stub-{uuid.uuid4().hex}"

    async def capture(self, *, provider_reference: str) -> None:
        return None

    async def void(self, *, provider_reference: str) -> None:
        return None


payment_gateway = PaymentGateway()
