import os
import chromadb
from google import genai
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "mandiri_rag"

google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def get_embedding(text: str) -> list:
    response = google_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
    )
    return collection

def store_chunks(chunks: list):
    collection = get_collection()
    
    documents = []
    metadatas = []
    ids = []
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        print(f"Embedding chunk {i+1}/{len(chunks)}...")
        embedding = get_embedding(chunk["content"])
        documents.append(chunk["content"])
        metadatas.append({
            "page": chunk["page"],
            "type": chunk["type"]
        })
        ids.append(f"chunk_{i}")
        embeddings.append(embedding)
    
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size]
        )
    
    return len(documents)

def retrieve_chunks(query: str, n_results: int = 5) -> list:
    collection = get_collection()
    
    query_embedding = get_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "content": results["documents"][0][i],
            "page": results["metadatas"][0][i]["page"],
            "type": results["metadatas"][0][i]["type"]
        })
    
    return chunks