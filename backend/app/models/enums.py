import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    VIEWER = "VIEWER"


class ContractKind(str, enum.Enum):
    FRAMEWORK = "FRAMEWORK"
    ADDENDUM = "ADDENDUM"


class ContractStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PaymentStatus(str, enum.Enum):
    NOT_PAID = "NOT_PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class ProductionStatus(str, enum.Enum):
    REQUEST = "REQUEST"
    LAYOUT = "LAYOUT"
    SCAN = "SCAN"
    READY = "READY"


class PaymentRecordStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELED = "CANCELED"


class DocumentType(str, enum.Enum):
    CONTRACT = "CONTRACT"
    INVOICE = "INVOICE"
    ACT = "ACT"
    SCAN = "SCAN"
    OTHER = "OTHER"


class InvoiceKind(str, enum.Enum):
    ADVANCE = "ADVANCE"
    BALANCE = "BALANCE"
    FULL = "FULL"
