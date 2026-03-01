def main():
    print("Hello from rag-document-asistant!")


if __name__ == "__main__":
    main()


from fastapi import FastAPI,Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.limiter import limiter
from core.security import decode_token
from routes.routes import router
from routes.auth import router as auth_router


app = FastAPI(
    title="RAG Document Assistant",
    swagger_ui_init_oauth={
    "usePkceWithAuthorizationCodeGrant": True
    }
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def set_user_id_middleware(request:Request, call_next):
    token = request.headers.get("Authorization","").replace("Bearer ", "")
    if token:
        payload = decode_token(token)
        if payload:
            request.state.user_id = payload.get("sub")
    
    return await call_next(request)

app.include_router(router)
app.include_router(auth_router)
