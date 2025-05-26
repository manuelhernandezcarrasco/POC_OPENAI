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

def safe_extract_text(path):
    try:
        return extract_text(path)
    except Exception as e:
        print(f"⚠️ Archivo ilegible/corrupto, se enviará placeholder al modelo: {path}\n   Motivo: {e}")
        return "Archivo ilegible o corrupto"

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

def process_cvs_one_by_one(adapter, prompt, jd_text, cv_texts, output_path, batch_size=10):
    results = []
    total = len(cv_texts)
    for idx, cv_text in enumerate(cv_texts, start=1):
        print(f"    - Iteración {idx}/{total}")
        try:
            response = adapter.send_request(prompt, jd_text, [cv_text])
            if not response or "candidates" not in response:
                print(f"      ❌ Respuesta inesperada de Gemini (sin 'candidates'):")
                print(json.dumps(response, indent=2, ensure_ascii=False))
                if response and "error" in response:
                    print(f"      ❌ Error de Gemini API: {response['error']}")
                continue
            content = response["candidates"][0]["content"]["parts"][0]["text"]
            # Limpieza y parseo robusto del JSON
            import re
            json_blocks = re.findall(r"```json\\s*(\{[\s\S]*?\})\\s*```", content)
            if json_blocks:
                for block in json_blocks:
                    persona = json.loads(block)
                    result_obj = {
                        "participant_id": str(uuid.uuid4()),
                        "score": persona.get("score"),
                        "reasons": persona.get("reasons", [])
                    }
                    results.append(result_obj)
            else:
                try:
                    parsed_json_str = content.strip().removeprefix("```json").removesuffix("```").strip()
                    persona = json.loads(parsed_json_str)
                    if isinstance(persona, list):
                        for p in persona:
                            result_obj = {
                                "participant_id": str(uuid.uuid4()),
                                "score": p.get("score"),
                                "reasons": p.get("reasons", [])
                            }
                            results.append(result_obj)
                    else:
                        result_obj = {
                            "participant_id": str(uuid.uuid4()),
                            "score": persona.get("score"),
                            "reasons": persona.get("reasons", [])
                        }
                        results.append(result_obj)
                except Exception as e2:
                    print(f"      ❌ Error parseando respuesta: {e2}")
                    print(content)
        except Exception as e:
            print(f"      ❌ Error procesando CV: {e}")
        # Guardar resultados cada batch_size CVs o al final
        if idx % batch_size == 0 or idx == total:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  💾 Resultados guardados en {output_path} ({idx}/{total})")
        # Esperar 60 segundos cada batch_size CVs, excepto al final
        if idx % batch_size == 0 and idx != total:
            print("  ⏳ Esperando 60 segundos por rate limit de Gemini...")
            time.sleep(60)

def run_quantity_test_on_case(caso_path, force_all_si=False):
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
        ])
        if force_all_si:
            cv_files = si_files[:si_count+no_count]
        else:
            si_files = si_files[:si_count]
            no_files = sorted([
                os.path.join(no_dir, f) for f in os.listdir(no_dir)
                if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx"))
            ])[:no_count]
            cv_files = si_files + no_files
        cv_texts = [safe_extract_text(path) for path in cv_files]
        output_path = os.path.join(caso_path, output_file)
        process_cvs_one_by_one(adapter, prompt, jd_text, cv_texts, output_path, batch_size=10)

def run_all():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("rubro", help="Nombre del rubro a procesar")
    parser.add_argument("--caso", help="Nombre del caso específico a procesar (opcional)")
    args = parser.parse_args()

    target_rubro = normalize(args.rubro)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sets_de_pruebas", "pruebas de cantidad"))

    if not os.path.isdir(base_path):
        print(f"❌ Carpeta base no encontrada: {base_path}")
        sys.exit(1)

    rubros = {normalize(d): d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))}
    if target_rubro not in rubros:
        print(f"❌ Rubro '{target_rubro}' no encontrado. Rubros disponibles: {list(rubros.keys())}")
        sys.exit(1)

    rubro_path = os.path.join(base_path, rubros[target_rubro])
    casos = []
    if args.caso:
        caso_dir = os.path.join(rubro_path, args.caso)
        if not os.path.isdir(caso_dir):
            print(f"❌ Caso '{args.caso}' no encontrado en rubro '{target_rubro}'")
            sys.exit(1)
        casos = [args.caso]
    else:
        casos = sorted(os.listdir(rubro_path))

    for caso in casos:
        caso_path = os.path.join(rubro_path, caso)
        if os.path.isdir(caso_path):
            print(f"🏁 Procesando caso: {caso}")
            if caso.strip().lower() in ["caso3", "caso4", "caso6"]:
                run_quantity_test_on_case(caso_path, force_all_si=True)
            else:
                run_quantity_test_on_case(caso_path)

if __name__ == "__main__":
    run_all()
