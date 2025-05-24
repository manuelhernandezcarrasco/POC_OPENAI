import os
import threading
import time
import uuid
import fitz
import PIL.Image
from dotenv import load_dotenv
import google.generativeai as genai
import base64
import json
from io import BytesIO
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from docx import Document

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

cv_dir = "cvs"
job_description_file = "job_description.pdf"
output_json_file = "output-gemini-images.json"
token_usage_file = "token-usage.json"

lock = threading.Lock()

BATCH_SIZE = 10
DELAY_AFTER_BATCH = 60


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)


def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def pdf_to_png_bytes(pdf_path, page_number=0):
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=150)
        image = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def image_file_to_bytes(image_path):
    with PIL.Image.open(image_path) as img:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()


def count_tokens(text):
    return len(text) // 4


def process_cv(cv_path, prompt_base, base_tokens):
    ext = os.path.splitext(cv_path)[1].lower()

    # Extract text based on file type
    if ext == ".pdf":
        text = extract_text_from_pdf(cv_path)
        # Convert to PNG bytes for visualization
        image_bytes = pdf_to_png_bytes(cv_path)
    elif ext == ".docx":
        text = extract_text_from_docx(cv_path)
        # For DOCX, we'll create a simple text-based visualization
        img = PIL.Image.new('RGB', (800, 600), color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
    elif ext in [".png", ".jpg", ".jpeg"]:
        image_bytes = image_file_to_bytes(cv_path)
        text = ""  # You might want to add OCR here
    else:
        print(f"⚠️ Ignorando archivo no compatible: {cv_path}")
        return None

    participant_id = str(uuid.uuid4())
    prompt = prompt_base.replace("[participant_id]", participant_id)

    # Add the extracted text to the prompt
    prompt += f"\n\nCV Text:\n{text}"

    try:
        response = model.generate_content(
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(image_bytes).decode("utf-8")
                    }
                }
            ],
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "participant_id": {"type": "string"},
                            "candidate_name": {"type": "string"},
                            "score": {"type": "integer"},
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["participant_id", "candidate_name", "score", "reasons"]
                    }
                }
            }
        )
        print("✅ Respuesta recibida")
        print(response.text)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"❌ Error procesando {cv_path}: {e}")
        return None


@app.route('/analyze', methods=['POST'])
def analyze():
    # Guardar archivos subidos temporalmente
    job_desc_file = request.files.get('job_description')
    cvs_files = request.files.getlist('cvs[]')
    if not job_desc_file or not cvs_files:
        return jsonify({'error': 'Missing job_description or cvs[] files'}), 400

    os.makedirs('tmp', exist_ok=True)
    
    # Save all files first before processing
    job_desc_path = os.path.join('tmp', job_desc_file.filename)
    job_desc_file.save(job_desc_path)
    job_description = extract_text_from_pdf(job_desc_path)

    # Save all CV files first
    cv_paths = []
    for cv_file in cvs_files:
        cv_path = os.path.join('tmp', cv_file.filename)
        cv_file.save(cv_path)
        cv_paths.append(cv_path)

    prompt_base = f"""
Actúa como un experto en recursos humanos especializado en evaluación de candidatos según su currículum.

A continuación se presentarán varios currículums, cada uno en el siguiente formato:

[participant_id] - [Texto del currículum]

Tu tarea es evaluar cada uno de ellos según su adecuación a la descripción del puesto, considerando los siguientes criterios:

- Nivel de seniority requerido
- Experiencia en la industria relevante
- Manejo básico de inglés

La idea es que armes un analisis contextual y semantico de cada cv, luego creando un perfil a cada candidato para poder contrastar esos perfiles
con la descripción del puesto, asi teniendo base para poder poner una evaluación a cada candidato.

Por cada currículum, devuelve una evaluación en formato JSON con esta estructura:

{{
  "participant_id": "...",
  "score": [puntaje de 0 a 100],
  "reasons": [
    "razón 1",
    "razón 2",
    ...
  ]
}}

Importante: devuelve un objeto JSON por cada currículum, sin texto adicional.

Descripción del puesto:
{job_description}
"""
    base_tokens = count_tokens(prompt_base)
    results = []
    total_cvs = len(cv_paths)
    
    def generate():
        try:
            for i, cv_path in enumerate(cv_paths, 1):
                # Send progress update
                progress = (i / total_cvs) * 100
                yield f"data: {json.dumps({'progress': progress, 'current': i, 'total': total_cvs})}\n\n"
                
                result = process_cv(cv_path, prompt_base, base_tokens)
                if result:
                    results.extend(result)
                
            # Send final results
            yield f"data: {json.dumps({'progress': 100, 'results': results})}\n\n"
        finally:
            # Cleanup all files
            for cv_path in cv_paths:
                try:
                    os.remove(cv_path)
                except:
                    pass
            try:
                os.remove(job_desc_path)
            except:
                pass

    return Response(generate(), mimetype='text/event-stream')


def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


if __name__ == '__main__':
    app.run(debug=True)