import re
import json
import fitz 



#This script is used to extract text from a pdf and store it as json file. File is deparated by numbered sections.
# you need to have a file with the name "Job Descriptions.pdf" at the same level of the script
def extract_job_descriptions(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Detecta todos los encabezados tipo 1.xx y sus ubicaciones
    pattern = r"(1\.\d{2})"
    matches = list(re.finditer(pattern, full_text))

    job_descriptions = []
    for i in range(len(matches)):
        start_idx = matches[i].end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        content = full_text[start_idx:end_idx].strip()

        job_entry = {
            "id": matches[i].group(),
            "content": content
        }
        job_descriptions.append(job_entry)

    return job_descriptions


if __name__ == "__main__":
    pdf_path = "Job Descriptions.pdf"
    results = extract_job_descriptions(pdf_path)

    # Guarda el resultado en un archivo JSON
    with open("job_descriptions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Extracción completada. Ver 'job_descriptions.json'.")
