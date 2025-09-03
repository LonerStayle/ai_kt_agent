import os, uuid, json, logging
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from FlagEmbedding import BGEM3FlagModel
from common import GlobalSetting


# 로그 세팅했습니다.
logger = logging.getLogger(__name__)

# 임베딩 모델 입니다. 
embedder = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)


# 임베딩 dense 는 의미 기반 유사도에 사용 됩니다. 
def get_embeddings(texts):
    return embedder.encode(texts)["dense_vecs"]


# 인덱싱 실행 함수 
PARSED_FILE = os.path.join(GlobalSetting.DATA_DIR, "all_chunk_list.jsonl")
def run_inddexing(batch_size=32):

    if not os.path.exists(PARSED_FILE):
        logger.error(f"Parsed file not found: {PARSED_FILE}")
        return
    
    # 아래는 임베딩 벡터 차원 확인용 입니다. 
    # 마치 딥러닝 전처리 텐서가 맞아야 작동하듯이 벡터도 인풋 맞춰줘야합니다.
    # 여기서는 차원수를 맞춰야되요 
    sample_vector = get_embeddings(["dimension check"])[0]
    vector_size = len(sample_vector)


    # Qdrent 벡터 DB 세팅(URL 은 일단 로컬 기준 )
    client = QdrantClient(url=GlobalSetting.QDRANT_URL)

    # 벡터 디비구조는 컬렉션(폴더와 비슷)과 데이터로 되어있어서 아래처럼 이름 넣어줘야되요 
    client.recreate_collection(
        collection_name=GlobalSetting.COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size,distance=Distance.COSINE)
    )
    
    segments = [json.load(line) for line in open(PARSED_FILE,"r",encoding="utf-8") ]
    for i in tqdm(range(0, len(segments), batch_size), desc = "indexing"):
        chunk = segments[i:i+batch_size]
        texts = [d["text"] for d in chunk]
        vectors = get_embeddings(texts)
        points = []
        for d, v in zip(chunk, vectors):
            points[
                PointStruct(id=str(uuid.uuid4(), vector = v, payload = d))
            ]

        try: 
            client.upsert(collection_name=GlobalSetting.COLLECTION_NAME, points=points)
        except Exception as e:
            logger.error(f"Failed batch {i}: {e}")
            continue
        
    total = client.count(collection_name=GlobalSetting.COLLECTION_NAME).count
    logger.info(f"Indexing complete. Total vectors: {total}")