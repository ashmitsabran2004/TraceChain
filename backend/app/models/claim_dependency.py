from sqlalchemy import Column, Integer, String, ForeignKey
from backend.app.database import Base

class ClaimDependencyModel(Base):
    __tablename__ = "claim_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_claim_id = Column(String, nullable=False, index=True)
    child_claim_id = Column(String, nullable=False, index=True)
    relationship_type = Column(String, default="DERIVED_FROM")
