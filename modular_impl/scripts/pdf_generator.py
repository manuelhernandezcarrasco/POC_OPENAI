import os
from PyPDF2 import PdfWriter
import random

output_dir = "pdfs_corruptos"
os.makedirs(output_dir, exist_ok=True)

# 1. PDFs completamente vacíos (válidos pero sin contenido)
for i in range(5):
    writer = PdfWriter()
    with open(f"{output_dir}/vacio_{i+1}.pdf", "wb") as f:
        writer.write(f)

# 2. PDFs con texto ilegible (bytes aleatorios como contenido)
for i in range(5):
    with open(f"{output_dir}/ilegible_{i+1}.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n")
        f.write(os.urandom(2048))  # 2KB de basura
        f.write(b"\n%%EOF")

# 3. PDFs truncados (simulan estar corruptos por corte)
for i in range(5):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    temp_file = f"{output_dir}/temp_{i}.pdf"
    final_file = f"{output_dir}/truncado_{i+1}.pdf"

    with open(temp_file, "wb") as f:
        writer.write(f)

    # Cortamos el archivo a la mitad
    with open(temp_file, "rb") as f:
        data = f.read()
    with open(final_file, "wb") as f:
        f.write(data[:len(data)//2])  # Cortamos a la mitad

    os.remove(temp_file)

# 4. Archivos con extensión .pdf pero que no son PDFs reales
for i in range(5):
    with open(f"{output_dir}/falso_{i+1}.pdf", "w") as f:
        f.write("Este no es un archivo PDF real.\n" * 10)

print(f"✅ 20 archivos creados en: {output_dir}")