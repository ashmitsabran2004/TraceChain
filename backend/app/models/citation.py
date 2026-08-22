from sqlalchemy import Column, String, Float, Text, ForeignKey
from backend.app.database import Base

class CitationModel(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True, index=True)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    evidence_text = Column(Text, default="")
    status = Column(String, default="VERIFIED")
    confidence = Column(Float, default=1.0)
