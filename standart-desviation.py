import json
import statistics


def calculate_score_standard_deviation(json_file_path):
    try:
        data = []
        for i in range(3):
            file_path = json_file_path + "set" + str(i + 1) + "/output-set" + str(i + 1) + ".json"
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                for item in file_data:
                    data.append(item)

    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_file_path}'. Please check the file format.")
        return None

    scores = []
    for item in data:
        if isinstance(item, dict) and "score" in item:
            scores.append(item['score'])
        else:
            print(f"Warning: Skipping an item with an invalid format: {item}")

    if not scores:
        print("No scores found in the JSON file to calculate standard deviation.")
        return 0.0 # Return 0 if no scores, or you could return None

    try:
        std_dev = statistics.stdev(scores)
        return std_dev
    except statistics.StatisticsError as e:
        print(f"Error calculating standard deviation: {e}")
        print("This might happen if there's only one score, in which case the standard deviation is 0.")
        return 0.0 # Standard deviation of a single data point is 0.0

if __name__ == "__main__":

    casos = ["admin_finanzas", "diseño_grafico", "ejecutivo_cuentas_digitales", "ejecutivo_influencers", "ingenieria_informatica", "rrhh", "tecnico_mantenimiento"]
    cantidad_casos = 5

    for caso in casos:
        for i in range(cantidad_casos):
            json_file_path = "sets_de_pruebas/pruebas_de_calidad/"+ caso + "/caso" + str(i + 1) + "/"
            std_dev = calculate_score_standard_deviation(json_file_path)
            print("Standard Deviation for " + caso + " Caso " + str(i + 1) + ": " + str(round(std_dev, 2)))
