from fastapi import FastAPI

app = FastAPI(title="amatechie-rag")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
