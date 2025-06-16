import json

def clear_json_file():
    try:
        casos = ["admin_finanzas", "diseño_grafico", "ejecutivo_cuentas_digitales", "ejecutivo_influencers","ingenieria_informatica", "rrhh", "tecnico_mantenimiento"]
        for caso in casos:
            for i in range(6):
                sets = [10, 30, 50]
                for set in sets:
                    file_name = "sets_de_pruebas/pruebas de cantidad/" + caso + "/caso" + str(i + 1) + "/output-set" + str(set) + ".json"
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write("[]")

    except IOError as e:
        print("")

if __name__ == "__main__":
    clear_json_file()