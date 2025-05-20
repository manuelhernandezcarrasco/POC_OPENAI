import os
import fitz
import PIL.Image
from dotenv import load_dotenv
import google.generativeai as genai
import base64
from io import BytesIO

# Cargar variables de entorno
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

# Configuraciones
cv_dir = "cvs"
job_description_file = "job_description.pdf"


# Leer archivos PDF
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


# Extraer descripción del puesto
job_description = extract_text_from_pdf(job_description_file)

# Convertir primer CV a imagen PNG
# cv_files = sorted(os.listdir(cv_dir))
# first_cv_pdf_path = os.path.join(cv_dir, cv_files[0])

# print("📄 Primer CV:", first_cv_pdf_path)

def pdf_page_to_png_bytes(pdf_path, page_number=0):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    pix = page.get_pixmap(dpi=150)
    image = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

image_bytes = pdf_page_to_png_bytes("cvs/curriculum cariola lucas.pdf")

def count_tokens(text):
    return len(text) // 4


prompt = f"""
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

local_prompt_tokens = count_tokens(prompt)

response = model.generate_content(
    contents = [
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
    print("Prompt (Local): ", local_prompt_tokens)
    print("Prompt (Imagen): ", response.usage_metadata.prompt_token_count - local_prompt_tokens)
    print("Respuesta: ", response.usage_metadata.candidates_token_count)
    print("Total: ", response.usage_metadata.total_token_count)
else:
    print("⚠️ No se pudo obtener metadata de uso de tokens.")

# Guardar resultados
with open("output-gemini-images.json", "w") as f:
    f.write(response.text)
