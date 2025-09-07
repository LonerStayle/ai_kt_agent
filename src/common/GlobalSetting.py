import torch, os

device = "cuda" if torch.cuda.is_available() else "cpu"

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "kpop_demon_hunters"

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
DATA_DIR = os.path.join(BASE_DIR, "data")

MODEL_NAME = "midm-2.0-base-instruct"