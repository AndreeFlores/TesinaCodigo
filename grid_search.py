from algoritmo_genetico import Poblacion
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import json
import pandas as pd
from typing import Literal
import zipfile

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

def realizar_busqueda(
        num_workers : int = None
        , verbose : bool = False
    ):
    
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
            if verbose:
                print(f"Leídos {len(items)} items desde {filename}")
        except Exception as e:
            if verbose:
                print(f"Error leyendo {filename}: {e}. Se usarán las combinaciones generadas y se reescribirá el archivo.")
            save_items_to_file(items,fname=filename)
    else:
        save_items_to_file(items,fname=filename)
        if verbose:
            print(f"Items guardados en {filename}")  
    
    # Ajusta max_workers, None para que concurrent.futures elija
    with ProcessPoolExecutor(max_workers=num_workers) as exe:
        futuros = {exe.submit(worker, it): it[0] for it in items}
        for futuro in as_completed(futuros):
            key = futuros[futuro]
            try:
                resultado = futuro.result()
                if verbose:
                    print(f"Combinación procesada: {resultado}", end="\r")
            except Exception as e:
                if verbose:
                    print(f"Error en combinación {key}: {e}")

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

def buscar_mejor_parametros(
        tipo_optimizacion : Literal['absoluto','porcentaje'] = 'porcentaje'
    ) -> tuple[dict, str]:
    """
    buscar_mejor_parametros - 
    
    Devuelve los mejores parámetros y la ubicación de la mejor
    población encontrada en la búsqueda.
    
    Parameters
    ----------
    tipo_optimizacion (Literal['absoluto','porcentaje'], optional, defaults to 'porcentaje') :
        Criterio utilizado para comparar poblaciones:
        * 'absoluto': regresa la población con la menor aptitud
        * 'porcentaje': regresa la población con la mayor disminución porcentual de la aptitud
    
    Returns
    -------
    tuple[dict, str] :
        Tupla con elementos:
        * diccionario con los parámetros y sus valores
        * str con la ubicación de los parámetros
    """
    
    base_dir = os.path.join("Datos Tesina", "algoritmo genetico","grid search")
    if not os.path.isdir(base_dir):
        archivos_path = []
    else:
        archivos_path = [
            os.path.join(base_dir, f)
            for f in os.listdir(base_dir)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(base_dir, f))
        ]
    
    aptitud_acumulada : float = None
    mejor_archivo : str = None
    porc_mejora_acumulada : float = None
    
    for archivo_path in archivos_path:
        with open(archivo_path,"r") as archivo:
            
            lineas = archivo.readlines()
            promedio_aptitud_inicio : float = float(lineas[22-1].removeprefix("promedio de aptitud "))
            promedio_aptitud_final : float = float(lineas[62-1].removeprefix("promedio de aptitud "))
            porc_mejora = (promedio_aptitud_final - promedio_aptitud_inicio) / promedio_aptitud_inicio
            aptitud_incumbente : float = float(lineas[2-1].removeprefix("resultado: "))
            
            #revisa que el archivo es viable
            if promedio_aptitud_final < promedio_aptitud_inicio:
                match tipo_optimizacion:
                    case "porcentaje":
                        if porc_mejora_acumulada is None:
                            porc_mejora_acumulada = porc_mejora
                            mejor_archivo = archivo_path
                        if porc_mejora < porc_mejora_acumulada:
                            porc_mejora_acumulada = porc_mejora
                            mejor_archivo = archivo_path
                    case "absoluto":
                        if aptitud_acumulada is None:
                            aptitud_acumulada = aptitud_incumbente
                            mejor_archivo = archivo_path
                        if aptitud_incumbente < aptitud_acumulada:
                            aptitud_acumulada = aptitud_incumbente
                            mejor_archivo = archivo_path
    
    if mejor_archivo is None:
        return None, None
    
    parametros = dict()
    with open(mejor_archivo,"r") as archivo:
        lineas = archivo.readlines()
            
        parametros["cantidad_individuos"] = int(lineas[5-1].removeprefix("cantidad_individuos: "))
        parametros["p_mutacion"] = float(lineas[6-1].removeprefix("p_mutacion: "))
        
        cantidad_maxima_generaciones = lineas[7-1].removeprefix("cantidad_maxima_generaciones: ")
        parametros["cantidad_maxima_generaciones"] = cantidad_maxima_generaciones if cantidad_maxima_generaciones is None else int(cantidad_maxima_generaciones)
        
        tiempo_maximo = lineas[8-1].removeprefix("tiempo_maximo: ")
        parametros["tiempo_maximo"] = tiempo_maximo if tiempo_maximo is None else float(tiempo_maximo)
        
        parametros["p_optimizacion_deterministica"] = float(lineas[9-1].removeprefix("p_optimizacion_deterministica: "))
        parametros["probabilidad_saltar_periodo"] = float(lineas[10-1].removeprefix("probabilidad_saltar_periodo: "))
        parametros["peso_seleccion_paso"] = float(lineas[11-1].removeprefix("peso_seleccion_paso: "))
        parametros["peso_seleccion_demanda"] = float(lineas[12-1].removeprefix("peso_seleccion_demanda: "))
        parametros["peso_mover_periodo"] = float(lineas[13-1].removeprefix("peso_mover_periodo: "))
        parametros["peso_cambiar_task"] = float(lineas[14-1].removeprefix("peso_cambiar_task: "))
        parametros["intentos_mutacion"] = int(lineas[15-1].removeprefix("intentos_mutacion: "))
        parametros["probabilidad_reducir"] = float(lineas[16-1].removeprefix("probabilidad_reducir: "))
        parametros["probabilidad_completo"] = float(lineas[17-1].removeprefix("probabilidad_completo: "))
    
    return parametros, mejor_archivo

