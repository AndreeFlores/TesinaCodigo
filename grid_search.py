from algoritmo_genetico import Poblacion, buscar_mejor_parametros
from itertools import product
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import json
import pandas as pd

def worker(item) -> str:
    """
    worker - Actividad que realizará un worker
    """

    key, value = item
    key = str(key)
    
    path_base = os.path.join("Datos Tesina", "algoritmo genetico","grid search")
    path = os.path.join(path_base,f"{key}.txt")
    # ya existe simulacion de estos parametros
    if os.path.exists(path):
        return key

    pob = Poblacion(
        **value,
        id_nombre=key,
        random_seed=1234
    )
    pob.calcular_solucion()
    pob.guardar(path=path_base)
    
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

    filename = os.path.join("Datos Tesina", "algoritmo genetico","grid search","parametros", "grid_items.txt")
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

def resultados():
    """
    resultados - 
    
    Crea una dataframe con la información del grid search
    """
    base = os.path.join("Datos Tesina","algoritmo genetico","grid search")
    filename_parametros = os.path.join(base, "parametros", "grid_items.txt")
    os.makedirs(os.path.dirname(filename_parametros), exist_ok=True)

    if os.path.exists(filename_parametros):
        try:
            items = load_items_from_file(fname=filename_parametros)
            print(f"Leídos {len(items)} items desde {filename_parametros}")
        except Exception as e:
            print(f"Error leyendo {filename_parametros}: {e}. Se usarán las combinaciones generadas y se reescribirá el archivo.")
            save_items_to_file(items,fname=filename_parametros)
    else:
        raise FileExistsError("Archivo de parametros no existe, utiliza main()")

    df = pd.DataFrame(
        columns=["Simulacion", "cantidad_individuos", "p_mutacion"
        , "cantidad_maxima_generaciones", "tiempo_maximo", "p_optimizacion_deterministica"
        , "probabilidad_saltar_periodo", "peso_seleccion_paso", "peso_seleccion_demanda"
        , "peso_mover_periodo", "peso_cambiar_task", "intentos_mutacion"
        , "probabilidad_reducir", "probabilidad_completo"
        , "Generacion 0", "Generacion 1", "Generacion 2", "Generacion 3", "Generacion 4"
        , "Generacion 5", "Generacion 6", "Generacion 7", "Generacion 8", "Generacion 9"
        , "Generacion 10", "Valor_Incumbente"
    ])

    for simulacion in items:
        filename = os.path.join(base,f"{simulacion[0]}.txt")
        with open(filename,"r", encoding="utf-8") as archivo:
            fila = dict()

            lineas = archivo.readlines()

            # Inicializar campos de Generacion (Generacion 0...10)
            for i in range(11):
                fila[f"Generacion {i}"] = None

            current_gen = None

            # Parsear líneas buscando prefijos conocidos
            for raw in lineas:
                s = raw.strip()
                if not s:
                    continue

                if s.startswith("nombre: "):
                    try:
                        fila["Simulacion"] = int(s.removeprefix("nombre: ").strip())
                    except Exception:
                        fila["Simulacion"] = s.removeprefix("nombre: ").strip()

                elif s.startswith("resultado: "):
                    fila["Valor_Incumbente"] = float(s.removeprefix("resultado: ").strip())

                elif s.startswith("cantidad_individuos: "):
                    fila["cantidad_individuos"] = int(s.removeprefix("cantidad_individuos: ").strip())

                elif s.startswith("p_mutacion: "):
                    fila["p_mutacion"] = float(s.removeprefix("p_mutacion: ").strip())

                elif s.startswith("cantidad_maxima_generaciones: "):
                    fila["cantidad_maxima_generaciones"] = int(s.removeprefix("cantidad_maxima_generaciones: ").strip())

                elif s.startswith("tiempo_maximo: "):
                    fila["tiempo_maximo"] = int(s.removeprefix("tiempo_maximo: ").strip())

                elif s.startswith("p_optimizacion_deterministica: "):
                    fila["p_optimizacion_deterministica"] = float(s.removeprefix("p_optimizacion_deterministica: ").strip())

                elif s.startswith("probabilidad_saltar_periodo: "):
                    fila["probabilidad_saltar_periodo"] = float(s.removeprefix("probabilidad_saltar_periodo: ").strip())

                elif s.startswith("peso_seleccion_paso: "):
                    fila["peso_seleccion_paso"] = int(s.removeprefix("peso_seleccion_paso: ").strip())

                elif s.startswith("peso_seleccion_demanda: "):
                    fila["peso_seleccion_demanda"] = int(s.removeprefix("peso_seleccion_demanda: ").strip())

                elif s.startswith("peso_mover_periodo: "):
                    fila["peso_mover_periodo"] = int(s.removeprefix("peso_mover_periodo: ").strip())

                elif s.startswith("peso_cambiar_task: "):
                    fila["peso_cambiar_task"] = int(s.removeprefix("peso_cambiar_task: ").strip())

                elif s.startswith("intentos_mutacion: "):
                    fila["intentos_mutacion"] = int(s.removeprefix("intentos_mutacion: ").strip())

                elif s.startswith("probabilidad_reducir: "):
                    fila["probabilidad_reducir"] = float(s.removeprefix("probabilidad_reducir: ").strip())

                elif s.startswith("probabilidad_completo: "):
                    fila["probabilidad_completo"] = float(s.removeprefix("probabilidad_completo: ").strip())

                # Bloque de generaciones: detectar índice y luego el promedio de aptitud
                elif s.startswith("Generacion "):
                    parts = s.split()
                    try:
                        current_gen = int(parts[1])
                    except Exception:
                        current_gen = None

                elif s.startswith("promedio de aptitud"):
                    # formato esperado: "promedio de aptitud <valor>"
                    try:
                        val = float(s.removeprefix("promedio de aptitud ").strip())
                    except Exception:
                        # fallback: tomar el último token
                        try:
                            val = float(s.split()[-1])
                        except Exception:
                            val = None

                    if current_gen is not None:
                        fila[f"Generacion {current_gen}"] = val

            # Añadir la fila al DataFrame
            df_fila = pd.DataFrame(data=fila, index=[0])
            
            if len(df.index) == 0:
                df = df_fila
            else:
                df : pd.DataFrame = pd.concat([df, df_fila], ignore_index=True)
            print(f"Cantidad de filas {len(df.index)}")
    
    df["Porc_Mejora_Aptitud"] = (df["Generacion 10"] - df["Generacion 0"]) / df["Generacion 0"]
    df["Hubo_Mejora"] = df["Generacion 10"] < df["Generacion 0"]
    
    path_csv = os.path.join("Datos Tesina","algoritmo genetico","grid search","resultados","analisis_grid_search.csv")
    os.makedirs(os.path.dirname(path_csv), exist_ok=True)
    
    df.to_csv(
        os.path.join(path_csv)
        , index=False
        , columns=["Simulacion", "cantidad_individuos", "p_mutacion"
            , "cantidad_maxima_generaciones", "tiempo_maximo", "p_optimizacion_deterministica"
            , "probabilidad_saltar_periodo", "peso_seleccion_paso", "peso_seleccion_demanda"
            , "peso_mover_periodo", "peso_cambiar_task", "intentos_mutacion"
            , "probabilidad_reducir", "probabilidad_completo"
            , "Generacion 0", "Generacion 1", "Generacion 2", "Generacion 3", "Generacion 4"
            , "Generacion 5", "Generacion 6", "Generacion 7", "Generacion 8", "Generacion 9"
            , "Generacion 10", "Valor_Incumbente", "Hubo_Mejora", "Porc_Mejora_Aptitud"
        ]
        , encoding="utf-8"
    )
    
if __name__ == "__main__":
    #num_workers : int = max(os.cpu_count()-2,1)
    
    #main(num_workers=num_workers)
    
    #print(buscar_mejor_parametros())
    
    resultados()