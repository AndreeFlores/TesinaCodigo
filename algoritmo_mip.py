from Carga_Datos import Datos, PATH_INPUT
import numpy as np
import glob
from pathlib import Path
import os
from datetime import datetime
import time

import pandas as pd
import gurobipy as gp
import gurobipy_pandas as gppd

class ModeloMIPCallback:
    
    def __init__(self
            , path_base : str
            , tiempo_checkpoint_segundos : float = 3600 
        ):
        self.objetivo_previo = None
        self.path_base = path_base
        self.tiempo_checkpoint = tiempo_checkpoint_segundos
        self.runtime_start = None
        
        self.file_model = os.path.join(self.path_base, "model.lp")
        
        self.se_encontro_mejor = False
    
    def _timestamp() -> str:
        return datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    def _timestr() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _filename_sol(self) -> str:
        """Genera el nombre para un archivo .sol"""
        ts = self._timestamp()
        sol_file = os.path.join(self.path_base, f"sol_{ts}.sol")
        
        return sol_file
    
    def _save_model_file(self, model):
        """Guarda el archivo con el modelo"""
        try:
            model.write(self.file_model)
            print(f"[Callback][{self._timestr()}] Modelo guardado")
        except Exception as e:
            print(f"[Callback][{self._timestr()}] Error guardando modelo: {e}")
    
    def _save_sol_file(self, model):
        """Guarda el archivo con la solucion"""
        if model.SolCount <= 0:
            print(f"[Callback][{self._timestr()}] No hay solución para guardar")
            return None
        sol_file = self._filename_sol()
        try:
            model.write(sol_file)
            print(f"[Callback][{self._timestr()}] Solución guardada")
            return sol_file
        except Exception as e:
            print(f"[Callback][{self._timestr()}] Error guardando solución: {e}")
            return None
    
    def latest_checkpoint(self):
        """Devuelve el checkpoint mas reciente"""
        sol_files = sorted(glob.glob(
            os.path.join(self.path_base, "sol_*.sol")
        ))
        latest_sol = sol_files[-1] if sol_files else None
        return latest_sol
    
    def load_solution(self, model, solfile):
        """Si existe solfile, leerla y cargarla en el modelo."""
        if solfile is None or not os.path.exists(solfile):
            print(f"[Callback][{self._timestr()}] No se encontró un archivo .sol guardado")
            return False
        try:
            model.read(solfile)
            print(f"[Callback][{self._timestr()}] Archivo .sol cargado")
            return True
        except Exception as e:
            print(f"[Callback][{self._timestr()}] Error cargando .sol: {e}")
            return False
    
    def __call__(self, model, where):
        
        #guardar modelo si no existe archivo
        if not os.path.exists(self.file_model):
            try:
                model.write(self.file_model)
                print(f"[Callback][{self._timestr()}] Modelo inicial guardado en {self.file_model}")
            except Exception as e:
                print(f"[Callback][{self._timestr()}] Error guardando modelo inicial: {e}")
        
        # inicializar tiempo de inicio de la sesión la primera vez
        if self.runtime_start is None:
            try:
                self.runtime_start = model.cbGet(gp.GRB.Callback.RUNTIME)
            except Exception:
                self.runtime_start = 0.0
        
        # al encontrar una solucion mejor
        if where == gp.GRB.Callback.MIPSOL:
            #imprime el progeso de la solucion
            #obtener el nuevo valor del objetivo
            valor_objetivo = model.cbGet(gp.GRB.callback.MIPSOL_OBJ)
            
            #imprimir valor incumbente
            if self.objetivo_previo is None:
                print(f"[Callback][{self._timestr()}] Solución encontrada, con un objetivo igual a {valor_objetivo}")
            else:
                mejora = self.objetivo_previo - valor_objetivo
                print(f"[Callback][{self._timestr()}] Nueva solucion encontrada, con un objetivo igual a {valor_objetivo}, mejora de {mejora}")
            
            self.objetivo_previo = valor_objetivo
            self.se_encontro_mejor = True
            #guardar solucion
            try:
                self._save_sol_file()
            except Exception as e:
                print(f"[Callback][{self._timestr()}] Error guardando checkpoint: {e}")
        
        # comprobar tiempo de sesión
        if where in (gp.GRB.Callback.MIP, 
                gp.GRB.Callback.MIPNODE, gp.GRB.Callback.MIPSOL
            ):
            try:
                runtime = model.cbGet(gp.GRB.Callback.RUNTIME)
            except Exception:
                runtime = None
            
            if runtime is not None:
                diferencia = runtime - (0.0 if self.runtime_start is None else self.runtime_start)
            
                if diferencia >= self.tiempo_checkpoint:
                    #guardar solucion si existe
                    try:
                        if model.SolCount > 0:
                            self._save_sol_file()
                    except Exception as e:
                        print(f"[Callback][{self._timestr()}] Error guardando checkpoint: {e}")
                    model.terminate() #terminar la busqueda de la solucion
                    
