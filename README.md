# 도커 - Q drant 설정 
```docker run -d \ --name qdrant \ -p 6333:6333 \ -p 6334:6334 \ qdrant/qdrant```

# 도커 - Redis 설정
```docker run -d --name redis-dev -p 6379:6379 redis```

# 백엔드 시작 
```uvicorn src.run_app.back_end.fast_api:app```

# 프론트 시작 
```streamlit run src\run_app\front_end\home.py```



----------------
### Redis 접속 & DB 초기화

```docker exec -it redis-dev redis-cli```
```FLUSHDB```
