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


class MediaModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApproachMode(str, enum.Enum):
    CHAT_ONLY = "chat_only"
    ASK_BEFORE_APPROACH = "ask_before_approach"
    MAY_APPROACH = "may_approach"


class CommunicationGoal(str, enum.Enum):
    DATING = "dating"
    FRIENDS = "friends"
    COMPANY_TONIGHT = "company_tonight"
    NETWORKING = "networking"
    CASUAL_CHAT = "casual_chat"


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


class TokenStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class DrinkOfferStatus(str, enum.Enum):
    PAYMENT_AUTHORIZED = "payment_authorized"
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REDEEMED = "redeemed"


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    AUTHORIZATION_PENDING = "authorization_pending"
    AUTHORIZED = "authorized"
    CAPTURE_PENDING = "capture_pending"
    CAPTURED = "captured"
    VOID_PENDING = "void_pending"
    VOIDED = "voided"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"
    FAILED = "failed"


class RedemptionStatus(str, enum.Enum):
    CREATED = "created"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ARCHIVED = "archived"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class ConnectionStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    BLOCKED = "blocked"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    BLOCKED = "blocked"


class MessageType(str, enum.Enum):
    TEXT = "text"
    SYSTEM = "system"
