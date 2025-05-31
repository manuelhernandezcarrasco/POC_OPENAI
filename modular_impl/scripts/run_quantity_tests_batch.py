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

def safe_extract_text(path):
    try:
        return extract_text(path)
    except Exception as e:
        print(f"⚠️ Archivo ilegible/corrupto, se enviará placeholder al modelo: {path}\n   Motivo: {e}")
        return "Archivo ilegible o corrupto"

def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def process_cvs_in_batches(adapter, prompt, jd_text, cv_texts, cv_files, output_path, batch_size=10, cv_per_request=2):
    results = []
    total = len(cv_texts)
    num_batches = (total + batch_size - 1) // batch_size
    request_count = 0
    processed_cvs = 0
    for batch_idx, batch_start in enumerate(range(0, total, batch_size)):
        batch_end = min(batch_start + batch_size, total)
        print(f"  ▶ Batch {batch_idx+1}/{num_batches} ({batch_end-batch_start} CVs)")
        batch_cv_texts = cv_texts[batch_start:batch_end]
        batch_cv_files = cv_files[batch_start:batch_end]
        for req_idx, (cv_group, file_group) in enumerate(zip(batched(batch_cv_texts, cv_per_request), batched(batch_cv_files, cv_per_request)), start=1):
            print(f"    - Request {req_idx} (CVs {batch_start + (req_idx-1)*cv_per_request + 1} - {min(batch_start + req_idx*cv_per_request, batch_end)}/{total})")
            try:
                response = adapter.send_request(prompt, jd_text, cv_group)
                content = response["candidates"][0]["content"]["parts"][0]["text"]
                import re
                # Extraer todos los bloques JSON individuales de la respuesta
                json_blocks = re.findall(r'\{[\s\S]*?\}', content)
                if json_blocks:
                    print(f"      🔎 Se encontraron {len(json_blocks)} bloques JSON en la respuesta (esperados: {len(cv_group)})")
                    for block, cv_file in zip(json_blocks, file_group):
                        try:
                            persona = json.loads(block)
                            candidate_name = os.path.splitext(os.path.basename(cv_file))[0]
                            result_obj = {
                                "participant_id": str(uuid.uuid4()),
                                "candidate_name": candidate_name,
                                "score": persona.get("score"),
                                "reasons": persona.get("reasons", [])
                            }
                            results.append(result_obj)
                            processed_cvs += 1
                        except Exception as e2:
                            print(f"      ❌ Error parseando bloque JSON: {e2}")
                            print(block)
                else:
                    print("      ❌ No se encontraron bloques JSON en la respuesta.")
                    print(content)
            except Exception as e:
                print(f"      ❌ Error procesando CVs: {e}")
            request_count += 1
            if request_count % 10 == 0 and (batch_idx < num_batches - 1 or req_idx < (len(batch_cv_texts) + cv_per_request - 1) // cv_per_request):
                print("  ⏳ Esperando 60 segundos por rate limit de Gemini...")
                time.sleep(60)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Resultados guardados en {output_path}")
    print(f"  📊 Total de CVs enviados: {total}, total de resultados guardados: {len(results)}")
    if len(results) != total:
        print(f"  ⚠️ ADVERTENCIA: Se esperaban {total} resultados, pero se guardaron {len(results)}. Puede haber respuestas faltantes o mal formateadas.")

def run_quantity_test_on_case(caso_path, force_all_si=False, cv_per_request=2, target_batch_size=None):
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
        (30, 20, "new-output-set50.json" if target_batch_size == 50 else "output-set50.json")
    ]

    for si_count, no_count, output_file in sets:
        if target_batch_size is not None:
            if (si_count + no_count) != target_batch_size:
                continue
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
        process_cvs_in_batches(adapter, prompt, jd_text, cv_texts, cv_files, output_path, batch_size=10, cv_per_request=cv_per_request)

def run_all():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("rubro", help="Nombre del rubro a procesar")
    parser.add_argument("--caso", help="Nombre del caso específico a procesar (opcional)")
    parser.add_argument("--cv_per_request", type=int, default=2, help="Cantidad de CVs por request (default 2)")
    parser.add_argument("--batch_size", type=int, help="Tamaño específico del batch a procesar (10, 30 o 50)")
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
                run_quantity_test_on_case(caso_path, force_all_si=True, cv_per_request=args.cv_per_request, target_batch_size=args.batch_size)
            else:
                run_quantity_test_on_case(caso_path, cv_per_request=args.cv_per_request, target_batch_size=args.batch_size)

if __name__ == "__main__":
    run_all()

