from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from backend.app.database import Base

class AgentRunModel(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    input = Column(Text, default="")
    output = Column(Text, default="")
    status = Column(String, default="COMPLETED")
    duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
