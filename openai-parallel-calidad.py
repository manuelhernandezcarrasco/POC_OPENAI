import os
import threading
import uuid
import fitz
import PIL.Image
from dotenv import load_dotenv
import base64
import json
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

load_dotenv()

model = "gpt-4.1-mini"
casos = ["admin_finanzas", "diseño_grafico", "ejecutivo_cuentas_digitales", "ejecutivo_influencers","ingenieria_informatica", "rrhh", "tecnico_mantenimiento"]
cantidad_casos = 5
cantidad_sets = 3



client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


def load_prompt_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: El archivo de prompt '{file_path}' no fue encontrado.")
        exit()
    except Exception as e:
        print(f"Error al leer el archivo de prompt '{file_path}': {e}")
        exit()


def process_cv(cv_filename, cv_dir, job_description_file, prompt_file_path, output_json_file):

    job_description = extract_text_from_pdf(job_description_file)

    prompt_template = load_prompt_from_file(prompt_file_path)
    prompt_base = prompt_template.replace("{job_description}", job_description)

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
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8")
                    }
                }
            ]
        }],
            temperature=0.2
        )

        print("✅ Respuesta recibida")
        response_text = response.choices[0].message.content

        with lock:
            print(f"✅ Procesado: {cv_filename}")

            existing_data = []
            if os.path.exists(output_json_file):
                with open(output_json_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        pass

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()

            result = json.loads(response_text)
            existing_data.append(result)

            with open(output_json_file, "w") as f:
                json.dump(existing_data, f, indent=2)

    except Exception as e:
        print(f"❌ Error procesando {cv_filename}: {e}")


with ThreadPoolExecutor() as executor:
    for caso in casos:
        for i in range(cantidad_casos):
            prueba = "sets_de_pruebas/pruebas_de_calidad/" + caso + "/caso" + str(i + 1) + "/"
            prompt_file_path = prueba + "prompt.txt"
            for j in range(cantidad_sets):
                set = "set" + str(j + 1) + "/"
                cv_dir = prueba + set + "cvs"
                job_description_file = prueba + set + "job_description.pdf"
                output_json_file = prueba + set + "output-set" + str(j + 1) + ".json"
                file = next((f for f in os.listdir(cv_dir) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))),None)
                for _ in range(BATCH_SIZE):
                    executor.submit(process_cv, file, cv_dir, job_description_file, prompt_file_path, output_json_file)