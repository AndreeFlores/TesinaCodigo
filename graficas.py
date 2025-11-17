import numpy as np
import pandas as pd
from Carga_Datos import Datos, str_a_task_mode, task_mode_a_str
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.ticker import MaxNLocator
import os

CUSTOM_COLOR_MAP = ListedColormap(
    [
        "#CF01FB", "#B100D7", "#9400B4", "#770092", "#5B0070",
        "#B57D00", "#9A6A00", "#815700", "#674500", "#4F3400",
        "#009C9F", "#008588", "#006F71", "#00595A", "#004344"
    ]
)

def buscar_mejor_parametros() -> tuple[dict, str]:
    """
    buscar_mejor_parametros - 
    
    Devuelve los mejores parámetros y la ubicación de la mejor
    población encontrada en la búsqueda.
    
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
            #revisa que el archivo es viable
            if promedio_aptitud_final < promedio_aptitud_inicio:
                aptitud_incumbente : float = float(lineas[2-1].removeprefix("resultado: "))
                if porc_mejora_acumulada is None: #4188
                    porc_mejora_acumulada = porc_mejora
                    mejor_archivo = archivo_path
                if porc_mejora < porc_mejora_acumulada:
                    porc_mejora_acumulada = porc_mejora
                    mejor_archivo = archivo_path
                #if aptitud_acumulada is None: #3540
                #    aptitud_acumulada = aptitud_incumbente
                #    mejor_archivo = archivo_path
                #if aptitud_incumbente < aptitud_acumulada:
                #    aptitud_acumulada = aptitud_incumbente
                #    mejor_archivo = archivo_path
    
    if mejor_archivo is None:
        return None, None
    
    parametros = dict()
    with open(mejor_archivo,"r") as archivo:
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

def task_array_to_dataframe(
        array : np.ndarray
    ) -> pd.DataFrame:
    
    datos = Datos()
    
    machines_dict = datos.machines_id
    
    df = pd.DataFrame(
        columns=["Maquina", "Start", "End","Producto","Demanda","task_mode","paso"]
    )
    
    for maquina, num_maq in machines_dict.items():
        for periodo in range(len(datos.periodos)):
            
            valor : str = array[num_maq, periodo]
            
            if valor == "":
                continue
            
            producto, demanda, task_mode, intervalo, paso = str_a_task_mode(
                valor
            )
            
            demanda = str(demanda)
            paso = str(paso)
            
            fila = df.loc[
                (df["Maquina"] == maquina) &
                (df["Producto"] == producto) &
                (df["Demanda"] == demanda) &
                (df["task_mode"] == task_mode) &
                (df["paso"] == paso)
            ].copy()
            
            if fila.empty:
                #vacia
                df.loc[len(df)] = [
                    maquina
                    , periodo
                    , periodo
                    , producto
                    , demanda
                    , task_mode
                    , paso
                ]
                
            else:
                #tiene datos
                valor = fila["End"] + 1
                df.loc[fila.index, "End"] = valor
    
    df["End"] = df["End"] + 1
    df["Start"] = df["Start"] + 1
    df["delta"] = df["End"] - df["Start"]
    df["Activity"] = df[["Maquina","Producto","Demanda","task_mode","paso"]].agg('|'.join, axis=1)
    
    return df

def dataframe_to_array(
        df : pd.DataFrame
        , dict_maquinas : dict[str, int]
        , periodos : int
    ) -> np.ndarray[tuple[int, int], str]:
    
    if periodos <= 0:
        raise ValueError("Cantidad de periodos no válida")
    
    if not set(["Maquina", "Start","Producto","Demanda","task_mode","paso"]).issubset(df.columns):
        raise ValueError('Las columnas de df deben ser: ["Maquina", "Start","Producto","Demanda","task_mode","paso"]')
    
    datos = Datos()
    
    array = np.full(
        shape = (len(dict_maquinas.keys()), periodos),
        fill_value = "",
        dtype = 'object'
    )
    
    for idx, row in df.iterrows():
        maquina = row["Maquina"]
        periodo = row["Start"] - 1
        producto = row["Producto"]
        demanda = row["Demanda"]
        task_mode = row["task_mode"]
        paso = row["paso"]
        
        intervalos = datos.intervalos(task_mode=task_mode)
        
        for i in range(len(intervalos)):
            valor = task_mode_a_str(
                producto=producto
                , demanda=demanda
                , task_mode=task_mode
                , intervalo=i
                , paso=paso
            )
            
            array[dict_maquinas[maquina], periodo + i] = valor
    return array

def grafica_gantt_plt(
        df : pd.DataFrame
        , time_leaps : list[int]
        , min_value_x : int
        , max_value_x : int
        , costo_energia : float = None
        , makespan : int = None
        , save_path : str = None
        , kwargs_fig : dict = None
        , mostrar_maquinas : list[str] = None
        , subtitulo : str = "Etiqueta: Maquina|Producto|Demanda|task_mode|paso"
        , mostrar_leyenda : bool = True
        , size_horizontal : int = 16
        , size_vertical : int = 8
        , kwargs_suptitle : dict = None
        , kwargs_subtitle : dict = None
        , kwargs_label : dict = None
        , kwargs_ticks : dict = None
        , titulo : str = "Gráfica Gantt de tasks"
    ):

    fig, ax = plt.subplots(
        figsize=(size_horizontal, size_vertical), layout='tight'
    )
    
    task_modes = df["task_mode"].unique()
    
    if mostrar_maquinas is None:
        mostrar_maquinas : list[str] = df["Maquina"].unique().tolist()
        
    # color map para los task mode
    color_dict = {
        #MAQ118
        "Ironing TM4" : CUSTOM_COLOR_MAP(0)
        , "Harden[2] TM1" : CUSTOM_COLOR_MAP(1)
        , "Harden[1.5] TM3" : CUSTOM_COLOR_MAP(2)
        , "Harden[0.5] TM4" : CUSTOM_COLOR_MAP(3)
        , "Harden[1] TM5" : CUSTOM_COLOR_MAP(4)
        #MAQ119
        , "Harden[1] TM1" : CUSTOM_COLOR_MAP(5)
        , "Ironing TM3" : CUSTOM_COLOR_MAP(6)
        , "Harden[0.5] TM1" : CUSTOM_COLOR_MAP(7)
        , "Harden[1.5] TM1" : CUSTOM_COLOR_MAP(8)
        #MAQ120
        ,"Ironing TM1" : CUSTOM_COLOR_MAP(10)
        ,"Anti-Shrinkage TM2" : CUSTOM_COLOR_MAP(12)
        ,"Sublimation TM3" : CUSTOM_COLOR_MAP(14)
    }
    
    # Plot each task as a horizontal bar
    bars = []
    activities = []
    for _, row in df.iterrows():
        start = row['Start']
        duration = row["delta"]
        machine = row["Maquina"]
        if machine not in mostrar_maquinas:
            continue
        
        color = color_dict.get(row["task_mode"], "gray")
        bar = ax.barh(machine
            , duration, left=start, height=0.5, color=color
            , edgecolor="white", linewidth=0.1
        )
        bars.append(bar[0])
        activities.append(row["Activity"])

    # Linea vertical para cada time leap
    for tl in time_leaps:
        ax.axvline(x = tl, color="k", linestyle=":")

    # Leyenda para los task mode
    if mostrar_leyenda:
        legend_handles = [
            Patch(color=color_dict[mode], label=str(mode)) for mode in task_modes
        ]
        legend = ax.legend(
            handles=legend_handles
            , title="task_mode"
            , loc = "center left"
            , bbox_to_anchor=(1, 0.5)
        )
        legend.set_zorder(2.5)
    
    # custom labels
    if kwargs_label is None:
        kwargs_label = dict()
    if kwargs_ticks is None:
        kwargs_ticks = dict()
    ax.set_xlabel("Periodo", **kwargs_label)
    ax.set_xticks(ticks=time_leaps)
    
    plt.xticks(**kwargs_ticks)
    plt.yticks(**kwargs_ticks)
    
    ax.set_xlim(
        left=min_value_x
        ,right=max_value_x
    )
    ax.set_ylabel("Máquina", **kwargs_label)
    
    if kwargs_suptitle is None:
        kwargs_suptitle = dict()
    fig.suptitle(
        titulo , **kwargs_suptitle
    )
    #subtitulo = "Etiqueta: Maquina|Producto|Demanda|task_mode|paso"  
    
    if makespan is not None:
        subtitulo = subtitulo + f"makespan: {makespan}\n"
    
    if costo_energia is not None:
        subtitulo = subtitulo + f"Costo de energía: {costo_energia:.2f}"
    
    if subtitulo != "":
        ax.set_title(
            subtitulo
            , loc="left"
            , **kwargs_subtitle
        )
    ax.invert_yaxis() # To display tasks from top to bottom
    
    # hover information
    annot = ax.annotate(
        "", xy=(0,0), xytext=(-20,20),textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->")
    )
    annot.set_visible(False)
    
    def update_annot(bar, activity):
        x = bar.get_x() + bar.get_width()/2
        y = bar.get_y() + bar.get_height()/2
        annot.xy = (x, y)
        annot.set_text(activity)
        color = {
            0 : "#CF01FB"
            , 1:"#B57D00"
            , 2:"#009C9F"
        }
        #annot.get_bbox_patch().set_facecolor(bar.get_facecolor())
        annot.get_bbox_patch().set_facecolor(color[y])
    
    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            for bar, activity in zip(bars, activities):
                cont, _ = bar.contains(event)
                if cont:
                    update_annot(bar, activity)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
        if vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

    if save_path is not None:
        if kwargs_fig is None:
            kwargs_fig = dict()
        fig.savefig(
            fname=save_path
            , **kwargs_fig
        )
    
    plt.tight_layout()
    plt.show()

def graficas_poblaciones():
    
    df = pd.DataFrame(columns=["id","generacion_0","generacion_1","generacion_2"
        ,"generacion_3","generacion_4","generacion_5","generacion_6"
        ,"generacion_7","generacion_8","generacion_9","generacion_10"
        ,"incumbente"
    ])
    
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
        fila = dict()
        
        with open(archivo_path,"r") as archivo:
            lineas = archivo.readlines()
            
            fila["id"] = str(lineas[1-1].removeprefix("nombre: ").removesuffix("\n"))
            fila["generacion_0"] = float(lineas[22-1].removeprefix("promedio de aptitud "))
            fila["generacion_1"] = float(lineas[26-1].removeprefix("promedio de aptitud "))
            fila["generacion_2"] = float(lineas[30-1].removeprefix("promedio de aptitud "))
            fila["generacion_3"] = float(lineas[34-1].removeprefix("promedio de aptitud "))
            fila["generacion_4"] = float(lineas[38-1].removeprefix("promedio de aptitud "))
            fila["generacion_5"] = float(lineas[42-1].removeprefix("promedio de aptitud "))
            fila["generacion_6"] = float(lineas[46-1].removeprefix("promedio de aptitud "))
            fila["generacion_7"] = float(lineas[50-1].removeprefix("promedio de aptitud "))
            fila["generacion_8"] = float(lineas[54-1].removeprefix("promedio de aptitud "))
            fila["generacion_9"] = float(lineas[58-1].removeprefix("promedio de aptitud "))
            fila["generacion_10"] = float(lineas[62-1].removeprefix("promedio de aptitud "))
            fila["incumbente"] = float(lineas[2-1].removeprefix("resultado: "))
            
            df_fila = pd.DataFrame(fila, index=[0])
            
            if len(df.index) == 0:
                df = df_fila
            else:
                df : pd.DataFrame = pd.concat([df, df_fila], ignore_index=True)
    
    _, mejor_path = buscar_mejor_parametros()
    
    #grafica boxplot
    fig, ax = plt.subplots(
        figsize=(7, 6), layout='tight'
    )
    ax.set_title(
        f"Box plot mejor individuo\nde cada población revisada"
        , fontsize=18
        , fontweight='bold'
    )
    ax.boxplot(
        df["incumbente"]
        , medianprops = dict(
            color = "black"
            , linestyle = "--"
        )
    )
    ax.set_xlim(0.5,2)
    
    #mejor
    with open(mejor_path,"r") as archivo:
        lineas = archivo.readlines()
        incumbente = float(lineas[2-1].removeprefix("resultado: "))
    mejor_punto = ax.plot(1,incumbente,"or")
    legend = ax.legend(
        [mejor_punto[0]]
        , [f"Mejor individuo\ncon los\nparámetros\nseleccionados"]
        , loc="upper right", edgecolor = "black"
        , fontsize = 16
    )
    legend.get_frame().set_alpha(None)
    legend.get_frame().set_facecolor((0, 0, 0, 0))
    #plt.tight_layout()
    plt.xticks([])
    ax.set_ylabel("Mejor individuo de población", fontsize=14, fontweight='bold')
    ax.yaxis.set_tick_params(labelsize=12)
    
    plt.xticks(fontweight="bold", fontsize = 14)
    plt.yticks(fontweight="bold", fontsize = 14)
    
    fig.savefig(
        fname=os.path.join("Datos Tesina","Figuras_Tablas","7_0","boxplot.png")
        , transparent=True
    )
    plt.show()
    
    #grafica líneas
    fig, ax = plt.subplots(
        figsize=(11, 5), layout='tight'
    )

    ax.set_title(
        "Promedio de aptitud vs generación por población"
        , fontsize=22
        , fontweight='bold'
    )
    ax.set_xlabel("Generación", fontsize=16, fontweight='bold')
    ax.set_ylabel("Promedio de aptitud", fontsize=16, fontweight='bold')
    
    id_mejor = os.path.basename(mejor_path).removesuffix(".txt")
    for idx, row in df.iterrows():
        cols = [f"generacion_{i}" for i in range(11)]
        valores = row[cols].to_numpy(dtype=float)
        
        #busca mejor
        id = row["id"]
        if id == id_mejor:
            mejor_linea = ax.plot(valores, alpha=1, color="black")
        else:
            ax.plot(valores, alpha=0.02)
            
    #plt.tight_layout()
    legend = ax.legend(
        [mejor_linea[0]]
        , [f"Población seleccionada"]
        , loc="upper right", edgecolor = "black"
        , fontsize = 12
    )
    legend.get_frame().set_alpha(None)
    legend.get_frame().set_facecolor((0, 0, 0, 0))
    plt.xticks([i for i in range(11)])
    
    plt.xticks(fontweight="bold", fontsize = 14)
    plt.yticks(fontweight="bold", fontsize = 14)
            
    fig.savefig(
        fname=os.path.join("Datos Tesina","Figuras_Tablas","7_0","lineas.png")
        , transparent=True
    )
    plt.show()

def grafica_incumbente(archivo_nombre : str):
    base_dir = os.path.join("Datos Tesina", "algoritmo genetico","Tesis")
    archivo_nombre = os.path.join(base_dir,archivo_nombre)
    
    promedio_aptitudes = []
    promedio_makespans = []
    promedio_costos = []
    
    #buscar valores
    with open(archivo_nombre,"r") as archivo:
        archivo_lineas = archivo.readlines()
        
        linea_aptitud = None
        linea_makespan = None
        linea_costo = None
        
        for index, linea in enumerate(archivo_lineas):
            revisar_linea = linea.removesuffix("\n")
            if revisar_linea == "Valores Generaciones":
                linea_aptitud = index
            if revisar_linea == "Valores Generaciones makespan":
                linea_makespan = index
            if revisar_linea == "Valores Generaciones costo":
                linea_costo = index
        
        i = 1
        while True:
            linea = archivo_lineas[linea_aptitud + i]
            if not linea.startswith("Generacion "):
                break
            if (linea_aptitud + i) > len(archivo_lineas):
                break
            
            promedio_aptitud = float(archivo_lineas[linea_aptitud + i + 2].removeprefix("promedio de aptitud ").removesuffix("\n"))
            promedio_aptitudes.append(promedio_aptitud)
            
            promedio_makespan = float(archivo_lineas[linea_makespan + i + 2].removeprefix("promedio de makespan ").removesuffix("\n"))
            promedio_makespans.append(promedio_makespan)
            
            promedio_costo = float(archivo_lineas[linea_costo + i + 2].removeprefix("promedio de costo ").removesuffix("\n"))
            promedio_costos.append(promedio_costo)
            i = i + 4
         
    #grafica linea
    fig, ax = plt.subplots(
        figsize=(14, 6), layout='tight'
    )
    x = [g for g in range(len(promedio_aptitudes))]
    
    ax.step(
        x=x
        , y=promedio_aptitudes
        , label="aptitud"
        , where="post"
        , color = "black"
    )
    
    ax.set_title(
        "Progreso de población simulada con parámetros seleccionados"
        , fontsize=22
        , fontweight='bold'
    )
    
    #ax.set_ylim(0,1400)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Generación", fontsize=18,fontweight="bold")
    ax.set_ylabel("Promedio por generación", fontsize=18,fontweight="bold")
    
    #legend = ax.legend(loc="upper right"
    #    , edgecolor = "black"
    #    , fontsize = 16
    #)
    #legend.get_frame().set_alpha(None)
    #legend.get_frame().set_facecolor((0, 0, 0, 0))
    
    plt.xticks(fontweight="bold", fontsize = 16)
    plt.yticks(fontweight="bold", fontsize = 16)
    #plt.legend(fontsize=16)
    fig.savefig(
        fname=os.path.join("Datos Tesina","Figuras_Tablas","7_0","aptitud_mejor.png")
        , transparent=True
    )
    plt.show()
  
def main():
    graficas_poblaciones()
    #grafica_incumbente("tesis_2.txt")

if __name__ == "__main__":
    main()
