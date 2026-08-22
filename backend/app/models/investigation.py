from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text
from backend.app.database import Base

class InvestigationModel(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    status = Column(String, default="COMPLETED")
    final_answer = Column(Text, default="")
    integrity_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
