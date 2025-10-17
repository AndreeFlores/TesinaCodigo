import numpy as np
import pandas as pd
from Carga_Datos import Datos, str_a_task_mode, task_mode_a_str
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

CUSTOM_COLOR_MAP = ListedColormap(
    [
        "#CF01FB", "#B100D7", "#9400B4", "#770092", "#5B0070",
        "#B57D00", "#9A6A00", "#815700", "#674500", "#4F3400",
        "#009C9F", "#008588", "#006F71", "#00595A", "#004344"
    ]
)

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
    ):

    fig, ax = plt.subplots(
        figsize=(16, 8), layout='tight'
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
    ax.set_xlabel("Periodo")
    ax.set_xticks(ticks=time_leaps)
    ax.set_xlim(
        left=min_value_x
        ,right=max_value_x
    )
    
    ax.set_ylabel("Máquina")
    fig.suptitle(
        "Gráfica Gantt de tasks"
    )
    #subtitulo = "Etiqueta: Maquina|Producto|Demanda|task_mode|paso"  
    
    if makespan is not None:
        subtitulo = subtitulo + f"\nmakespan: {makespan}"
    
    if costo_energia is not None:
        subtitulo = subtitulo + f"\nCosto de energía: {costo_energia:.2f}"
    
    if subtitulo != "":
        ax.set_title(
            subtitulo
            , loc="left"
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
