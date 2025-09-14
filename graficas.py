import plotly.figure_factory as ff
import plotly.express as px
import numpy as np
import pandas as pd
from Carga_Datos import Datos, str_a_task_mode

def task_array_to_dataframe(
        array : np.ndarray
    ) -> pd.DataFrame:
    
    datos = Datos()
    
    machines_dict = datos.machines_id
    
    df = pd.DataFrame(
        columns=["Maquina", "Start", "End","Producto","Demanda","task_mode"]
    )
    
    for maquina, num_maq in machines_dict.items():
        for periodo in range(len(datos.periodos)):
            
            valor : str = array[num_maq, periodo]
            
            if valor == "":
                continue
            
            producto, demanda, task_mode, intervalo = str_a_task_mode(
                valor
            )
            
            fila = df.loc[
                (df["Maquina"] == maquina) &
                (df["Producto"] == producto) &
                (df["Demanda"] == demanda) &
                (df["task_mode"] == task_mode)
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
                ]
            else:
                #tiene datos
                valor = fila["End"] + 1
                df.loc[fila.index, "End"] = valor
    
    df["Delta"] = df["End"] - df["Start"]
    df["Activity"] = df[["Maquina","Producto","Demanda","task_mode"]].agg('|'.join, axis=1)
    
    return df
    
