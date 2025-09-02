import torch


device = "cuda" if torch.cuda.is_available() else "cpu"

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = ""