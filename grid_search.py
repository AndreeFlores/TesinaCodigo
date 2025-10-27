from algoritmo_genetico import Poblacion
from itertools import product
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import json

def worker(item) -> str:
    """
    worker - Actividad que realizará un worker
    """

    key, value = item
    key = str(key)
    
    path = os.path.join("Datos Tesina", "algoritmo genetico",f"{key}.txt")
    # ya existe simulacion de estos parametros
    if os.path.exists(path):
        return key

    pob = Poblacion(
        **value,
        id_nombre=key,
        random_seed=1234
    )
    pob.calcular_solucion()
    pob.guardar()
    
    return key

def main(num_workers : int = None):
    
    valores_probabilidad_mutacion = [0.01,0.05,0.1] #listo
    valores_generaciones = [10]
    valores_tiempo = [3600]
    valores_peso_mutacion_mover_periodo = [1,4] #listo
    valores_peso_mutacion_cambiar_task = [1,4] #listo
    valores_p_saltar_periodo = [0.05,0.33] #listo
    valores_peso_seleccion_paso = [1,2,4] #listo
    valores_peso_seleccion_demanda = [1,2,4] #listo
    valores_prob_mutacion_mover_periodo_reducir = [0.33,0.66] #listo
    valores_prob_mutacion_mover_periodo_completa = [0.33,0.66] #listo
    valores_intentos_mutacion = [1,2,10] #listo
    valores_p_optimizacion_deterministica = [0.0,1.0] #listo
    
    parametros = [
        "probabilidad_mutacion",
        "generaciones",
        "tiempo",
        "peso_mutacion_mover_periodo",
        "peso_mutacion_cambiar_task",
        "p_saltar_periodo",
        "peso_seleccion_paso",
        "peso_seleccion_demanda",
        "prob_mutacion_mover_periodo_reducir",
        "prob_mutacion_mover_periodo_completa",
        "intentos_mutacion",
        "p_optimizacion_deterministica",
    ]

    valores = [
        valores_probabilidad_mutacion,
        valores_generaciones,
        valores_tiempo,
        valores_peso_mutacion_mover_periodo,
        valores_peso_mutacion_cambiar_task,
        valores_p_saltar_periodo,
        valores_peso_seleccion_paso,
        valores_peso_seleccion_demanda,
        valores_prob_mutacion_mover_periodo_reducir,
        valores_prob_mutacion_mover_periodo_completa,
        valores_intentos_mutacion,
        valores_p_optimizacion_deterministica,
    ]

    # Diccionario con todas las combinaciones
    dict_combinaciones = {
        idx: dict(zip(parametros, combo))
        for idx, combo in enumerate(product(*valores), start=1)
    }
    items = list(dict_combinaciones.items())

    filename = os.path.join("Datos Tesina", "algoritmo genetico", "grid_items.txt")
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Guardar o leer items desde archivo .txt (JSON)
    if os.path.exists(filename):
        try:
            items = load_items_from_file(fname=filename)
            print(f"Leídos {len(items)} items desde {filename}")
        except Exception as e:
            print(f"Error leyendo {filename}: {e}. Se usarán las combinaciones generadas y se reescribirá el archivo.")
            save_items_to_file(items,fname=filename)
    else:
        save_items_to_file(items,fname=filename)
        print(f"Items guardados en {filename}")

    tiempo_inicio = time.time()
    
    print("Iniciando busqueda grid search")
    
    # Ajusta max_workers, None para que concurrent.futures elija
    with ProcessPoolExecutor(max_workers=num_workers) as exe:
        futuros = {exe.submit(worker, it): it[0] for it in items}
        for futuro in as_completed(futuros):
            key = futuros[futuro]
            try:
                resultado = futuro.result()
                print(f"Combinación procesada: {resultado}")
            except Exception as e:
                print(f"Error en combinación {key}: {e}")
    
    tiempo_final = time.time() - tiempo_inicio
    
    print(f"Tiempo total: {tiempo_final:.2f}")

def save_items_to_file(items_list, fname):
    # items_list: list of (idx, dict)
    serializable = [[int(k), v] for k, v in items_list]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

def load_items_from_file(fname):
    with open(fname, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [(int(entry[0]), entry[1]) for entry in data]

if __name__ == "__main__":
    num_workers : int = max(os.cpu_count()-2,1)
    
    main(num_workers=num_workers)