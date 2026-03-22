import os
from genetico.IndividuoA import IndividuoA
from genetico.Poblacion import Poblacion
from grid_search import (
    buscar_mejor_parametros
    , unzip_grid_search
    , tiempo_grid_search
)
import json

def figura_muestra_mutacion():
    """
    figura_muestra_mutacion - 
    
    Metodo para crear los datos de las figuras de la tesina del subcapítulo 6.3
    """
    path_base = os.path.join("Datos Tesina", "Figuras_Tablas", "6_3", "Mutacion")
    # Crear las carpetas si no existen
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    #inicializar individuo
    individuo = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_inicio.csv")
        , random_seed=42
    )
    
    #guardar resultado
    if not os.path.exists(os.path.join(path_base,"cromosoma_inicio.csv")):
        individuo.dataframe(path_save=os.path.join(path_base,"cromosoma_inicio.csv")
            , kwargs_to_csv={"index":False}
        )
    
    #guardar grafica gantt como se inicia el ejemplo
    individuo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_inicio.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_mutacion_1_inicio.png")
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118"]
            , "subtitulo" : ""
        }
    )
    
    #aplicar mutacion de mover periodo
    individuo.mutacion_mover_periodo(
        maquina="MAQ118", periodo=824, probabilidad_reducir=0, probabilidad_completo=1
        , guardar_en_cromosoma=True
    )

    #guardar grafica gantt con mutacion
    individuo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_mutacion_1.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_mutacion_1_mutado.png")
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118"]
            , "subtitulo" : ""
        }
    )
    
    #guardar grafica gantt con mutacion
    individuo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_inicio.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_mutacion_2_inicio.png")
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118","MAQ119"]
            , "subtitulo" : ""
        }
    )
    #aplicar mutacion de mover task mode
    #producto movido: GORGORÃO RIBBON , demanda: 12
    individuo.mutacion_cambiar_task_mode(
        maquina="MAQ118", periodo=367
        ,  guardar_en_cromosoma=True
    )
    
    #guardar grafica gantt con mutacion
    individuo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_mutacion_2.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_mutacion_2_mutado.png")
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118","MAQ119"]
            , "subtitulo" : ""
        }
    )

def figura_muestra_cruce():
    """
    figura_muestra_cruce - 
    
    Metodo para crear los datos de las figuras de la tesina del subcapítulo 6.3
    """
    path_base = os.path.join("Datos Tesina", "Figuras_Tablas", "6_3","Cruce")
    # Crear las carpetas si no existen
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    #inicializar individuos
    madre = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_1.csv")
        , random_seed=123
    )
    padre = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_2.csv")
        , random_seed=456
    )
    #guardar individuos
    if not os.path.exists(os.path.join(path_base,"cromosoma_1.csv")):
        madre.dataframe(path_save=os.path.join(path_base,"cromosoma_1.csv")
            , kwargs_to_csv={"index":False}
        )
    if not os.path.exists(os.path.join(path_base,"cromosoma_2.csv")):
        padre.dataframe(path_save=os.path.join(path_base,"cromosoma_2.csv")
            , kwargs_to_csv={"index":False}
        )
    #guardar graficas
    madre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_1.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_1.png")
    )
    padre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_2.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_2.png")
    )
    
    #crear hijo
    hijo, resultado = madre.cruce_time_leap(
        padre=padre
    )
    
    print(f"madre aptitud:{madre.aptitud()}")
    print(f"padre aptitud:{padre.aptitud()}")
    print(f"hijo aptitud:{hijo.aptitud()}, {resultado}")
    
    
    if not os.path.exists(os.path.join(path_base,"cromosoma_3.csv")):
        hijo.dataframe(path_save=os.path.join(path_base,"cromosoma_3.csv")
            , kwargs_to_csv={"index":False}
        )
    hijo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_3.csv")
        , kwargs_to_csv={
            "index":False
        }
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_3.png")
    )

