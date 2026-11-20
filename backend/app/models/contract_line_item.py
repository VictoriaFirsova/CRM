from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContractLineItem(Base):
    """Строка таблицы №1 приложения: документ · продукция · стоимость."""

    __tablename__ = "contract_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    document_name: Mapped[str] = mapped_column(String(500))
    product_name: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    vat_exempt: Mapped[bool] = mapped_column(Boolean, default=True)
    # Расчёт ЗП: ((price * 0.94) - cost) * 0.7, при share_half ÷ 2
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    share_half: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    contract: Mapped["Contract"] = relationship(back_populates="line_items")
