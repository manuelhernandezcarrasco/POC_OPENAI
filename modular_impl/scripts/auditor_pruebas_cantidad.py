import os
from pathlib import Path

def check_case(caso_path, caso_num):
    prompt_path = os.path.join(caso_path, "prompt.txt")
    jd_path = os.path.join(caso_path, "job_description.pdf")
    outputs = [f"output-set{i}.json" for i in (10, 30, 50)]
    outputs_present = [f for f in outputs if os.path.isfile(os.path.join(caso_path, f))]

    if not os.path.isfile(prompt_path):
        print(f"❌ {caso_path}: falta prompt.txt")
    elif os.path.getsize(prompt_path) == 0:
        print(f"⚠️  {caso_path}: prompt.txt está vacío")

    if not os.path.isfile(jd_path):
        print(f"❌ {caso_path}: falta job_description.pdf")
    elif os.path.getsize(jd_path) == 0:
        print(f"⚠️  {caso_path}: job_description.pdf está vacío")

    if len(outputs_present) != 3:
        print(f"⚠️  {caso_path}: se encontraron {len(outputs_present)} archivos output-set*.json")

    cvs_dir = os.path.join(caso_path, "cvs")
    no_dir = os.path.join(cvs_dir, "no")
    si_dir = os.path.join(cvs_dir, "si")

    def count_files(folder):
        folder_path = Path(folder)
        if not folder_path.is_dir():
            return -1
        return len([f for f in folder_path.iterdir() if f.suffix.lower() in [".pdf", ".jpg", ".jpeg", ".png"]])

    no_count = count_files(no_dir)
    si_count = count_files(si_dir)

    expected = {
        "1": (20, 30),
        "2": (20, 30),
        "3": (0, 50),
        "4": (0, 50),
        "5": (20, 30),
        "6": (0, 50),
    }
    expected_no, expected_si = expected.get(str(caso_num), (None, None))

    if expected_no is not None:
        if no_count == -1:
            print(f"❌ {caso_path}: falta carpeta cvs/no")
        elif expected_no == 0 and no_count != 0:
            print(f"❌ {caso_path}: cvs/no debería estar vacía pero tiene {no_count} archivo(s)")
        elif expected_no > 0 and no_count != expected_no:
            print(f"❌ {caso_path}: cvs/no debería tener {expected_no} archivos pero tiene {no_count}")

    if expected_si is not None:
        if si_count == -1:
            print(f"❌ {caso_path}: falta carpeta cvs/si")
        elif si_count != expected_si:
            print(f"❌ {caso_path}: cvs/si debería tener {expected_si} archivos pero tiene {si_count}")
        else:
            print(f"✅ {caso_path}: si={si_count} no={no_count}")


def audit_pruebas_cantidad():
    # Calcular la ruta absoluta correctamente desde la ubicación del script
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sets_de_pruebas", "pruebas de cantidad"))
    if not os.path.isdir(base_dir):
        print(f"❌ La carpeta base no existe: {base_dir}")
        return
    for rubro in os.listdir(base_dir):
        rubro_path = os.path.join(base_dir, rubro)
        if not os.path.isdir(rubro_path):
            continue
        print(f"\n🔎 Auditando rubro: {rubro}")
        for i in range(1, 7):
            caso_path = os.path.join(rubro_path, f"caso{i}")
            if os.path.isdir(caso_path):
                check_case(caso_path, i)

if __name__ == "__main__":
    audit_pruebas_cantidad()
