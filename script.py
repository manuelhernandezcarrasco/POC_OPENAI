import json

# Ruta a tu archivo JSON
json_path = "token-usage.json"

# Cargar el archivo JSON
with open(json_path, "r") as f:
    data = json.load(f)

# Recorrer y mostrar los prompt_tokens_image
for i, entry in enumerate(data, start=1):
    image_tokens = entry.get("response_tokens", "No encontrado")
    print(image_tokens)