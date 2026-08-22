from backend.app.database import Base, engine
from backend.app.models.investigation import InvestigationModel
from backend.app.models.source import SourceModel
from backend.app.models.claim import ClaimModel
from backend.app.models.citation import CitationModel
from backend.app.models.claim_dependency import ClaimDependencyModel
from backend.app.models.agent_run import AgentRunModel

# Create all database tables on module import
Base.metadata.create_all(bind=engine)
