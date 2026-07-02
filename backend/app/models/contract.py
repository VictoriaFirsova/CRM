from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ContractKind, ContractStatus, PaymentStatus, ProductionStatus


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    responsible_manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # VARCHAR в БД (scripts/migrate_contract_kinds), не нативный PG enum
    kind: Mapped[ContractKind] = mapped_column(
        Enum(ContractKind, native_enum=False, length=20),
        default=ContractKind.FRAMEWORK,
        index=True,
    )
    parent_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    addendum_number: Mapped[int | None] = mapped_column(nullable=True)
    number_prefix: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    number_sequence: Mapped[int | None] = mapped_column(nullable=True, index=True)
    number_year: Mapped[int | None] = mapped_column(nullable=True, index=True)
    contract_number: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    contract_status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.OPEN)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.NOT_PAID)
    production_status: Mapped[ProductionStatus] = mapped_column(
        Enum(ProductionStatus), default=ProductionStatus.REQUEST
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    advance_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship(back_populates="contracts")
    parent: Mapped["Contract | None"] = relationship(
        remote_side="Contract.id",
        foreign_keys=[parent_contract_id],
        back_populates="addendums",
    )
    addendums: Mapped[list["Contract"]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_contract_id],
    )
    responsible_manager: Mapped["User"] = relationship(
        back_populates="managed_contracts", foreign_keys=[responsible_manager_id]
    )
    line_items: Mapped[list["ContractLineItem"]] = relationship(
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractLineItem.position",
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
