from fastapi import FastAPI

app = FastAPI()

# 루트 엔드포인트
@app.get("/title")
def read_root():
    return {"title": "K 테크 에이전트 화이팅!!"}

# 파라미터 받는 엔드포인트
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str = None):
#     return {"item_id": item_id, "query": q}


