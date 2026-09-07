from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(parsed_chunks: list) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    final_chunks = []
    
    for chunk in parsed_chunks:
        # Tabel dan gambar tidak dipotong — langsung masuk as-is
        if chunk["type"] in ["table", "image"]:
            final_chunks.append(chunk)
            continue
        
        # Teks panjang dipotong dengan overlap
        if len(chunk["content"]) > 1000:
            splits = text_splitter.split_text(chunk["content"])
            for split in splits:
                final_chunks.append({
                    "content": split,
                    "page": chunk["page"],
                    "type": chunk["type"]
                })
        else:
            final_chunks.append(chunk)
    
    return final_chunks