from Carga_Datos import Datos, PATH_INPUT
import gurobipy as gp
import numpy as np
import time
from pathlib import Path

class ModeloLineal:
    
    def __init__(self, delta = 0.0001):
        
        self.modelo = gp.Model("Scheduling")
        self.modelo.setParam("LogFile", "lm_schedule.log")
        self.modelo.Params.Threads = 8
        
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
                    , name = f"Amount of solar energy in t = {periodo}"
                )
                , "Socket" : self.modelo.addVar(
                    lb = 0
                    , vtype = gp.GRB.CONTINUOUS
                    , name = f"Amount of socket energy in t = {periodo}"
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
                    , name =f"Production, [{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}][{periodo}]"
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
            , name = f"Periodo final"
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
            , name = f"Costo de Energia"
        )
        
        self.modelo.ModelSense = sense

    def restriccion_Makespan(self):
        """
        restriccion_Makespan - 
        
        Crea la restriccion de Makespan (tiempo total de produccion)
        """
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            for periodo in self.datos.periodos:
        
                self.modelo.addConstr(
                    periodo * self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo] <= self.variables["Makespan"]
                    , name = f"Makespan, [{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}][{periodo}]"
                )
    
    def restriccion_Energia(self):
        """
        restriccion_Energia - 
        
        Crea la condicción que la suma de energia por periodo sea igual a la suma de energia utilizada.
        
        Esto es para que en la funcion objetivo de minimizar el costo de energia
        no se considere la energia solar que es "gratis" (gasto variable = 0). 
        """
        
        for periodo in self.datos.periodos:
            lista_variables = []
            
            for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
                lista_variables.append(
                    self.datos.energia_task_intervalo(task=task, task_mode=task_mode, intervalo=intervalo) *
                    self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                )
                
            self.modelo.addConstr(
                self.variables["Energy"][periodo]["Solar"] + self.variables["Energy"][periodo]["Socket"] ==
                gp.quicksum(lista_variables)
                , name = f"Uso de Energia, {periodo}"
            )
    
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
                , name = f"Production_intervalo, [{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]"
            )

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
                        , name = f"Production_binario, [{producto}][{num}][{paso}]"
                    )
                    
                    self.modelo.addConstr(
                        periodo_actual >= 0 + self.delta
                        , name = f"Production_periodo, [{producto}][{num}][{paso}]"
                    )
                    
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
                        , name = f"Production_binario, [{producto}][{num}][{paso}]"
                    )
                    
                    self.modelo.addConstr(
                        periodo_anterior <= periodo_actual - self.delta
                        , name = f"Production_periodo, [{producto}][{num}][{paso}]"
                    )                

    def restriccion_maquinas(self):
        """
        restriccion_maquinas - 
        
        Crea las restricciones que limitan que las maquinas
        solo puedan procesar una actividad a la vez en cada periodo
        
        Las 3 restricciones 
        * `restriccion_maquinas`
        * `restriccion_Production`
        * `restriccion_intervalos`
        limitan los intervalos a cuales periodos pueden ser asignados
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
                , name = f"Maquina_activa, [{key[0]}][{key[1]}]"
            )

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
                                , name = f"Produccion_Intervalo_ub, [{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]"
                            )
                            
                            self.modelo.addConstr(
                                0 <= periodo_actual - periodo_anterior
                                , name = f"Produccion_Intervalo_lb, [{producto}][{num}][{paso}][{task}][{task_mode}][{maquina}][{intervalo}]"
                            )

    def restriccion_producto_terminado(self):
        """
        restriccion_producto_terminado - 
        
        Crea las restricciones para los productos que tienen un límite de tiempo en su produccion o "deadline"
        """
        
        #deadline
        for producto, num, periodo_demanda in self.datos.iterar_deadlines():
            expresion = gp.LinExpr()
            
            receta = self.datos.receta_producto(producto=producto)
            paso = len(receta)
            task, dict_task_modes , _= receta[- 1]
            for task_mode, maquinas in dict_task_modes.items():
                intervalos = self.datos.intervalos(task_mode=task_mode)
                cantidad_intervalos = len(intervalos)
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
                , name = f"deadline_producto, [{producto}][{num}]"
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

    def resolver(self):
        """
        resolver - 
        
        Busca la solución optima del problema.
        """
        
        self.modelo.optimize()
    
    def resultado(self, path : Path):
        archivo = open(path,"w")
        
        for producto, num, paso, task, task_mode, maquina, intervalo in self.datos.iterar_completo():
            for periodo in self.datos.periodos:
                
                var : gp.Var = self.variables["Production"][producto][num][paso][task][task_mode][maquina][intervalo][periodo]
                #print(f"{var.VarName} = {var.X}")
                archivo.write(f"{var.VarName},{var.X}"+"\n")
        
        archivo.close()

def main():
    ml = ModeloLineal()
    start = time.time()
    print("Creando objetivos")
    ml.crear_objetivos()
    print(f"Tiempo en crear objetivos: {time.time() - start:.2f} segundos")

    start = time.time()
    print("Creando restricciones")
    ml.crear_restricciones()
    print(f"Tiempo en crear restricciones: {time.time() - start:.2f} segundos")

    start = time.time()
    print("Resolviendo problema lineal")
    ml.resolver()
    print(f"Tiempo en resolver problema lineal: {time.time() - start:.2f} segundos")

    start = time.time()
    print("Resultado")
    ml.resultado()
    print(f"Tiempo en mostrar resultado: {time.time() - start:.2f} segundos")
    
if __name__ == "__main__":
    main()