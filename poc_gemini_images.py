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

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

cv_dir = "cvs"
job_description_file = "job_description.pdf"
output_json_file = "output-gemini-images.json"
token_usage_file = "token-usage.json"

lock = threading.Lock()

BATCH_SIZE = 10
DELAY_AFTER_BATCH = 60


# Leer archivos PDF
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


job_description = extract_text_from_pdf(job_description_file)

prompt_base = f"""
Actúa como un experto en recursos humanos especializado en evaluación de candidatos según su currículum.

A continuación se presentarán varios currículums, cada uno en el siguiente formato:

[participant_id] - [Texto del currículum]

Tu tarea es evaluar cada uno de ellos según su adecuación a la descripción del puesto, considerando los siguientes criterios:

- Nivel de seniority requerido
- Experiencia en la industria relevante
- Manejo básico de inglés

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


def process_cv(cv_filename):
    cv_path = os.path.join(cv_dir, cv_filename)
    ext = os.path.splitext(cv_filename)[1].lower()

    # Convert to PNG bytes
    if ext == ".pdf":
        image_bytes = pdf_to_png_bytes(cv_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        image_bytes = image_file_to_bytes(cv_path)
    else:
        print(f"⚠️ Ignorando archivo no compatible: {cv_filename}")
        return

    participant_id = str(uuid.uuid4())

    prompt = prompt_base.replace("[participant_id]", participant_id)

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
                            "score": {"type": "integer"},
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["participant_id", "score", "reasons"]
                    }
                }
            }
        )

        print("✅ Respuesta recibida")
        print(response.text)

        # Mostrar tokens usados
        if hasattr(response, 'usage_metadata'):
            print("🧠 Tokens usados:")
            print("Prompt: ", response.usage_metadata.prompt_token_count)
            print("Prompt (Local): ", base_tokens)
            print("Prompt (Imagen): ", response.usage_metadata.prompt_token_count - base_tokens)
            print("Respuesta: ", response.usage_metadata.candidates_token_count)
            print("Total: ", response.usage_metadata.total_token_count)
        else:
            print("⚠️ No se pudo obtener metadata de uso de tokens.")

        with lock:
            print(f"✅ Procesado: {cv_filename}")

            existing_data = []
            if os.path.exists(output_json_file):
                with open(output_json_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        pass

            result = json.loads(response.text)
            existing_data.extend(result)

            with open(output_json_file, "w") as f:
                json.dump(existing_data, f, indent=2)

            # Guardar tokens
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "participant_id": participant_id,
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "prompt_tokens_local": base_tokens,
                    "prompt_tokens_image": response.usage_metadata.prompt_token_count - base_tokens,
                    "response_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }

                if os.path.exists(token_usage_file):
                    with open(token_usage_file, "r") as f:
                        try:
                            tokens_data = json.load(f)
                        except json.JSONDecodeError:
                            tokens_data = []
                else:
                    tokens_data = []

                tokens_data.append(usage)

                with open(token_usage_file, "w") as f:
                    json.dump(tokens_data, f, indent=2)

    except Exception as e:
        print(f"❌ Error procesando {cv_filename}: {e}")


def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


all_files = [f for f in os.listdir(cv_dir) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]

for i, batch in enumerate(batched(all_files, BATCH_SIZE), start=1):
    print(f"🚀 Lanzando batch {i} con {len(batch)} archivos...")
    threads = []

    for file in batch:
        t = threading.Thread(target=process_cv, args=(file,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if i < (len(all_files) + BATCH_SIZE - 1) // BATCH_SIZE:
        print(f"⏳ Esperando {DELAY_AFTER_BATCH} segundos después del batch {i}...")
        time.sleep(DELAY_AFTER_BATCH)

print("🏁 Procesamiento completo.")
