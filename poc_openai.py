import os
import fitz
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
cv_dir = "cvs"
model = "gpt-4o"
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
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


job_description = extract_text_from_pdf(job_description_file)
cvs = [extract_text_from_pdf(file) for file in cv_pdf_files]
cv_list = "\n".join([f"CV {i + 1}: {cv}" for i, cv in enumerate(cvs)])

prompt = f"""
You are a professional Human Resources expert responsible for evaluating job applicants.

Given the following job description:

---
{job_description}
---

And the following list of candidate CVs:

---
{cv_list}
---

Your task is to:
1. **Identify which candidates do not meet the minimum requirements** for the job. List them and explain why.
2. **List the candidates who are the most suitable** for the position. Rank them from most to least suitable and justify each ranking based on experience, skills, and relevance to the job posting.

Return your answer in a structured, clear format.
"""

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
    temperature=0.2
)

print(response.choices[0].message.content)
print(f"📊 Token usage: {response.usage}")
