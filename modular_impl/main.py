import json
import os
import time
from dotenv import load_dotenv
from utils.file_utils import extract_text
# from adapters.gpt4omini_adapter import GPT4oMiniAdapter
from adapters.gemini_adapter import GeminiFlashAdapter

ADAPTERS = {
    "gpt4omini": GPT4oMiniAdapter,
    "gemini": GeminiFlashAdapter,
}

def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_set(set_name: str) -> tuple[str, str, list[str]]:
    base_path = os.path.join("sets", set_name)
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

    for i in range(0, len(cv_paths), batch_size):
        batch_paths = cv_paths[i:i+batch_size]
        cvs_texts = [extract_text(p) for p in batch_paths]
        print(f"\n===> Procesando CVs {i+1} a {i+len(batch_paths)}...")
        result = adapter.send_request(prompt, jd_text, cvs_texts)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if model.lower().startswith("gemini"):
            print("Esperando 60 segundos por límite del free tier de Gemini...")
            time.sleep(60)

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    run_batch(config)
