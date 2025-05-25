import sys
import os
import unicodedata
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
import time
import uuid
from dotenv import load_dotenv
from modular_impl.adapters.gemini_adapter import GeminiFlashAdapter
from modular_impl.scripts.file_utils import extract_text

load_dotenv()

def normalize(s):
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()

def run_batch_on_set(set_path: str, prompt_path: str, model="gemini", iterations=10):
    adapter = GeminiFlashAdapter()
    prompt = open(prompt_path, "r", encoding="utf-8").read().strip()
    jd_path = os.path.join(set_path, "job_description.pdf")
    cvs_dir = os.path.join(set_path, "cvs")

    if not os.path.exists(jd_path) or not os.path.isdir(cvs_dir):
        print(f"❌ Datos incompletos en {set_path}")
        return

    jd_text = extract_text(jd_path)
    cv_files = [os.path.join(cvs_dir, f) for f in os.listdir(cvs_dir)
                if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))]
    cv_files.sort()

    if len(cv_files) == 0:
        print(f"⚠️  No hay CVs en {cvs_dir}")
        return

    cvs_texts = [extract_text(p) for p in cv_files]

    output_path = os.path.join(set_path, f"output-{os.path.basename(set_path)}.json")
    results = []

    for iteration in range(iterations):
        print(f"🔁 Iteración {iteration+1}/{iterations} en {set_path}")
        response = adapter.send_request(prompt, jd_text, cvs_texts)

        try:
            candidate = response["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json_str = candidate.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(parsed_json_str)

            for persona in parsed if isinstance(parsed, list) else [parsed]:
                result_obj = {
                    "participant_id": str(uuid.uuid4()),
                    "reasons": persona["reasons"],
                    "score": persona["score"]
                }
                results.append(result_obj)

                print(f"👤 {result_obj['participant_id']}")
                print(f"   ✔ Score: {result_obj['score']}")
                for reason in result_obj["reasons"]:
                    print(f"   - {reason}")

        except Exception as e:
            print("❌ Error al parsear respuesta")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("Detalles:", e)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Resultados guardados en {output_path}\n")

    if model.lower().startswith("gemini"):
        print("⏳ Esperando 60 segundos por política de rate limit Gemini...")
        time.sleep(60)

def run_all():
    # Calcular la ruta base correctamente desde la ubicación del script
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sets_de_pruebas", "pruebas_de_calidad"))
    print(f"[DEBUG] Buscando carpeta base: {base}")
    if not os.path.isdir(base):
        print(f"❌ La carpeta base no existe: {base}")
        sys.exit(1)
    if len(sys.argv) < 2:
        print("Uso: python3 main_script_parameter.py <rubro>")
        print("Ejemplo: python3 main_script_parameter.py rrhh")
        sys.exit(1)
    target_rubro = sys.argv[1]
    rubros = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    rubros_norm = {normalize(d): d for d in rubros}
    target_norm = normalize(target_rubro)
    if target_norm not in rubros_norm:
        print(f"❌ El rubro '{target_rubro}' no existe en {base}")
        print("Rubros disponibles:")
        for r in rubros:
            print("-", r)
        sys.exit(1)
    rubro_path = os.path.join(base, rubros_norm[target_norm])
    for caso in os.listdir(rubro_path):
        caso_path = os.path.join(rubro_path, caso)
        if not os.path.isdir(caso_path):
            continue
        prompt_path = os.path.join(caso_path, "prompt.txt")
        if not os.path.exists(prompt_path):
            print(f"❌ Falta prompt en {caso_path}")
            continue
        for set_x in ["set1", "set2", "set3"]:
            set_path = os.path.join(caso_path, set_x)
            if os.path.isdir(set_path):
                run_batch_on_set(set_path, prompt_path)

if __name__ == "__main__":
    run_all()
