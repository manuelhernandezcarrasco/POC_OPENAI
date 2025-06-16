import os
import fitz
import uuid
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
cv_dir = "cvs"
model = "o4-mini"
job_description_file = "job_description.pdf"

cv_pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.endswith(".pdf")]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def count_tokens(text):
    # encoding = tiktoken.encoding_for_model(model)
    # return len(encoding.encode(text))
    return len(text) // 4


job_description = extract_text_from_pdf(job_description_file)
cvs = [extract_text_from_pdf(file) for file in cv_pdf_files]
cv_list = []
for file in cv_pdf_files:
    cv_text = extract_text_from_pdf(file)
    cv_list.append({
        "id": str(uuid.uuid4()),
        "text": cv_text
    })

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

# Separate queries in batches
batch_size = 50

results = ""

for i in range(0, len(cv_list), batch_size):
    batch = cv_list[i:i + batch_size]
    prompt = build_prompt(job_description, batch)

    print(f"▶️ Procesando batch {i // batch_size + 1} con {len(batch)} CVs...")

    # Count tokens for each CV
    cv_token_counts = [count_tokens(cv) for cv in cvs]

    # Calculate average
    average_tokens = sum(cv_token_counts) / len(cv_token_counts) if cv_token_counts else 0

    print("📄 Tokens per CV:", cv_token_counts)
    print(f"📊 Average tokens per CV: {average_tokens:.2f}")

    # Count tokens for the entire prompt
    user_message = {"role": "user", "content": prompt}
    total_input_tokens = count_tokens(prompt)

    print(f"🔢 Tokens in input prompt: {total_input_tokens}")

    response = client.chat.completions.create(
        model=model,
        messages=[user_message],
    )

    results += response.choices[0].message.content
    print(response.choices[0].message.content)
    print(f"📊 Token usage: {response.usage}")

with open("output-openai.json", "w") as f:
    f.write(results)
