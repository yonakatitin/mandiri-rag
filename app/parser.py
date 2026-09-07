import fitz  # PyMuPDF
import pdfplumber
import base64
import os
from PIL import Image
import io
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def encode_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def interpret_image_with_gemini(image: Image.Image, page_num: int) -> str:
    b64 = encode_image_to_base64(image)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(
                data=base64.b64decode(b64),
                mime_type="image/png"
            ),
            "Kamu adalah analis dokumen keuangan. Deskripsikan secara detail semua informasi yang ada pada gambar/grafik/infografis ini. Jika ada angka, persentase, atau data, sebutkan semuanya secara eksplisit. Jawab dalam Bahasa Indonesia."
        ]
    )
    return response.text

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

        # 3. Ekstrak gambar
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))

            # Skip gambar terlalu kecil (icon, dekorasi)
            if image.width < 100 or image.height < 100:
                continue

            try:
                description = interpret_image_with_gemini(image, page_label)
                chunks.append({
                    "content": f"[GAMBAR/GRAFIK - Halaman {page_label}]\n{description}",
                    "page": page_label,
                    "type": "image"
                })
            except Exception as e:
                print(f"Gagal interpretasi gambar hal {page_label}: {e}")

    doc.close()
    return chunks