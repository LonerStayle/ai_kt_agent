# 도커 - Q drant 설정 (미 세팅시)
```docker run -d --name qdrant -p 6333:6333 qdrant/qdrant```
```(세팅시) docker start qdrant```


# 도커 - Redis 설정 (미 세팅시)
```docker run -d --name redis-dev -p 6379:6379 redis```
```(세팅시) docker start redis-dev ```

# 백엔드 시작 
```uvicorn src.run_app.back_end.fast_api:app```

# 프론트 시작 
```(윈도우) streamlit run src\run_app\front_end\home.py```
```streamlit run src/run_app/front_end/home.py```

# chunk source indexing
``` python -m src.pipe_lines.index ```

----------------
### Redis 접속 & DB 초기화

```docker exec -it redis-dev redis-cli```
```FLUSHDB```
