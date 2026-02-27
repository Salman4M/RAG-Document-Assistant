def main():
    print("Hello from rag-document-asistant!")


if __name__ == "__main__":
    main()


from fastapi import FastAPI
from routes.routes import router
from routes.auth import router as auth_router

app = FastAPI(
    title="RAG Document Assistant",
    swagger_ui_init_oauth={
    "usePkceWithAuthorizationCodeGrant": True
    }
)
app.include_router(router)
app.include_router(auth_router)
