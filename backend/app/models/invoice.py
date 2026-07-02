from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InvoiceKind, PaymentRecordStatus


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    kind: Mapped[InvoiceKind] = mapped_column(
        Enum(InvoiceKind, native_enum=False, length=20),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    invoice_date: Mapped[date] = mapped_column(Date)
    file_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[PaymentRecordStatus] = mapped_column(
        Enum(PaymentRecordStatus, native_enum=False, length=20),
        default=PaymentRecordStatus.PENDING,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contract: Mapped["Contract"] = relationship(back_populates="invoices")
