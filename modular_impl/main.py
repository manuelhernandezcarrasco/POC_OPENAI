import json
import os
import time
import uuid
from dotenv import load_dotenv
from file_utils import extract_text
from adapters.gemini_adapter import GeminiFlashAdapter

ADAPTERS = {
    "gemini": GeminiFlashAdapter,
}

def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_set(set_name: str) -> tuple[str, str, list[str]]:
    base_path = os.path.join("sets_de_pruebas", set_name)
    prompt_path = os.path.join(base_path, "prompt.txt")
    jd_path = os.path.join(base_path, "job_description.pdf")
    cvs_dir = os.path.join(base_path, "cvs")

    if not os.path.exists(prompt_path) or not os.path.exists(jd_path) or not os.path.isdir(cvs_dir):
        raise FileNotFoundError(f"Set incompleto: {set_name}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    cv_files = [
        os.path.join(cvs_dir, f)
        for f in os.listdir(cvs_dir)
        if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))
    ]
    cv_files.sort()

    return prompt, jd_path, cv_files

def run_batch(config: dict):
    set_name = config["set_name"]
    prompt, jd_path, cv_paths = load_set(set_name)
    batch_size = config["batch_size"]
    model = config["model"]

    adapter_class = ADAPTERS.get(model)
    if adapter_class is None:
        raise ValueError(f"Modelo no soportado: {model}")

    jd_text = extract_text(jd_path)
    adapter = adapter_class()
    results = []

    for i in range(0, len(cv_paths), batch_size):
        batch_paths = cv_paths[i:i + batch_size]
        cvs_texts = [extract_text(p) for p in batch_paths]

        if len(cvs_texts) < batch_size and len(cvs_texts) > 0:
            cvs_texts += [cvs_texts[-1]] * (batch_size - len(cvs_texts))

        print(f"===> Procesando CVs {i + 1} a {i + len(batch_paths)}...")
        response = adapter.send_request(prompt, jd_text, cvs_texts)

        try:
            candidate = response["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json_str = candidate.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(parsed_json_str)

            for persona in parsed if isinstance(parsed, list) else [parsed]:
                participant_id = str(uuid.uuid4())
                result_obj = {
                    "participant_id": participant_id,
                    "reasons": persona["reasons"],
                    "score": persona["score"]
                }
                results.append(result_obj)

                # Imprimir en consola
                print(f"👤 {result_obj['participant_id']}")
                print(f"   ✔ Score: {result_obj['score']}")
                for motivo in result_obj['reasons']:
                    print(f"   - {motivo}")
        except Exception as e:
            print("❌ Error al parsear la respuesta del modelo.")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("Detalles:", e)

        if model.lower().startswith("gemini"):
            print("⏱ Esperando 60 segundos por límite del free tier de Gemini...")
            time.sleep(60)

    # Guardar salida en archivo acumulando resultados
    # Obtener nombre del caso (última carpeta de set_name)
    case_name = os.path.basename(set_name)
    output_path = os.path.join("sets_de_pruebas", set_name, f"output-{case_name}.json")
    # Leer datos existentes si el archivo ya existe
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    # Acumular resultados
    all_results = existing_data + results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"📝 Resultados guardados en: {output_path}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    run_batch(config)
