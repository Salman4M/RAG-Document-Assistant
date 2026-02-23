def main():
    print("Hello from rag-document-asistant!")


if __name__ == "__main__":
    main()


from fastapi import FastAPI
from routes.routes import router

app = FastAPI(title="RAG Document Assistant")
app.include_router(router)