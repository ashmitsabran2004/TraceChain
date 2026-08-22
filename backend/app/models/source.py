from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from backend.app.database import Base

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, default="https://evidence.org/doc")
    publisher = Column(String, default="Market Research")
    published_at = Column(String, default="2025-08-01")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