class ModeloMIP:
    
    def __init__(self):
        self.path_base = os.path.join("Datos Tesina", "algoritmos mip")
        if not os.path.exists(self.path_base):
            os.makedirs(self.path_base, exist_ok=True)
        
        self.path_log = os.path.join(self.path_base,"mip_schedule.txt") #ubicacion del log
        
        self.modelo = gp.Model("MIP_Scheduling")
        self.datos = Datos(path = PATH_INPUT)
        
        self.modelo.setParam("LogFile", self.path_log)
        self.modelo.setParam("Threads",4) #numero de threads a utilizar
        self.modelo.setParam("NodefileStart",0.5) #durante la busqueda si se supera esta cantidad de GB en la memoria se guarda en un archivo
        self.modelo.setParam("PreSparsify",1) #Modo de reduccion del presolve del modelo
        
        self.modelo.setParam("MIPFocus",1) #estrategia para la busqueda de la solucion
        
        self.modelo.setParam("Seed",0) #random seed
        
        #crear variables
        self.crear_variables()
        
        #crear objetivos
        self.crear_objetivos()
        
        #crear restricciones
        self.crear_restriccion_makespan()
        self.crear_restriccion_energia_utilizada()
        self.crear_restriccion_flujo_produccion()
        self.crear_restriccion_maquina()
        self.crear_restriccion_deadline()
        self.crear_restriccion_mismo_turno()
           
    def crear_variables(self):
        """
        crear_variables - 
        
        Crea las variables del modelo
        """
        
        lista_df = []
        
        cambio_turnos : list[int] = self.datos.time['time_leap'] #ejemplo: [192,384,576,768,960]
        cambio_turnos.append(max(self.datos.periodos))
        
        cambio_turnos_np = np.array(cambio_turnos)
        
        for producto, demanda, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            energia_requerida =  self.datos.energia_task_intervalo(
                task=task, task_mode=task_mode, intervalo=intervalo
            )
            intervalo_maximo = len(self.datos.intervalos(task_mode=task_mode)) - 1
            
            for periodo in self.datos.periodos:
                
                siguiente_cambio_idx = np.argwhere(periodo <= cambio_turnos_np).min()
                siguiente_cambio = cambio_turnos_np[siguiente_cambio_idx]
                
                periodo_final = periodo + intervalo
                
                lista_df.append({
                    "Producto" : producto
                    , "Demanda" : demanda
                    , "Paso" : paso
                    , "Task" : task
                    , "Maquina" : maquina
                    , "Task_Mode" : task_mode
                    , "Intervalo" : intervalo
                    , "Periodo" : periodo - 1
                    , "Energia_Requerida" : energia_requerida
                    , "Periodo_Valor" : periodo
                    , "Es_Intervalo_Inicial" : False if intervalo > 0 else True
                    , "Es_Intervalo_Final" : True if intervalo == intervalo_maximo else False
                    , "Es_Viable_Periodo_Final" : True if (periodo < siguiente_cambio) and (periodo_final < siguiente_cambio) else False
                })
        
        self.variables_df = pd.DataFrame(data=lista_df).set_index([
            "Producto", "Demanda", "Paso", "Task", "Maquina", "Task_Mode", "Intervalo", "Periodo"
        ])
        
        self.variables_df["Hay_Produccion"] = gppd.add_vars(self.modelo, self.variables_df, name="Prod", vtype=gp.GRB.BINARY)
        
        self.variables_makespan = self.modelo.addVar(
            lb = 1
            , ub = max(self.datos.periodos)
            , vtype = gp.GRB.INTEGER
            , name = f"Makespan"
        )
        
        self.variables_socket = self.modelo.addMVar(
            shape =(max(self.datos.periodos))
            , ub= gp.GRB.INFINITY
            , vtype = gp.GRB.CONTINUOUS
            , name ="Energia_Socket"
        )
        
        self.variables_solar = self.modelo.addMVar(
            shape =(max(self.datos.periodos))
            , lb=0
            , ub= self.datos.solar_amount
            , vtype = gp.GRB.CONTINUOUS
            , name ="Energia_Solar"
        )
        
    def crear_objetivos(self
            , weight_makespan : float = 1
            , weight_energy : float = 1
            , sense = gp.GRB.MINIMIZE
        ) :
        """
        crear_objetivos - 
        
        Crea los objetivos del problema
        - Makespan : tiempo total utilizado
        - Costo de Energia : suma del costo de la energia de enchufe
        
        Parameters
        ----------
        weight_makespan (float, optional, defaults to 1) :
            El peso del objetivo de makespan
        
        weight_energy (float, optional, defaults to 1) :
            El peso del objetivo del costo de energia
        
        sense (int, optional, defaults to gp.GRB.MINIMIZE) :
            Si minimizar o maximizar los objetivos
        """
        
        #Makespan ecuacion 9
        self.modelo.setObjectiveN(
            expr = self.variables_makespan
            , index = 0
            , weight = weight_makespan
            , name = f"Makespan_objetivo"
        )
        
        #Energy ecuacion 10
        expresion = (self.variables_socket @ self.datos.socket_price)
        self.modelo.setObjectiveN(
            expr = expresion
            , index=1
            , weight= weight_energy
            , name = f"Costo_de_Energia_objetivo"
        )
        
        self.modelo.ModelSense = sense
    
    def crear_restriccion_makespan(self):
        """
        crear_restriccion_makespan - 
        
        Crea las restricciones que limitan el valor del makespan
        """
        #makespan ecuacion 12
        self.restriccion_makespan = gppd.add_constrs(
            self.modelo
            , self.variables_df["Hay_Produccion"] * self.variables_df["Periodo_Valor"]
            , gp.GRB.LESS_EQUAL
            , self.variables_makespan
            , name="restriccion_makespan"
        )
    
    def crear_restriccion_energia_utilizada(self):
        """
        crear_restriccion_energia_utilizada - 
        
        Crea las restricciones con el uso de energia
        """
        #restriccion ecuacion 13
        series_linexp_energia_utilizada = self.variables_df.assign(
            Energia_Utilizada = self.variables_df["Energia_Requerida"] * self.variables_df["Hay_Produccion"]
        ).groupby(["Periodo"]).sum()["Energia_Utilizada"]
        
        energia_disponible = self.variables_solar + self.variables_socket
        
        if series_linexp_energia_utilizada.shape != energia_disponible.shape:
            raise ValueError("Error en el tamaño de las matrices de expresiones de energia")

        for i in range(energia_disponible.shape[0]):
            self.modelo.addConstr(
                series_linexp_energia_utilizada.iloc[i] == energia_disponible[i]
                , name=f"Restriccion_energia_utilizada[{i}]"
            )
    
    def crear_restriccion_flujo_produccion(self):
        """
        crear_restriccion_flujo_produccion - 
        
        Crea las restricciones relacionadas con el flujo de la produccion
        """
        
        #restriccion ecuacion 14
        self.restriccion_flujo_primer_intervalo = gppd.add_constrs(
            self.modelo
            , self.variables_df.xs(0, level="Intervalo").groupby(["Producto","Demanda","Paso"]).sum()["Hay_Produccion"]
            , gp.GRB.EQUAL
            , 1
            , name="Solo_un_intervalo_inicial"
        )
    
        #restriccion ecuacion 15
        df_agrupado = self.variables_df.loc[(self.variables_df["Es_Intervalo_Inicial"]) | (self.variables_df["Es_Intervalo_Final"])].assign(
            Periodo_Procesado = self.variables_df["Hay_Produccion"] * self.variables_df["Periodo_Valor"]
        ).groupby(["Producto","Demanda","Paso","Intervalo"]).sum()
        
        df_agrupado.reset_index(level="Intervalo", inplace=True)
        
        df_agrupado["Intervalo"] = df_agrupado["Intervalo"].case_when(
            [(df_agrupado["Intervalo"] == 0, "Inicio"), (df_agrupado["Intervalo"] != 0, "Termina")],
        )
        
        df_agrupado = df_agrupado[["Periodo_Procesado","Intervalo"]]
        
        df_agrupado = df_agrupado.pivot_table(
            index=["Producto", "Demanda", "Paso"],
            columns="Intervalo",
            values="Periodo_Procesado",
            aggfunc="sum"
        )
        df_agrupado_shift = df_agrupado.groupby(level=["Producto", "Demanda"]).shift(1).dropna(axis=0, how="any")
        
        df_agrupado = df_agrupado.merge(df_agrupado_shift, how="inner", left_index=True, right_index=True, suffixes=('','_anterior'))
        del df_agrupado_shift
        self.restriccion_flujo_pasos = gppd.add_constrs(
            self.modelo
            , df_agrupado["Termina_anterior"] + 1
            , gp.GRB.LESS_EQUAL
            , df_agrupado["Inicio"]
            , name="Flujo_de_produccion"
        )
        del df_agrupado
        
        #restriccion ecuacion 16
        df_agrupado = self.variables_df.assign(
            Periodo_Procesado = self.variables_df["Hay_Produccion"] * self.variables_df["Periodo_Valor"]
        ).groupby(["Producto", "Demanda", "Paso", "Task", "Maquina", "Task_Mode", "Intervalo"]).sum()[["Periodo_Procesado","Hay_Produccion"]]
        
        df_agrupado_intervalo_cero = df_agrupado.xs(key=0, level="Intervalo")["Hay_Produccion"]
        
        df_agrupado_shift = df_agrupado.groupby(level=["Producto", "Demanda", "Paso", "Task", "Maquina", "Task_Mode"]).shift(1).dropna(axis=0, how="any")
        df_agrupado = df_agrupado.merge(df_agrupado_shift, how="inner", left_index=True, right_index=True, suffixes=('','_anterior'))
        
        df_agrupado.join(df_agrupado_intervalo_cero, on=["Producto", "Demanda", "Paso", "Task", "Maquina", "Task_Mode"], rsuffix="_rhs")
        
        self.restriccion_flujo_activacion = gppd.add_constrs(
            self.modelo
            , (df_agrupado["Periodo_Procesado"] - df_agrupado["Periodo_Procesado_anterior"])
            , gp.GRB.EQUAL
            , df_agrupado["Hay_Produccion_anterior"]
            , name="Activacion_intervalos"
        )
    
    def crear_restriccion_maquina(self):
        """
        restriccion_maquina - 
        
        Crea las restricciones para limitar el uso de las maquinas a una sola actividad por periodo
        """
        
        #restriccion ecuacion 17
        self.restriccion_maquina = gppd.add_constrs(
            self.modelo
            , self.variables_df.groupby(["Maquina","Periodo"]).sum()["Hay_Produccion"]
            , gp.GRB.LESS_EQUAL
            , 1
            , name="Restriccion_uso_maquina"
        )
    
    def crear_restriccion_deadline(self):
        """
        crear_restriccion_deadline - 
        
        Crear la restruccion del deadline para cada producto-demanda
        """
        
        #restriccion ecuacion 18
        for producto, demanda, periodo_limite in self.datos.iterar_deadlines():
            df_filtrado = self.variables_df.loc[(producto,demanda,slice(None),slice(None),slice(None),slice(None),slice(None),slice(None)),:]
            
            gppd.add_constrs(
                self.modelo
                , (df_filtrado["Hay_Produccion"] * df_filtrado["Periodo_Valor"])
                , gp.GRB.LESS_EQUAL
                , periodo_limite
                , name="Deadline"
            )
    
    def crear_restriccion_mismo_turno(self):
        """
        crear_restriccion_mismo_turno - 
        
        Crea las restricciones relacionadas para que la actividad se realice completamente en un turno
        """
        
        #restriccion ecuacion 19
        self.restriccion_turno =  gppd.add_constrs(
            self.modelo
            , self.variables_df.loc[self.variables_df["Es_Viable_Periodo_Final"]]["Hay_Produccion"]
            , gp.GRB.EQUAL
            , 0
            , name="Es_Valido_Mismo_Turno"
        )
    
    def optimizar(self):
        """
        optimizar - 
        
        Se optimiza el modelo.
        
        Realiza checkpoints
        """
        
        try:
            self.modelo = gp.read(os.path.join(self.path_base, "model.lp"))
            print("Ya existe un archivo model.lp cargando modelo")
        except Exception as e:
            print(f"No se pudo leer archivo model.lp causa: {e}")
        
        while True:
            #Optimizacion finalizada
            status = self.modelo.Status
            if status in (gp.GRB.OPTIMAL
                    , gp.GRB.INFEASIBLE
                    , gp.GRB.UNBOUNDED
                    , gp.GRB.INF_OR_UNBD
                ):
                print("Optimización finalizada con estado:", status)
                break

            #Empezando la optimizacion
            print("Empezando optimizacion")
            callback = ModeloMIPCallback(
                path_base=self.path_base
                , tiempo_checkpoint_segundos= 3600
            )
            self.modelo.optimize(callback)

            #Optimización interrumpida por callback
            print("Optimización finalizada")
            time.sleep(1)
            
            #para alterar la busqueda
            self.modelo.setParam("Seed"
                , np.random.random_integers(0,2**30-1
            ))
    
    def guardar_variables(self):
        """
        guardar_variables - 
        
        Guarda las variables con su valores del modelo
        """
        
        datos_variables = [
            (v.varName, v.X) for v in self.modelo.getVars()
        ]
        
        df = pd.DataFrame(datos_variables, columns=['Variable', 'Value'])
        df.to_csv(os.path.join(self.path_base,"variables.csv"), index=False)
        
def main():
    ml = ModeloMIP()
    
    ml.optimizar()
    
    if ml.modelo.SolCount > 0:
        print("Objetivo final:", ml.modelo.ObjVal)
        ml.guardar_variables()
        print("Variables guardadas")
    
if __name__ == "__main__":
    main()

