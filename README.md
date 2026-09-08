# Multimodal RAG - Bank Mandiri 2025 Annual Report

An automated question-answering system based on PDF documents using Multimodal Retrieval Augmented Generation (RAG). This system can process text, tables, charts, and infographics from Bank Mandiri's 2025 financial report.

## System Architecture

```
PDF Input
    ↓
[Parser] → Extract Text + Tables + Render Pages to Gemini Vision
    ↓
[Chunker] → Split text with overlap, keep tables & images intact
    ↓
[Vector Store] → Embedding + store to ChromaDB
    ↓
[Query] → Retrieve chunks → Generate answer with Gemini
    ↓
JSON Response + Page Source Metadata
```

## Tech Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Orchestration | LangChain |
| Vector Database | ChromaDB |
| LLM & Vision | Gemini 3.5 Flash Lite |
| Embedding | Gemini Embedding 001 |
| PDF Parser | PyMuPDF + pdfplumber |

## Installation

**1. Clone repository**
```bash
git clone https://github.com/yonakatitin/mandiri-rag.git
cd mandiri-rag
```

**2. Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Setup API Key**

Create a `.env` file in the root project:
```
GOOGLE_API_KEY=your_google_api_key_here
```

Get your API key at [Google AI Studio](https://aistudio.google.com)

**5. Run the server**
```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`

## API Endpoints

### 1. POST /ingest
Upload and process a PDF file into the vector database.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Laporan_Keuangan_Bank_Mandiri_2025.pdf"
```

**Response:**
```json
{
  "status": "success",
  "filename": "Laporan_Keuangan_Bank_Mandiri_2025.pdf",
  "total_parsed_chunks": 23,
  "total_stored_chunks": 53
}
```

### 2. POST /query
Ask a question based on the ingested document.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the roles of the Customer Protection Unit?",
    "n_results": 5
  }'
```

**Response:**
```json
{
  "question": "What are the roles of the Customer Protection Unit?",
  "answer": "...",
  "sources": [
    {"page": 7, "type": "text"},
    {"page": 8, "type": "image"}
  ]
}
```

## Example Questions

1. What are the roles of the Customer Protection Unit according to POJK No. 22 of 2023?
2. Is debt collection allowed at 21.00?
3. What is the nominal and percentage growth of loans in the mining and construction sectors?
4. What is the composition of third-party funds (DPK) in 2024 and 2025?
5. How does Bank Mandiri handle customer complaints?
6. What complaint channels does Bank Mandiri provide?

## Project Structure

```
mandiri-rag/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI entry point
│   ├── ingestion.py     # PDF upload & processing endpoint
│   ├── query.py         # Question answering endpoint
│   ├── parser.py        # PDF parsing (text, tables, vision)
│   ├── chunker.py       # Text chunking
│   └── vectorstore.py   # Embedding & ChromaDB
├── data/                # PDF input folder
├── chroma_db/           # Vector database (auto-generated)
├── .env                 # API keys (not committed)
└── requirements.txt     # Python dependencies
```

## Multimodal Capabilities

This system goes beyond plain text extraction:
- **Tables** — Extracts numerical data with row/column structure preserved
- **Charts/Graphs** — Interprets donut/pie charts with accurate values and labels
- **Infographics** — Understands flowcharts and step-by-step diagrams