def tiempo_grid_search():
    tiempo_total : float = 0
    base_dir = os.path.join("Datos Tesina", "algoritmo genetico","grid search")
    if not os.path.isdir(base_dir):
        archivos_path = []
    else:
        archivos_path = [
            os.path.join(base_dir, f)
            for f in os.listdir(base_dir)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(base_dir, f))
        ]
    
    for archivo_path in archivos_path:
        with open(archivo_path,"r") as archivo:
            lineas = archivo.readlines()
            
            for linea_tiempo in range(23,63+1,4):
                tiempo_generacion = float(
                    lineas[linea_tiempo-1].removeprefix("tiempo de creacion de generacion (segundos) ")
                )
                
                tiempo_total = tiempo_total + tiempo_generacion
    
    return tiempo_total

def zip_grid_search(
        base_dir : str | None = None
        , nombre_zip : str = "grid_search.zip"
    ):
    """
    zip_grid_search - 
    
    Guarda los resultados de las poblaciones en el grid search en un archivo .zip
    
    Parameters
    ----------
    base_dir (str | None, optional, defaults to None) :
        Ubicación de los archivos
    
    nombre_zip (str, optional, defaults to "grid_search.zip") :
        Nombre del archivo .zip
    
    Raises
    ------
    FileExistsError :
        Si la ubicación `base_dir` no existe
    
    """
    
    if base_dir is None:
        base_dir = os.path.join("Datos Tesina", "algoritmo genetico","grid search")
        
    if not os.path.exists(base_dir):
        raise FileExistsError(f"{base_dir} no existe")
    
    if not os.path.isdir(base_dir):
        archivos_path = []
    else:
        archivos_path = [
            os.path.join(base_dir, f)
            for f in os.listdir(base_dir)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(base_dir, f))
        ]
    
    with zipfile.ZipFile(os.path.join(base_dir,nombre_zip),"w") as file:
        for archivo in archivos_path:
            file.write(archivo)

def unzip_grid_search(
        base_dir : str | None = None
        , nombre_zip : str = "grid_search.zip"
    ):
    """
    unzip_grid_search - 
    
    Guarda los resultados de las poblaciones de un archivo .zip en `base_dir`
    
    Parameters
    ----------
    base_dir (str | None, optional, defaults to None) :
        Ubicación de los archivos
    
    nombre_zip (str, optional, defaults to "grid_search.zip") :
        Nombre del archivo .zip
    
    Raises
    ------
    FileExistsError :
        Si la ubicación `base_dir` no existe
    
    """
    
    if base_dir is None:
        base_dir = os.path.join("Datos Tesina", "algoritmo genetico","grid search")
        
    if not os.path.exists(base_dir):
        raise FileExistsError(f"El archivo {base_dir} no existe")
    
    with zipfile.ZipFile(os.path.join(base_dir, nombre_zip), "r") as file:
        file.extractall(base_dir)

def main(verbose : bool = False):
    num_workers : int = max(os.cpu_count()-2,1)
    
    if verbose:
        print(f"Cantidad de cores: {num_workers}")
    
    realizar_busqueda(num_workers=num_workers, verbose=verbose)
    
    resultados()
    dict_param, ubicacion = buscar_mejor_parametros()
    
    tiempo_total_segundos = tiempo_grid_search()
    if verbose:
        print(f"Tiempo total de busqueda: {tiempo_total_segundos} segundos")
    
    zip_grid_search()

if __name__ == "__main__":
    main(verbose=True)
    