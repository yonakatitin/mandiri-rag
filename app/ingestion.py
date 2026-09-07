import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.parser import parse_pdf
from app.chunker import chunk_documents
from app.vectorstore import store_chunks

router = APIRouter()

UPLOAD_DIR = "data"

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    # Validasi file PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File harus berformat PDF")
    
    # Simpan file PDF ke folder data
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    try:
        # 1. Parse PDF
        print(f"Parsing PDF: {file.filename}")
        parsed_chunks = parse_pdf(file_path)
        print(f"Total parsed chunks: {len(parsed_chunks)}")
        
        # 2. Chunking
        print("Chunking dokumen...")
        final_chunks = chunk_documents(parsed_chunks)
        print(f"Total final chunks: {len(final_chunks)}")
        
        # 3. Simpan ke vector store
        print("Menyimpan ke ChromaDB...")
        total_stored = store_chunks(final_chunks)
        print(f"Total tersimpan: {total_stored}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_parsed_chunks": len(parsed_chunks),
            "total_stored_chunks": total_stored
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saat ingestion: {str(e)}")