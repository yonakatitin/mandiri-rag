import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "mandiri_rag"

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model_name="models/text-embedding-004"
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    return collection

def store_chunks(chunks: list):
    collection = get_collection()
    
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk["content"])
        metadatas.append({
            "page": chunk["page"],
            "type": chunk["type"]
        })
        ids.append(f"chunk_{i}")
    
    # Simpan ke ChromaDB dalam batch
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
    
    return len(documents)

def retrieve_chunks(query: str, n_results: int = 5) -> list:
    collection = get_collection()
    
    results = collection.query(
        query_texts=[query],
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