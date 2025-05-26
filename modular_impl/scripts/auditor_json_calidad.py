import os
import json

def is_json_empty(filepath):
    try:
        if os.path.getsize(filepath) == 0:
            return True
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data == [] or data == {} or data is None
    except Exception:
        return True  # Si no se puede leer/parsing, lo consideramos vacío

base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sets_de_pruebas", "pruebas_de_calidad"))

for rubro in os.listdir(base):
    rubro_path = os.path.join(base, rubro)
    if not os.path.isdir(rubro_path):
        continue
    for caso in os.listdir(rubro_path):
        caso_path = os.path.join(rubro_path, caso)
        if not os.path.isdir(caso_path):
            continue
        for set_x in os.listdir(caso_path):
            set_path = os.path.join(caso_path, set_x)
            if not os.path.isdir(set_path):
                continue
            for file in os.listdir(set_path):
                if file.endswith(".json"):
                    json_path = os.path.join(set_path, file)
                    if is_json_empty(json_path):
                        print(f"VACÍO: {json_path} (set: {set_x})")

