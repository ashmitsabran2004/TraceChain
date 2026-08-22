from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from backend.app.database import Base

class ClaimModel(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # RAW_CLAIM, VERIFIED_CLAIM, DERIVED_CLAIM, FINAL_CLAIM
    agent = Column(String, nullable=False) # research, verification, analysis, final_answer
    status = Column(String, default="UNVERIFIED") # VERIFIED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONFLICTING, UNVERIFIED
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
