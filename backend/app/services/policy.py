"""Product policy decisions isolated per docs/CONTRACTS_DATA.md section 11."""

from app.models.enums import ApproachMode
from app.schemas.discovery import AvailableAction


def drink_offer_allowed(requires_connection: bool) -> bool:
    """Whether sending a drink offer is allowed by product policy.

    Contract TBD #1: the requirement of an accepted ContactRequest before a
    drink offer is a product decision, isolated here and defaulting to off.
    """
    return not requires_connection


def available_actions(
    mode: ApproachMode, drink_offer_allowed: bool = False
) -> list[AvailableAction]:
    """Actions the viewer may take on a visible profile.

    Per contract TBD #1 and #7 the drink action is not offered until the
    product policy allows offers without an accepted contact request; the
    chat_only mode never allows ask_to_approach.
    """
    actions: list[AvailableAction] = ["contact"]
    if drink_offer_allowed:
        actions.append("drink")
    if mode != ApproachMode.CHAT_ONLY:
        actions.append("ask_to_approach")
    return actions
