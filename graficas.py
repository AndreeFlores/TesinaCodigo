import numpy as np
import pandas as pd
from Carga_Datos import Datos, str_a_task_mode
import matplotlib.pyplot as plt

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

def grafica_gantt_plt(
        df : pd.DataFrame
        , time_leaps : list[int]
    ):

    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Define a color map for task_mode values
    task_modes = df["task_mode"].unique()
    colors = plt.cm.get_cmap("tab10", len(task_modes))
    color_dict = {mode: colors(i) for i, mode in enumerate(task_modes)}
    
    # Plot each task as a horizontal bar
    for index, row in df.iterrows():
        start = row['Start']
        end = row['End']
        duration = row["delta"]
        machine = row["Maquina"]
        color = color_dict.get(row["task_mode"], "gray")
        ax.barh(machine, duration, left=start, height=0.5, color=color)

    # Plot each time leap
    for tl in time_leaps:
        ax.axvline(x = tl, color="k", linestyle=":")

    # Customize the plot
    ax.set_xlabel("Periodo")
    ax.set_ylabel("Máquina")
    ax.set_title("Gantt Chart with Integer X-axis")
    ax.invert_yaxis() # To display tasks from top to bottom
    
    #ax.grid(True, linestyle='--', alpha=0.7)

    plt.show()