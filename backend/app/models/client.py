from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company_name: Mapped[str] = mapped_column(String(500))
    full_company_name: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    kpp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    legal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bik: Mapped[str | None] = mapped_column(String(9), nullable=True)
    correspondent_account: Mapped[str | None] = mapped_column(String(20), nullable=True)
    settlement_account: Mapped[str | None] = mapped_column(String(20), nullable=True)
    director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    director_name_genitive: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signer_position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signer_basis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    archive_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="owned_clients", foreign_keys=[owner_id])
    contracts: Mapped[list["Contract"]] = relationship(back_populates="client")
    history: Mapped[list["ClientHistory"]] = relationship(
        back_populates="client", order_by="ClientHistory.changed_at.desc()"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="client")


class ClientHistory(Base):
    __tablename__ = "client_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    field_name: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped["Client"] = relationship(back_populates="history")
