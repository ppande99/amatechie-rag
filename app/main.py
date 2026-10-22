from fastapi import FastAPI

from app.api.ask import router as ask_router

app = FastAPI(title="amatechie-rag")
app.include_router(ask_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