def figura_poster_cruce():
    path_base = os.path.join("Datos Tesina", "Figuras_Tablas", "Poster","Cruce")
    # Crear las carpetas si no existen
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    #inicializar individuos
    madre = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_poster_1.csv")
        , random_seed=123
    )
    padre = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_poster_2.csv")
        , random_seed=456
    )

    #guardar individuos
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_1.csv")):
        madre.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_1.csv")
            , kwargs_to_csv={"index":False}
        )
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_2.csv")):
        padre.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_2.csv")
            , kwargs_to_csv={"index":False}
        )
    
    #crear hijo
    hijo, resultado = madre.cruce_time_leap(
        padre=padre
    )
    
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_3.csv")):
        hijo.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_3.csv")
            , kwargs_to_csv={"index":False}
        )

    madre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_1.csv")
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_poster_1.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118","MAQ120"]
            , "subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 8
            , "size_vertical" : 4
        }
        , max_value_x=192
        , titulo="Individuo madre"
        , kwargs_suptitle={
            "fontweight" : "bold"
            , "fontsize" : 18
        }
        , kwargs_subtitle={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_label={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontweight" : "bold"
            , "fontsize" : 12
        }
    )
    
    padre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_2.csv")
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_poster_2.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118","MAQ120"]
            , "subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 8
            , "size_vertical" : 4
        }
        , max_value_x=192
        , titulo="Individuo padre"
        , kwargs_suptitle={
            "fontweight" : "bold"
            , "fontsize" : 18
        }
        , kwargs_subtitle={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_label={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontweight" : "bold"
            , "fontsize" : 12
        }
    )
    
    hijo.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_3.csv")
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_poster_3.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={
            "mostrar_maquinas" : ["MAQ118","MAQ120"]
            , "subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 8
            , "size_vertical" : 8
        }
        , max_value_x=192
        , titulo="Individuo descendiente"
        , kwargs_suptitle={
            "fontweight" : "bold"
            , "fontsize" : 18
        }
        , kwargs_subtitle={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_label={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontweight" : "bold"
            , "fontsize" : 12
        }
    )

def figura_poster_mutacion():
    path_base = os.path.join("Datos Tesina", "Figuras_Tablas", "Poster","Mutacion")
    # Crear las carpetas si no existen
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    #inicializar individuos
    madre = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_poster_mutacion_1.csv")
        , random_seed=42
    )
    
    #guardar individuos
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_mutacion_1.csv")):
        madre.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_mutacion_1.csv")
            , kwargs_to_csv={"index":False}
        )
    
    madre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_mutacion_1.csv")
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_poster_1.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={"subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 8
            , "size_vertical" : 4
        }
        , max_value_x=192
        , titulo="Individuo, antes de mutación"
        , kwargs_suptitle={
            "fontweight" : "bold"
            , "fontsize" : 18
        }
        , kwargs_subtitle={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_label={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontweight" : "bold"
            , "fontsize" : 12
        }
    )
    
    for periodo_input in [3,15,27,36,46,55,66,89,102,116]:
        madre.mutacion_mover_periodo(
            maquina="MAQ118", periodo=periodo_input
            , probabilidad_completo=1, probabilidad_reducir=1
        )
    
    #cambiar el task en
    #MAQ119,152,163,SMOOTH ELASTIC(A),1,Harden[0.5] TM1,0,11,MAQ119|SMOOTH ELASTIC(A)|1|Harden[0.5] TM1|0
    madre.mutacion_cambiar_task_mode(
        maquina="MAQ119", periodo=152
    )
    
    #guardar individuos
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_mutacion_2.csv")):
        madre.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_mutacion_2.csv")
            , kwargs_to_csv={"index":False}
        )
    
    madre.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_mutacion_2.csv")
        , path_save_fig=os.path.join(path_base,"grafica_cromosoma_poster_2.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={"subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 8
            , "size_vertical" : 4
        }
        , max_value_x=192
        , titulo="Individuo, después de mutación"
        , kwargs_suptitle={
            "fontweight" : "bold"
            , "fontsize" : 18
        }
        , kwargs_subtitle={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_label={
            "fontweight" : "bold"
            , "fontsize" : 14
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontweight" : "bold"
            , "fontsize" : 12
        }
    )

def figura_poster_ejemplo():
    path_base = os.path.join("Datos Tesina", "Figuras_Tablas", "Poster","Ejemplo")
    
    # Crear las carpetas si no existen
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    #inicializar individuos
    ind = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_poster_ejemplo.csv")
        , random_seed=123
    )
    
    #guardar individuos
    if not os.path.exists(os.path.join(path_base,"cromosoma_poster_ejemplo.csv")):
        ind.dataframe(path_save=os.path.join(path_base,"cromosoma_poster_ejemplo.csv")
            , kwargs_to_csv={"index":False}
        )
    
    ind.grafica_gantt(
        path_save_df=os.path.join(path_base,"cromosoma_poster_ejemplo.csv")
        , path_save_fig=os.path.join(path_base,"cromosoma_poster_ejemplo.png")
        , kwargs_to_csv={
            "index":False
        }
        , kwargs_grafica={"subtitulo" : "" 
            , "mostrar_leyenda" : False
            , "size_horizontal" : 16
            , "size_vertical" : 9
            , "mostrar_leyenda" : False
        }
        , kwargs_suptitle={
            "fontsize" : 36
            , "fontweight" : "bold"
        }
        , kwargs_subtitle={
            "fontsize" : 18
            , "fontweight" : "bold"
        }
        , kwargs_label={
            "fontsize" : 18
            , "fontweight" : "bold"
        }
        , kwargs_fig={
            "transparent" : True
        }
        , kwargs_ticks = {
            "fontsize" : 18
            , "fontweight" : "bold"
        }
        , titulo="Actividades asignadas, ejemplo de un individuo"
    )
    
