import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class CredentialTemplate(Base, TimestampMixin):
    """
    Configurable, versioned institutional credential template.
    Allows universities and certifiers to define customized issuance templates
    mapped to validated schema types.
    """
    __tablename__ = "credential_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fields_json: Mapped[str] = mapped_column(Text, nullable=False) # JSON schema definitions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization")
