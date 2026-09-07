from fastapi import FastAPI
from app.ingestion import router as ingestion_router
from app.query import router as query_router

app = FastAPI(
    title="Multimodal RAG - Laporan Bank Mandiri",
    description="API untuk tanya jawab dokumen laporan keuangan Bank Mandiri 2025",
    version="1.0.0"
)

app.include_router(ingestion_router, tags=["Ingestion"])
app.include_router(query_router, tags=["Query"])

@app.get("/")
async def root():
    return {
        "message": "Multimodal RAG API siap digunakan!",
        "endpoints": {
            "ingest": "POST /ingest",
            "query": "POST /query"
        }
    }