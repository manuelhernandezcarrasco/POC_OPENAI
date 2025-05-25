import os
import threading
import time
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
classified_cvs_file = "classified_files.json"

lock = threading.Lock()

THREAD_BATCH_SIZE = 10
CV_BATCH_SIZE = 10
DELAY_AFTER_BATCH = 60

job_types = [
    "Ejecutivo de Influencers / Social Media Talent Manager",
    "Ejecutivo de Cuentas Digitales",
    "Diseño Gráfico",
    "Ingeniería Informática / Software",
    "Marketing Digital / Performance",
    "Recursos Humanos",
    "Administración y Finanzas",
    "Atención al Cliente",
    "Producción Audiovisual / Multimedia",
    "Psicología"
]


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


job_list_string = "\n".join(f"- {jt}" for jt in job_types)


def process_batch(cv_filenames):
    print(f"🧵 Thread {threading.current_thread().name} procesando {len(cv_filenames)} CVs...")

    prompt = f"""
    Actúa como un reclutador profesional de recursos humanos.

    Te daré un currículum en forma de imagen. Tu tarea es analizar el contenido del CV y clasificarlo en **uno solo** de los siguientes tipos de puesto:

    {job_list_string}

    Si el currículum no corresponde claramente a ninguna de las categorías anteriores, responde null como valor de `job_type`.

    Devuelve solamente un JSON con esta estructura (sin ningún texto adicional):


    Devuélveme solo un JSON como este (sin texto adicional):

    {{
      "filename": "[cv_filename]"
      "participant_name": "[participant_name]",
      "job_type": "[job_type_elegido]"
    }}

    para esta corrida se clasificaran los siguientes CVs:
    {cv_filenames}
    """

    contents = [prompt]
    valid_filenames = []

    for cv_filename in cv_filenames:
        cv_path = os.path.join(cv_dir, cv_filename)
        ext = os.path.splitext(cv_filename)[1].lower()

        if ext == ".pdf":
            image_bytes = pdf_to_png_bytes(cv_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            image_bytes = image_file_to_bytes(cv_path)
        else:
            print(f"⚠️ Ignorando archivo no compatible: {cv_filename}")
            continue

        valid_filenames.append(cv_filename)

        contents.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        })

    if not valid_filenames:
        print("⚠️ No valid CVs in batch.")
        return
    try:
        response = model.generate_content(
            contents=contents,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "participant_name": {"type": "string"},
                            "job_type": {"type": "string"}
                        },
                        "required": ["filename", "participant_name", "job_type"]
                    }
                }
            }
        )

        print("✅ Respuesta recibida")
        print(response.text)

        with lock:

            if os.path.exists(classified_cvs_file):
                with open(classified_cvs_file, "r") as f:
                    existing_data = json.load(f)
            else:
                existing_data = []

            result = json.loads(response.text)
            existing_data.extend(result)

            with open(classified_cvs_file, "w") as f:
                json.dump(existing_data, f, indent=2)

    except Exception as e:
        print(f"❌ Error procesando {cv_filename}: {e}")


def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

all_files = [f for f in os.listdir(cv_dir) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]

# Outer batch size = number of threads * number of CVs each thread handles
outer_batch_size = THREAD_BATCH_SIZE * CV_BATCH_SIZE

for i, outer_batch in enumerate(batched(all_files, outer_batch_size), start=1):
    print(f"🚀 Lanzando batch {i} con {len(outer_batch)} archivos...")
    threads = []

    # Divide the outer batch into THREAD_BATCH_SIZE sub-batches, each of size CV_BATCH_SIZE
    for j in range(THREAD_BATCH_SIZE):
        start_idx = j * CV_BATCH_SIZE
        end_idx = start_idx + CV_BATCH_SIZE
        sub_batch = outer_batch[start_idx:end_idx]

        if not sub_batch:
            break  # Avoid launching empty threads

        t = threading.Thread(target=process_batch, args=(sub_batch,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(f"✅ Batch {i} completado.")

    if i < (len(all_files) + outer_batch_size - 1) // outer_batch_size:
        print(f"⏳ Esperando {DELAY_AFTER_BATCH} segundos después del batch {i}...")
        time.sleep(DELAY_AFTER_BATCH)

print("🏁 Procesamiento completo.")
