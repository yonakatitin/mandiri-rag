import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.vectorstore import retrieve_chunks
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    n_results: int = 5

@router.post("/query")
async def query_document(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")
    
    try:
        # 1. Retrieve chunks relevan dari ChromaDB
        chunks = retrieve_chunks(request.question, request.n_results)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="Tidak ada dokumen yang ditemukan")
        
        # 2. Susun context dari chunks
        context = ""
        for i, chunk in enumerate(chunks):
            context += f"\n[Sumber: Halaman {chunk['page']}, Tipe: {chunk['type']}]\n"
            context += chunk["content"]
            context += "\n---\n"
        
        # 3. Buat prompt untuk Gemini
        prompt = f"""Kamu adalah asisten analis dokumen keuangan Bank Mandiri.
Jawab pertanyaan berikut berdasarkan konteks yang diberikan.
Jika informasi tidak ada dalam konteks, katakan tidak tersedia.
Jawab dalam Bahasa Indonesia secara jelas dan terstruktur.

Konteks:
{context}

Pertanyaan: {request.question}

Jawaban:"""
        
        # 4. Generate jawaban dengan Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        # 5. Susun metadata sumber
        sources = []
        for chunk in chunks:
            sources.append({
                "page": chunk["page"],
                "type": chunk["type"]
            })
        
        return {
            "question": request.question,
            "answer": response.text,
            "sources": sources
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saat query: {str(e)}")