def optimizacion_final_tesis():
    
    dict_param, ubicacion = buscar_mejor_parametros()
    print("Mejor simulación:", ubicacion)
    print("Parámetros", dict_param)
    
    with open(os.path.join("Datos Tesina","algoritmo genetico"
            ,"Tesis","mejor_parametros.txt"), "w", encoding="utf-8") as f:
        json.dump(dict_param, f, ensure_ascii=False, indent=2)
    
    print("*"*50)
    print("Aptitud promedio")
    
    poblacion_1 = Poblacion(
        random_seed=12345
        , id_nombre="tesis_promedio"
        , n=20
        , probabilidad_mutacion=dict_param["p_mutacion"]
        , p_optimizacion_deterministica=dict_param["p_optimizacion_deterministica"]
        , p_saltar_periodo=dict_param["probabilidad_saltar_periodo"]
        , peso_seleccion_paso=dict_param["peso_seleccion_paso"]
        , peso_seleccion_demanda=dict_param["peso_seleccion_demanda"]
        , peso_mutacion_mover_periodo=dict_param["peso_mover_periodo"]
        , peso_mutacion_cambiar_task=dict_param["peso_cambiar_task"]
        , intentos_mutacion=dict_param["intentos_mutacion"]
        , prob_mutacion_mover_periodo_reducir=dict_param["probabilidad_reducir"]
        , prob_mutacion_mover_periodo_completa=dict_param["probabilidad_completo"]
        , generaciones=200
        , tiempo=None
    )
    
    poblacion_1.calcular_solucion(verbose=True)
    poblacion_1.guardar(path=os.path.join("Datos Tesina", "algoritmo genetico","Tesis"))

    print("*"*50)
    print("Aptitud makespan")
    
    poblacion_2 = Poblacion(
        random_seed=12345
        , id_nombre="tesis_ciclo_makespan"
        , n=20
        , probabilidad_mutacion=dict_param["p_mutacion"]
        , p_optimizacion_deterministica=dict_param["p_optimizacion_deterministica"]
        , p_saltar_periodo=dict_param["probabilidad_saltar_periodo"]
        , peso_seleccion_paso=dict_param["peso_seleccion_paso"]
        , peso_seleccion_demanda=dict_param["peso_seleccion_demanda"]
        , peso_mutacion_mover_periodo=dict_param["peso_mover_periodo"]
        , peso_mutacion_cambiar_task=dict_param["peso_cambiar_task"]
        , intentos_mutacion=dict_param["intentos_mutacion"]
        , prob_mutacion_mover_periodo_reducir=dict_param["probabilidad_reducir"]
        , prob_mutacion_mover_periodo_completa=dict_param["probabilidad_completo"]
        , generaciones=200
        , tiempo=None
    )
    
    poblacion_2.calcular_solucion(verbose=True
        , ciclo=dict(makespan=5,energia=5)
        , iniciar_makespan=True
    )
    poblacion_2.guardar(path=os.path.join("Datos Tesina", "algoritmo genetico","Tesis"))

    print("*"*50)
    print("Aptitud energia")
    
    poblacion_3 = Poblacion(
        random_seed=12345
        , id_nombre="tesis_ciclo_energia"
        , n=20
        , probabilidad_mutacion=dict_param["p_mutacion"]
        , p_optimizacion_deterministica=dict_param["p_optimizacion_deterministica"]
        , p_saltar_periodo=dict_param["probabilidad_saltar_periodo"]
        , peso_seleccion_paso=dict_param["peso_seleccion_paso"]
        , peso_seleccion_demanda=dict_param["peso_seleccion_demanda"]
        , peso_mutacion_mover_periodo=dict_param["peso_mover_periodo"]
        , peso_mutacion_cambiar_task=dict_param["peso_cambiar_task"]
        , intentos_mutacion=dict_param["intentos_mutacion"]
        , prob_mutacion_mover_periodo_reducir=dict_param["probabilidad_reducir"]
        , prob_mutacion_mover_periodo_completa=dict_param["probabilidad_completo"]
        , generaciones=200
        , tiempo=None
    )
    
    poblacion_3.calcular_solucion(verbose=True
        , ciclo=dict(makespan=5,energia=5)
        , iniciar_makespan=False
    )
    poblacion_3.guardar(path=os.path.join("Datos Tesina", "algoritmo genetico","Tesis"))

    print("*"*50)
    print("Aptitud 10makespan 5energia")
    
    poblacion_4 = Poblacion(
        random_seed=12345
        , id_nombre="tesis_ciclo_10makespan_5energia"
        , n=20
        , probabilidad_mutacion=dict_param["p_mutacion"]
        , p_optimizacion_deterministica=dict_param["p_optimizacion_deterministica"]
        , p_saltar_periodo=dict_param["probabilidad_saltar_periodo"]
        , peso_seleccion_paso=dict_param["peso_seleccion_paso"]
        , peso_seleccion_demanda=dict_param["peso_seleccion_demanda"]
        , peso_mutacion_mover_periodo=dict_param["peso_mover_periodo"]
        , peso_mutacion_cambiar_task=dict_param["peso_cambiar_task"]
        , intentos_mutacion=dict_param["intentos_mutacion"]
        , prob_mutacion_mover_periodo_reducir=dict_param["probabilidad_reducir"]
        , prob_mutacion_mover_periodo_completa=dict_param["probabilidad_completo"]
        , generaciones=200
        , tiempo=None
    )
    
    poblacion_4.calcular_solucion(verbose=True
        , ciclo=dict(makespan=10,energia=5)
        , iniciar_makespan=True
    )
    poblacion_4.guardar(path=os.path.join("Datos Tesina", "algoritmo genetico","Tesis"))

    print("*"*50)
    print("Aptitud 10energia 5makespan")
    
    poblacion_5 = Poblacion(
        random_seed=12345
        , id_nombre="tesis_ciclo_10energia_5makespan"
        , n=20
        , probabilidad_mutacion=dict_param["p_mutacion"]
        , p_optimizacion_deterministica=dict_param["p_optimizacion_deterministica"]
        , p_saltar_periodo=dict_param["probabilidad_saltar_periodo"]
        , peso_seleccion_paso=dict_param["peso_seleccion_paso"]
        , peso_seleccion_demanda=dict_param["peso_seleccion_demanda"]
        , peso_mutacion_mover_periodo=dict_param["peso_mover_periodo"]
        , peso_mutacion_cambiar_task=dict_param["peso_cambiar_task"]
        , intentos_mutacion=dict_param["intentos_mutacion"]
        , prob_mutacion_mover_periodo_reducir=dict_param["probabilidad_reducir"]
        , prob_mutacion_mover_periodo_completa=dict_param["probabilidad_completo"]
        , generaciones=200
        , tiempo=None
    )
    
    poblacion_5.calcular_solucion(verbose=True
        , ciclo=dict(makespan=5,energia=10)
        , iniciar_makespan=False
    )
    poblacion_5.guardar(path=os.path.join("Datos Tesina", "algoritmo genetico","Tesis"))

    print("Terminado")


def prueba_optimizacion():
    
    path_base = os.path.join("Datos Tesina", "Pruebas", "Optimizacion_deterministica")
    if not os.path.exists(path_base):
        os.makedirs(path_base, exist_ok=True)
    
    individuo = IndividuoA(
        inicializar=True
        , saved_path=os.path.join(path_base,"cromosoma_inicio.csv")
        , random_seed=1234
    )
    
    individuo.dataframe(path_save=os.path.join(path_base,"cromosoma_inicio.csv")
        , kwargs_to_csv={"index":False}
    )
    
    print(individuo.aptitud())
    
    individuo.optimizacion_deterministica(os.path.join(path_base,"optimizacion_deterministica.csv"))
    
    individuo.dataframe(path_save=os.path.join(path_base,"cromosoma_optimizado.csv")
        , kwargs_to_csv={"index":False}
    )
    
    print(individuo.aptitud())

def main():
    #crear resultado de la tesis
    unzip_grid_search()
    #tiempo_gs = tiempo_grid_search()
    #print(tiempo_gs)
    optimizacion_final_tesis()
    
if __name__ == "__main__":
    main()
    