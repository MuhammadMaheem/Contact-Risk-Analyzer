FROM python:3.11-slim

# tesseract-ocr + poppler-utils are required for the OCR fallback path
# (pytesseract + pdf2image) — the most commonly forgotten step when
# containerizing this kind of pipeline.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# CPU-only torch wheel first — avoids pulling multi-GB CUDA packages that
# sentence-transformers would otherwise resolve to by default.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads storage/chroma storage/generated_reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
