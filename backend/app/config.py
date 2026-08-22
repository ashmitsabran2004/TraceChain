from dotenv import load_dotenv

load_dotenv()

# Configuration for Citation system
# List of cue words indicating a causal relationship (case-insensitive)
CAUSAL_CUES = [
    "because",
    "due to",
    "caused by",
    "resulted in",
    "leads to",
    "as a result of",
]
