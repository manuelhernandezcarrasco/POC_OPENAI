import os
import fitz
import uuid
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

cv_dir = "cvs"
job_description_file = "job_description.pdf"
model = "claude-3-5-haiku-20241022"

cv_pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.endswith(".pdf")]
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def count_tokens(text):
    return len(text) // 4

def build_prompt(job_description, batch):
    cvs_text = "\n".join([f"{cv['id']} - {cv['text']}" for cv in batch])
    return f"""
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

Currículums:
{cvs_text}
"""

# Load job description and CVs
job_description = extract_text_from_pdf(job_description_file)
cv_list = []
for file in cv_pdf_files:
    cv_text = extract_text_from_pdf(file)
    cv_list.append({
        "id": str(uuid.uuid4()),
        "text": cv_text
    })

batch_size = 50
results = ""

for i in range(0, len(cv_list), batch_size):
    batch = cv_list[i:i + batch_size]
    prompt = build_prompt(job_description, batch)

    print(f"\n▶️ Procesando batch {i // batch_size + 1} con {len(batch)} CVs...")

    cv_token_counts = [count_tokens(cv["text"]) for cv in batch]
    average_tokens = sum(cv_token_counts) / len(cv_token_counts) if cv_token_counts else 0

    print("📄 Tokens per CV:", cv_token_counts)
    print(f"📊 Average tokens per CV: {average_tokens:.2f}")

    user_message = {"role": "user", "content": prompt}
    total_input_tokens = count_tokens(prompt)

    print(f"🔢 Tokens in input prompt: {total_input_tokens}")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.2,
        messages=[user_message]
    )
    output = response.content[0].text
    print(output)
    results += output + "\n"

with open("output-claude.json", "w") as f:
    f.write(results)
