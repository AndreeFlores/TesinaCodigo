from Carga_Datos import Datos, PATH_INPUT
import gurobipy as gp
import numpy as np
import time
from pathlib import Path
import os

class ModeloLineal:
    
    def __init__(self, delta = 0.0001):
        
        self.modelo = gp.Model("Scheduling")
        
        self.datos = Datos(path = PATH_INPUT)
        
        self.delta = delta #un numero pequeño
        
        #inicializar variables
        self.variables = dict()
        
        #tiempo total de produccion
        self.variables["Makespan"] = self.modelo.addVar(
            lb = 1
            , ub = max(self.datos.periodos)
            , vtype = gp.GRB.INTEGER
            , name = f"Makespan"
        )
        
        #variables de energia
        self.variables["Energy"] = dict()
        for periodo in self.datos.periodos:
            datos_energia_periodo = self.datos.energia_periodo(periodo)
            
            self.variables["Energy"][periodo] = {
                "Solar" : self.modelo.addVar(
                    lb = 0
                    , ub = datos_energia_periodo["Solar"]["amount"]
                    , vtype = gp.GRB.CONTINUOUS
                    , name = f"Amount_of_solar_energy_in_t_=_{periodo}"
                )
                , "Socket" : self.modelo.addVar(
                    lb = 0
                    , vtype = gp.GRB.CONTINUOUS
                    , name = f"Amount_of_socket_energy_in_t_=_{periodo}"
                )
            }
        
        #variables binarias de produccion
        self.variables["Production"] = dict()
        #self.variables["Proximidad"] = dict()
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            
            if producto not in self.variables["Production"]:
                self.variables["Production"][producto] = dict()
                
            if num not in self.variables["Production"][producto]:
                self.variables["Production"][producto][num] = dict()
            
            if paso not in self.variables["Production"][producto][num]:
                self.variables["Production"][producto][num][paso] = dict()
            
            if task not in self.variables["Production"][producto][num][paso]:
                self.variables["Production"][producto][num][paso][task] = dict()
            
            if task_mode not in self.variables["Production"][producto][num][paso][task]:
                self.variables["Production"][producto][num][paso][task][task_mode] = dict()
            
            if maquina not in self.variables["Production"][producto][num][paso][task][task_mode]:
                self.variables["Production"][producto][num][paso][task][task_mode][maquina] = dict()
            
            if intervalo not in self.variables["Production"][producto][num][paso][task][task_mode][maquina]:
                self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo] = dict()

            for periodo in self.datos.periodos:
                
                self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo] = self.modelo.addVar(
                    vtype = gp.GRB.BINARY
                    , name =f"Production_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}][{periodo}]".replace(" ","_")
                )
    
        ###resultado:
        i = 0
        self.maquinas : dict[str,int] = dict()
        for maq in list(self.datos.machines.keys()):
            self.maquinas[maq] = i
            i += 1
        self.array_schedule = np.full(
            shape = (len(self.maquinas.keys()), len(self.datos.periodos))
            , fill_value = ""
        )
    
    #listo
    def crear_objetivos(self
            , weight_makespan : float = 1
            , weight_energy : float = 1
            , sense = gp.GRB.MINIMIZE
        ):
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
        
        #Makespan
        self.modelo.setObjectiveN(
            expr = self.variables["Makespan"]
            , index = 0
            , weight = weight_makespan
            , name = f"Periodo_final"
        )
        
        #Energy
        expresion = gp.LinExpr()
        for periodo in self.datos.periodos:
            precio = self.datos.energia_periodo(periodo)
            
            expresion.addTerms(precio['Socket Energy']['price']
                , self.variables["Energy"][periodo]["Socket"]
            )
        
        self.modelo.setObjectiveN(
            expr = expresion
            , index = 1
            , weight = weight_energy
            , name = f"Costo_de_Energia"
        )
        
        self.modelo.ModelSense = sense

    #listo ecuacion 13
    def restriccion_Makespan(self):
        """
        restriccion_Makespan - 
        
        Crea la restriccion de Makespan (tiempo total de produccion)
        """
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            for periodo in self.datos.periodos:
        
                self.modelo.addConstr(
                    periodo * self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo] <= self.variables["Makespan"]
                    , name = f"Makespan_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}][{periodo}]".replace(" ","_")
                )
    
    #listo ecuacion 14
    def restriccion_Energia(self):
        """
        restriccion_Energia - 
        
        Crea la condicción que la suma de energia por periodo sea igual a la suma de energia utilizada.
        
        Esto es para que en la funcion objetivo de minimizar el costo de energia
        no se considere la energia solar que es "gratis" (gasto variable = 0). 
        """
        
        for periodo in self.datos.periodos:
            
            expresion = gp.LinExpr()
            
            for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
                
                expresion.add(
                    self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                    , self.datos.energia_task_intervalo(task=task, task_mode=task_mode, intervalo=intervalo)
                )
                
            self.modelo.addConstr(
                self.variables["Energy"][periodo]["Solar"] + self.variables["Energy"][periodo]["Socket"] == expresion
                , name = f"Uso_de_Energia_{periodo}"
            )
    
    #listo ecuacion 20
    def restriccion_CambioTurno(self):
        """
        restriccion_CambioTurno - 
        
        Agrega las restricciones para evitar que suceda un cambio de turno
        mientras que se realizan los trabajos.
        """
        
        cambio_turnos : list[int] = self.datos.time['time_leap'] #ejemplo: [192,384,576,768,960]

        #obtener todas los primeros intervalos posibles        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():

            #aunque es posible realizar esta restriccion con los siguientes invervalos
            #del task_mode, solo se revisa el primero
            if intervalo != 0:
                continue
            
            cant_intervalos = len(self.datos.intervalos(task_mode=task_mode))
            
            for cambio in cambio_turnos:
                #"Harden[1] TM2" -> range(5 - 1) = [0,1,2,3]
                # si t = 192 -> [192 - 0, 192 - 1, 192 - 2, 192 - 3] = [192,191,190,189]
                
                # el -1 en range(cant_intervalos - 1) es necesario para no considerar el caso
                # donde el task_mode termina justo antes del cambio del turno
                for i in range(cant_intervalos - 1): 
                    periodo : int = cambio - i
                    
                    self.variables["Production"][producto][num] \
                        [paso][task][task_mode][maquina][intervalo][periodo].lb = 0
                        
                    self.variables["Production"][producto][num] \
                        [paso][task][task_mode][maquina][intervalo][periodo].ub = 0

    #listo ecuacion 15
    def restriccion_produccion(self):
        """
        restriccion_produccion - 
        
        Crea las restricciones que limita un solo task_mode para cada paso de produccion.
        """
        
        periodos = self.datos.periodos
        diccionario_pasos = dict()
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            
            prod_num_paso = (producto, num, paso)
            if prod_num_paso not in diccionario_pasos:
                diccionario_pasos[prod_num_paso] = gp.LinExpr()
            
            if intervalo != 0:
                continue
            
            for periodo in periodos:
                diccionario_pasos[prod_num_paso].add(
                    self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                )
        
        for key in diccionario_pasos.keys():
            producto, num, paso = key
            
            self.modelo.addConstr(
                diccionario_pasos[key] == 1
                , name=f"Inicio_Paso_[{producto}][{num}][{paso}]".replace(" ","_")
            )
                
    #ecuacion 16
    def restriccion_recetas_2(self):
        """
        restriccion_recetas_2 - 
        
        Crea las restricciones que limita los periodos entre distintos pasos del producto-demanda
        """
        
        periodos = self.datos.periodos
        diccionario_receta = dict()
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            
            prod_num_paso = (producto, num, paso)
            if prod_num_paso not in diccionario_receta:
                diccionario_receta[prod_num_paso] = dict()
                diccionario_receta[prod_num_paso]["Inicio"] = gp.LinExpr()
                diccionario_receta[prod_num_paso]["Final"] = gp.LinExpr()

            if intervalo == 0:
                for periodo in periodos:
                    diccionario_receta[prod_num_paso]["Inicio"].add(
                        self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                        , periodo
                    )

            cantidad_intervalos = len(self.datos.intervalos(task_mode=task_mode))-1
            if intervalo == cantidad_intervalos:
                for periodo in periodos:
                    diccionario_receta[prod_num_paso]["Final"].add(
                        self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                        , periodo
                    )
        
        for prod_num_paso in diccionario_receta.keys():
            producto, num, paso = prod_num_paso
            if paso == 0:
                continue
            
            self.modelo.addConstr(
                diccionario_receta[(producto,num,paso-1)]["Final"] + 1 <= diccionario_receta[(producto,num,paso)]["Inicio"]
                , name=f"Paso_receta_[{producto}][{num}][{paso}]".replace(" ","_")
            )
                
    #revisar (version anterior)
    def restriccion_Production(self):
        """
        restriccion_Production - 
        
        Crea las restricciones que limitan a lo maximo 1
        un intervalo del task_mode entre todas los periodos
        
        Las 3 restricciones 
        * `restriccion_maquinas`
        * `restriccion_Production`
        * `restriccion_intervalos`
        limitan los intervalos a cuales periodos pueden ser asignados
        """
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            expresion = gp.LinExpr()
            
            for periodo in self.datos.periodos:
                expresion.add(
                    self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                )
            
            self.modelo.addConstr(
                expresion <= 1
                , name = f"Production_intervalo_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]".replace(" ","_")
            )

    #revisar (version anterior)
    def restriccion_Recetas(self):
        """
        restriccion_Recetas - 
        
        Crea las restricciones que controla el flujo de produccion
        para los productos
        """
        
        periodos = self.datos.periodos
        
        for producto, num in self.datos.iterar_productos():
            receta = self.datos.receta_producto(producto=producto)
            
            for paso in range(len(receta)):
                binario_actual = gp.LinExpr()
                #binario_anterior = gp.LinExpr()
                periodo_actual = gp.LinExpr()
                periodo_anterior = gp.LinExpr()
                
                if paso == 0:
                    #periodo actual
                    task_actual, dict_task_modes_actual , _= receta[paso]
                    
                    for task_mode, maquinas in dict_task_modes_actual.items():
                        for maquina in maquinas:
                            for periodo in periodos:
                                binario_actual.add(
                                    self.variables["Production"][producto][num][paso][task_actual][task_mode][maquina][0][periodo]
                                )
                                periodo_actual.add(
                                    self.variables["Production"][producto][num][paso][task_actual][task_mode][maquina][0][periodo]
                                    , periodo
                                )
                    
                    self.modelo.addConstr(
                        binario_actual == 1
                        , name = f"Production_binario_[{producto}][{num}][{paso}]".replace(" ","_")
                    )
                    
                    #self.modelo.addConstr(
                    #    periodo_actual >= 1#0 + self.delta
                    #    , name = f"Production_periodo_[{producto}][{num}][{paso}]".replace(" ","_")
                    #)
                    
                else:
                    #periodo anterior
                    task_anterior, dict_task_modes_anterior , _= receta[paso - 1]
                    
                    for task_mode, maquinas in dict_task_modes_anterior.items():
                        ultimo_intervalo = len(
                            self.datos.intervalos(task_mode=task_mode)
                        ) - 1
                        
                        for maquina in maquinas:
                            for periodo in periodos:
                                #binario_anterior.add(
                                #    self.variables["Production"][producto][num][paso] \
                                #        [task_anterior][task_mode][maquina][ultimo_intervalo][periodo]
                                #)
                                periodo_anterior.add(
                                    self.variables["Production"][producto][num][paso-1] \
                                        [task_anterior][task_mode][maquina][ultimo_intervalo][periodo]
                                    , periodo
                                )
                    
                    #periodo actual
                    task_actual, dict_task_modes_actual , _= receta[paso]
                    
                    for task_mode, maquinas in dict_task_modes_actual.items():
                        for maquina in maquinas:
                            for periodo in periodos:
                                binario_actual.add(
                                    self.variables["Production"][producto][num][paso] \
                                        [task_actual][task_mode][maquina][0][periodo]
                                )
                                periodo_actual.add(
                                    self.variables["Production"][producto][num][paso] \
                                        [task_actual][task_mode][maquina][0][periodo]
                                    , periodo
                                )
                    
                    self.modelo.addConstr(
                        binario_actual == 1
                        , name = f"Production_binario_[{producto}][{num}][{paso}]".replace(" ","_")
                    )
                    
                    self.modelo.addConstr(
                        periodo_anterior <= periodo_actual - self.delta
                        , name = f"Production_periodo_[{producto}][{num}][{paso}]".replace(" ","_")
                    )                

    #listo ecuacion 17
    def restriccion_maquinas(self):
        """
        restriccion_maquinas - 
        
        Crea las restricciones que limitan que las maquinas
        solo puedan procesar una actividad a la vez en cada periodo
        """
        
        #crea las restricciones para que las maquinas solo 
        #sean utilizadaa para un task_mode al mismo tiempo
        
        periodos = self.datos.periodos
        
        dict_maquinas = dict()
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            for periodo in periodos:
                maquina_periodo = (maquina,periodo)
                
                if maquina_periodo not in dict_maquinas:
                    dict_maquinas[maquina_periodo] = gp.LinExpr()
                    
                dict_maquinas[maquina_periodo].add(
                    self.variables["Production"][producto][num][paso] \
                        [task][task_mode][maquina][intervalo][periodo]
                )
                
        for key, value in dict_maquinas.items():
            self.modelo.addConstr(
                value <= 1
                , name = f"Maquina_activa_[{key[0]}][{key[1]}]".replace(" ","_")
            )

    #revisar (version anterior) ecuacion 18
    def restriccion_intervalos(self):
        """
        restriccion_intervalos -
        
        Crea las restricciones para que los intervalos de cada_task_mode
        tengan una diferencia de un periodo
        
        Las 3 restricciones 
        * `restriccion_maquinas`
        * `restriccion_Production`
        * `restriccion_intervalos`
        limitan los intervalos a cuales periodos pueden ser asignados
        
        """
        #crea las restricciones para que los intervalos de cada task_mode
        #tengan una distancia de un periodo
        
        #la funcion restriccion_Production ya garantiza que un intervalo
        #dado solo sea procesa a lo maximo una vez entre todos los periodos
        
        periodos = self.datos.periodos
        
        for producto, num in self.datos.iterar_productos():
            receta = self.datos.receta_producto(producto=producto)
            
            for paso in range(len(receta)):
                task, dict_task_modes , _= receta[paso]
        
                for task_mode, maquinas in dict_task_modes.items():
                    for maquina in maquinas:
                        for intervalo in range(len(self.datos.intervalos(task_mode=task_mode))):
                            
                            periodo_actual = gp.LinExpr()
                            periodo_anterior = gp.LinExpr()
                                    
                            if intervalo == 0:
                                continue
                            
                            for periodo in periodos:
                                
                                periodo_anterior.add(
                                    self.variables["Production"][producto][num][paso] \
                                        [task][task_mode][maquina][intervalo-1][periodo]
                                    , mult=periodo
                                )
                                
                                periodo_actual.add(
                                    self.variables["Production"][producto][num][paso] \
                                        [task][task_mode][maquina][intervalo][periodo]
                                    , mult=periodo
                                )
                                
                            self.modelo.addConstr(
                                periodo_actual - periodo_anterior <= 1
                                , name = f"Produccion_Intervalo_ub_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]".replace(" ","_")
                            )
                            
                            self.modelo.addConstr(
                                0 <= periodo_actual - periodo_anterior
                                , name = f"Produccion_Intervalo_lb_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]".replace(" ","_")
                            )

    #listo ecuacion 18
    def restriccion_intervalos_2(self):
        """
        restriccion_intervalos_2 - 
        
        Crea las restricciones para que los intervalos de cada task_mode tengan:
        * Una diferencia de 1 periodo si el primer intervalo esta activo,
            el cual es posible solo cuando todos los intervalos estan activos
        * Una diferencia de 0 periodo si el primer intervalo esta inactivo,
            el cual es posible solo cuando todos los intervalos estan inactivos
        """
        
        dict_sumas = dict()
        periodos = self.datos.periodos
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            prod = (producto,num,paso,task,task_mode,maquina)
            
            if prod not in dict_sumas:
                dict_sumas[prod] = dict()
                dict_sumas[prod]["primero"] = gp.LinExpr()
                dict_sumas[prod]["todos"] = dict()
            
            if intervalo not in dict_sumas[prod]["todos"]:
                dict_sumas[prod]["todos"][intervalo] = gp.LinExpr()
            
            for periodo in periodos:
                if intervalo == 0:
                    dict_sumas[prod]["primero"].add(
                        self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                    )
                
                dict_sumas[prod]["todos"][intervalo].add(
                    self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                    , periodo
                )
        
        for key in dict_sumas.keys():
            producto,num,paso,task,task_mode,maquina = key
            
            for intervalo in dict_sumas[key]["todos"].keys():
                
                if intervalo == 0:
                    continue
            
                self.modelo.addConstr(
                    dict_sumas[key]["todos"][intervalo] - dict_sumas[key]["todos"][intervalo-1] == dict_sumas[prod]["primero"]
                    , name=f"Produccion_intervalo_[{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]".replace(" ","_")
                )

    #listo ecuacion 19
    def restriccion_producto_terminado(self):
        """
        restriccion_producto_terminado - 
        
        Crea las restricciones para los productos que tienen un límite de tiempo en su produccion o "deadline"
        """
        
        #deadline
        for producto, num, periodo_demanda in self.datos.iterar_deadlines():
            expresion = gp.LinExpr()
            
            receta = self.datos.receta_producto(producto=producto)
            paso = len(receta) - 1
            task, dict_task_modes , _= receta[- 1]
            for task_mode, maquinas in dict_task_modes.items():
                intervalos = self.datos.intervalos(task_mode=task_mode)
                cantidad_intervalos = len(intervalos) - 1
                for maquina in maquinas:
                    for periodo in self.datos.periodos:

                        if periodo <= periodo_demanda:
                            expresion.add(
                                self.variables["Production"][producto][num][paso] \
                                [task][task_mode][maquina][cantidad_intervalos][periodo]
                                , periodo
                            )
                        else:
                            break
        
            self.modelo.addConstr(
                expresion <= periodo_demanda
                , name = f"deadline_producto_[{producto}][{num}]".replace(" ","_")
            )

    def crear_restricciones(self):
        """
        crear_restricciones - 
        
        Crea las restricciones necesarias del problema.
        """
        
        self.restriccion_Makespan()
        
        self.restriccion_maquinas()
        self.restriccion_Production()
        self.restriccion_Recetas()
        self.restriccion_intervalos()
        self.restriccion_CambioTurno()
        self.restriccion_producto_terminado()
        
        self.restriccion_Energia()
    
    def crear_restricciones_2(self):
        """
        crear_restricciones - 
        
        Crea las restricciones necesarias del problema.
        """
        
        self.restriccion_Makespan() #ecuacion 13
        self.restriccion_Energia() #ecuacion 14
        self.restriccion_produccion() #ecuacion 15
        self.restriccion_recetas_2() #ecuacion 16
        self.restriccion_maquinas() #ecuacion 17
        self.restriccion_intervalos_2() #ecuacion 18
        self.restriccion_producto_terminado() #ecuacion 19
        self.restriccion_CambioTurno() #ecuacion 20
        

    def resolver(self, write_file : str | Path = "out.sol"):
        """
        resolver - 
        
        Busca la solución optima del problema.
        """
        self.modelo.setParam("LogFile", "lm_schedule.log")
        self.modelo.Params.Threads = 12
        self.modelo.Params.NodefileStart = 0.5
        
        if os.path.exists(write_file):
            self.modelo.Params.TimeLimit = 60*60*1 #segundos
            self.modelo.params.MIPFocus = 3 #mejorar bound del objetivo
            self.modelo.params.Heuristics = 0.05 #heuristicas, valores mas grandes producen mas y mejores soluciones factibles
            self.modelo.params.MIPGap = 1e-4 #valor default
            self.modelo.Params.CutPasses = -1
            self.modelo.Params.Cuts = -1
            self.modelo.Params.Disconnected = -1
            #self.modelo.Params.ImproveStartTime = 60*60
            
            self.modelo.read(write_file)

            self.modelo.optimize()
            self.modelo.write(write_file)
        else:
            #self.modelo.Params.TimeLimit = 60*60*10 #segundos
            self.modelo.Params.PreSparsify = 1
            self.modelo.params.MIPFocus = 1 #buscar soluciones rapidamente
            self.modelo.params.Heuristics = 0.50 #heuristicas, valores mas grandes producen mas y mejores soluciones factibles
            self.modelo.params.MIPGap = 1 #valor alto para que termine lo mas rapido posible
            self.modelo.Params.CutPasses = 10
            self.modelo.Params.Cuts = 2
            self.modelo.Params.Disconnected = 1
            #self.modelo.Params.ImproveStartTime = 600
           
            self.modelo.optimize()
            if self.modelo.SolCount == 0:
                raise NotImplementedError("No existe una solucion")
            self.modelo.write(write_file)
    
    def resolver_completo(self, write_file : str | Path = "out.sol"):
        self.modelo.setParam("LogFile", "lm_schedule.log")
        
        self.modelo.params.MIPFocus = 3 #mejorar bound del objetivo
        self.modelo.params.Heuristics = 0.05 #heuristicas, valores mas grandes producen mas y mejores soluciones factibles
        self.modelo.params.MIPGap = 1e-4 #valor default
        self.modelo.Params.CutPasses = -1
        self.modelo.Params.Cuts = -1
        self.modelo.Params.Disconnected = -1
        
        self.modelo.optimize()
        self.modelo.write(write_file)
    
    def resultado(self, path : Path):
        archivo = open(path,"w")
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            for periodo in self.datos.periodos:
                
                var : gp.Var = self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                #print(f"{var.VarName} = {var.X}")
                archivo.write(f"{var.VarName},{var.X}"+"\n")
        
        archivo.close()
        

def main(
        guardar_modelo : bool = False
        , resolver_completo : bool = True
    ):
    ml = ModeloLineal()
    start = time.time()
    print("Creando objetivos")
    ml.crear_objetivos()
    print(f"Tiempo en crear objetivos: {time.time() - start:.2f} segundos")

    start = time.time()
    print("Creando restricciones")
    ml.crear_restricciones_2()
    print(f"Tiempo en crear restricciones: {time.time() - start:.2f} segundos")
    
    if (not os.path.exists("modelo.lp")) and (guardar_modelo):
        ml.modelo.write("modelo.lp")

    start = time.time()
    print("Resolviendo problema lineal")
    if resolver_completo:
        ml.resolver_completo()
    else:
        for _ in range(5):
            ml.resolver()
    print(f"Tiempo en resolver problema lineal: {time.time() - start:.2f} segundos")

    start = time.time()
    print("Resultado")
    ml.resultado(
        path="Resultado pl.txt"
    )
    print(f"Tiempo en mostrar resultado: {time.time() - start:.2f} segundos")
    
if __name__ == "__main__":
    main()