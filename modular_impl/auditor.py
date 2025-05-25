import os

def check_caso_structure(caso_path):
    prompt_path = os.path.join(caso_path, "prompt.txt")
    if not os.path.isfile(prompt_path):
        print(f"❌ {caso_path}: falta prompt.txt")
        return

    for i in range(1, 4):
        set_path = os.path.join(caso_path, f"set{i}")
        if not os.path.isdir(set_path):
            print(f"❌ {caso_path}: falta carpeta set{i}/")
            continue

        jd_path = os.path.join(set_path, "job_description.pdf")
        cvs_path = os.path.join(set_path, "cvs")

        if not os.path.isfile(jd_path):
            print(f"❌ {set_path}: falta job_description.pdf")
        elif os.path.getsize(jd_path) == 0:
            print(f"⚠️  {set_path}: job_description.pdf está vacío")

        if not os.path.isdir(cvs_path):
            print(f"❌ {set_path}: falta carpeta cvs/")
        else:
            cv_files = [f for f in os.listdir(cvs_path) if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))]
            if not cv_files:
                print(f"⚠️  {set_path}: carpeta cvs/ vacía")
            else:
                print(f"✅ {set_path}: {len(cv_files)} CV(s)")

def run_auditor():
    base_dir = "sets_de_pruebas/pruebas_de_calidad"
    for rubro in os.listdir(base_dir):
        rubro_path = os.path.join(base_dir, rubro)
        if not os.path.isdir(rubro_path):
            continue
        for caso in os.listdir(rubro_path):
            caso_path = os.path.join(rubro_path, caso)
            if os.path.isdir(caso_path):
                check_caso_structure(caso_path)

if __name__ == "__main__":
    run_auditor()
