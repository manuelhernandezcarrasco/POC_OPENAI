import sys
import os
import json
import time
import uuid
import unicodedata
from dotenv import load_dotenv
from modular_impl.adapters.gemini_adapter import GeminiFlashAdapter
from modular_impl.scripts.file_utils import extract_text

load_dotenv()

def normalize(s):
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()

def load_cv_texts(cv_paths):
    return [extract_text(path) for path in cv_paths]

def prepare_cv_batch(si_dir, no_dir, si_count, no_count):
    si_files = sorted([
        os.path.join(si_dir, f) for f in os.listdir(si_dir)
        if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx"))
    ])[:si_count]

    no_files = sorted([
        os.path.join(no_dir, f) for f in os.listdir(no_dir)
        if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx"))
    ])[:no_count]

    return load_cv_texts(si_files + no_files)

def process_cvs_in_batches(adapter, prompt, jd_text, cv_texts, output_path, batch_size=10):
    results = []
    total = len(cv_texts)
    num_batches = (total + batch_size - 1) // batch_size
    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        print(f"  ▶ Batch {batch_idx+1}/{num_batches} ({end-start} CVs)")
        for i, cv_text in enumerate(cv_texts[start:end], start=1):
            print(f"    - Iteración {start + i}/{total}")
            try:
                response = adapter.send_request(prompt, jd_text, [cv_text])
                content = response["candidates"][0]["content"]["parts"][0]["text"]
                persona = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
                if isinstance(persona, list):
                    for p in persona:
                        result_obj = {
                            "participant_id": str(uuid.uuid4()),
                            "score": p["score"],
                            "reasons": p["reasons"]
                        }
                        results.append(result_obj)
                else:
                    result_obj = {
                        "participant_id": str(uuid.uuid4()),
                        "score": persona["score"],
                        "reasons": persona["reasons"]
                    }
                    results.append(result_obj)
            except Exception as e:
                print(f"      ❌ Error procesando CV: {e}")
        if batch_idx < num_batches - 1:
            print("  ⏳ Esperando 60 segundos por rate limit de Gemini...")
            time.sleep(60)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Resultados guardados en {output_path}\n")

def run_quantity_test_on_case(caso_path):
    prompt_path = os.path.join(caso_path, "prompt.txt")
    jd_path = os.path.join(caso_path, "job_description.pdf")
    si_dir = os.path.join(caso_path, "cvs", "si")
    no_dir = os.path.join(caso_path, "cvs", "no")

    if not os.path.exists(prompt_path) or not os.path.exists(jd_path):
        print(f"❌ Faltan archivos requeridos en {caso_path}")
        return

    prompt = open(prompt_path, encoding="utf-8").read().strip()
    jd_text = extract_text(jd_path)

    adapter = GeminiFlashAdapter()

    sets = [
        (5, 5, "output-set10.json"),
        (20, 10, "output-set30.json"),
        (30, 20, "output-set50.json")
    ]

    for si_count, no_count, output_file in sets:
        print(f"\n🔹 Analizando set: {output_file} ({si_count} si, {no_count} no)")
        si_files = sorted([
            os.path.join(si_dir, f) for f in os.listdir(si_dir)
            if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx"))
        ])[:si_count]
        no_files = sorted([
            os.path.join(no_dir, f) for f in os.listdir(no_dir)
            if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx"))
        ])[:no_count]
        cv_files = si_files + no_files
        cv_texts = [extract_text(path) for path in cv_files]
        output_path = os.path.join(caso_path, output_file)
        process_cvs_in_batches(adapter, prompt, jd_text, cv_texts, output_path, batch_size=10)

def run_all():
    if len(sys.argv) < 2:
        print("Uso: python3 run_quantity_tests.py <rubro>")
        sys.exit(1)

    target_rubro = normalize(sys.argv[1])
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sets_de_pruebas", "pruebas de cantidad"))

    if not os.path.isdir(base_path):
        print(f"❌ Carpeta base no encontrada: {base_path}")
        sys.exit(1)

    rubros = {normalize(d): d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))}
    if target_rubro not in rubros:
        print(f"❌ Rubro '{target_rubro}' no encontrado. Rubros disponibles: {list(rubros.keys())}")
        sys.exit(1)

    rubro_path = os.path.join(base_path, rubros[target_rubro])
    for caso in sorted(os.listdir(rubro_path)):
        caso_path = os.path.join(rubro_path, caso)
        if os.path.isdir(caso_path):
            print(f"🏁 Procesando caso: {caso}")
            run_quantity_test_on_case(caso_path)

if __name__ == "__main__":
    run_all()
