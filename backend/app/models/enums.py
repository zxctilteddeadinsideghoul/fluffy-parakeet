"""Domain enums, aligned with docs/CONTRACTS_DATA.md section 3."""

import enum


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    LIMITED = "limited"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class VerificationType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    IDENTITY = "identity"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApproachMode(str, enum.Enum):
    CHAT_ONLY = "chat_only"
    ASK_BEFORE_APPROACH = "ask_before_approach"
    MAY_APPROACH = "may_approach"


class PresenceStatus(str, enum.Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    ENDED = "ended"
    EXPIRED = "expired"


class PresenceVisibility(str, enum.Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class CheckInMethod(str, enum.Enum):
    VENUE_QR = "venue_qr"
    STAFF = "staff"
    PARTNER_INTEGRATION = "partner_integration"


class VenueStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class VenuePartnerStatus(str, enum.Enum):
    PROSPECT = "prospect"
    PILOT = "pilot"
    ACTIVE = "active"
    PAUSED = "paused"
