import pymupdf as fitz
import pdfplumber
import base64
import os
from PIL import Image
import io
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def encode_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def interpret_page_with_gemini(image: Image.Image, page_num: int, max_retries: int = 3) -> str:
    b64 = encode_image_to_base64(image)
    
    for attempt in range(max_retries):
        time.sleep(3)
        try:
            response = client.models.generate_content(
                # model="gemini-3.6-flash",
                model="gemini-3.5-flash-lite",
                contents=[
                    types.Part.from_bytes(
                        data=base64.b64decode(b64),
                        mime_type="image/png"
                    ),
                    """Kamu adalah analis dokumen keuangan. 
Analisis halaman dokumen ini secara menyeluruh.
Fokus pada:
1. Tabel - ekstrak semua data angka dengan label yang tepat
2. Grafik/Chart donut/pie - perhatikan LEGENDA warna dengan sangat teliti. 
   Cocokkan setiap warna di legenda dengan bagian chart yang sesuai.
   Sebutkan nilai persentase sesuai urutan legenda yang tertera.
3. Infografis/Flowchart - ikuti arah panah dengan teliti dari kiri ke kanan 
   dan atas ke bawah. Jelaskan setiap tahap secara berurutan sesuai arah panah.
4. Teks penting lainnya

Jawab dalam Bahasa Indonesia secara detail dan akurat."""
                ]
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"Retry {attempt + 1}/{max_retries} hal {page_num}, tunggu {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e

def extract_tables_from_page(pdf_path: str, page_num: int) -> list:
    tables_text = []
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        tables = page.extract_tables()
        for table in tables:
            if not table:
                continue
            rows = []
            for row in table:
                cleaned = [cell if cell else "" for cell in row]
                rows.append(" | ".join(cleaned))
            tables_text.append("\n".join(rows))
    return tables_text

def parse_pdf(pdf_path: str) -> list:
    chunks = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_label = page_num + 1

        # 1. Ekstrak teks
        text = page.get_text().strip()
        if text:
            chunks.append({
                "content": text,
                "page": page_label,
                "type": "text"
            })

        # 2. Ekstrak tabel
        tables = extract_tables_from_page(pdf_path, page_num)
        for table in tables:
            if table.strip():
                chunks.append({
                    "content": f"[TABEL - Halaman {page_label}]\n{table}",
                    "page": page_label,
                    "type": "table"
                })

        # 3. Render halaman sebagai gambar dan kirim ke Gemini Vision
        print(f"Menginterpretasi visual halaman {page_label}...")
        try:
            mat = fitz.Matrix(2, 2)  # scale 2x untuk kualitas lebih baik
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            description = interpret_page_with_gemini(image, page_label)
            chunks.append({
                "content": f"[VISUAL - Halaman {page_label}]\n{description}",
                "page": page_label,
                "type": "image"
            })
        except Exception as e:
            print(f"Gagal interpretasi visual hal {page_label}: {e}")

    doc.close()
    return chunks