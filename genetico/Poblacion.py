import numpy as np
import random as rand
import os
import time
from .IndividuoA import IndividuoA

class Poblacion():
    
    def __init__(self
            , n : int = 10
            , probabilidad_mutacion : float = 0.01
            , generaciones : int = None
            , tiempo : float = 3600
            , peso_mutacion_mover_periodo : float = 1
            , peso_mutacion_cambiar_task : float = 1
            , p_saltar_periodo : float = 0.05
            , peso_seleccion_paso : float = 1.5
            , peso_seleccion_demanda : float = 3
            , prob_mutacion_mover_periodo_reducir : float = 0.5
            , prob_mutacion_mover_periodo_completa : float = 0.5
            , intentos_mutacion : int = 1
            , p_optimizacion_deterministica : float = 0.5
            , id_nombre : str = None
            , random_seed : int = None
        ):
        """
        __init__ - 
        
        Crea una población para encontrar la solución del problema
        de asignación.
        
        Parameters
        ----------
        n (int, optional, defaults to 10) :
            Número de individuos en una generación. Debe ser un número par mayor a 0.
        
        probabilidad_mutacion (float, optional, defaults to 0.01) :
            La probabilidad que suceda una mutacion. Debe ser un número entre 0 y 1 inclusive.
        
        generaciones (int, optional, defaults to None) :
            Número total de generaciones que se van a crear. Debe ser None o un número entero mayor a 0.
            Si es None, no hay un límite en el número de generaciones que se crearan.
            `generaciones` y `tiempo` no pueden ser ambos None al mismo tiempo.
        
        tiempo (float, optional, defaults to 3600) :
            Tiempo total en segundos que se utilizaran para buscar procesar las generaciones. Debe ser None o un número entero mayor a 0.
            Si es None, no hay un límite en el tiempo a procesar.
            `generaciones` y `tiempo` no pueden ser ambos None al mismo tiempo.
        
        peso_mutacion_mover_periodo (float, optional, defaults to 1) :
            Peso utilizado para elegir aleatoriamente el tipo de mutacion de mover el periodo de un task mode.
            Debe ser un número mayor o igual a 0.
        
        peso_mutacion_cambiar_task (float, optional, defaults to 1) :
            Peso utilizado para elegir aleatoriamente el tipo de mutacion de cambiar de máquina de un task.
            Debe ser un número mayor o igual a 0.
        
        p_saltar_periodo (float, optional, defaults to 0.05) :
            Probabilidad de "saltar" un periodo durante el periodo de inicialización (no cruce) de un individuo.
            Debe ser un número entre [0,1)
        
        peso_seleccion_paso (float, optional, defaults to 1.5) :
            Peso utilizado en la inicialización (no cruce) de un individuo. Este peso es utilizado para seleccionar aleatoriamente
            un task de un producto en la asignación, este peso hace que se tenga una myor probabilidada los productos que tengan más pasos completados,
            es decir, que faltan menos pasos para terminar.
            Debe ser un valor mayor a 0.
        
        peso_seleccion_demanda (float, optional, defaults to 3) :
            Peso utilizado en la inicialización (no cruce) de un individuo. Este peso es utilizado para seleccionar aleatoriamente
            un task de un producto en la asignación, este peso hace que se tenga una myor probabilidada los productos que tengan un identificadpr
            de demanda menor.
            Debe ser un valor mayor a 0.
        
        prob_mutacion_mover_periodo_reducir (float, optional, defaults to 0.5) :
            Probabilidad utilizada en la mutacion de mover periodo.
            Esta probabilidad es utilizada para determinar si se reduce el periodo del task mode.
            Un valor de 0 nunca se reducirá, un valor de 1 siempre lo reducirá.
            Debe ser un número entre [0,1]
        
        prob_mutacion_mover_periodo_completa (float, optional, defaults to 0.5) :
            Probabilidad utilizada en la mutacion de mover periodo.
            Esta probabilidad es utilizada para determinar si se reduce completamente el task mode.
            Un valor de 0 solo moverá un periodo a la vez, un valor de 1 siempre lo reducirá completamente 
            ,todo los periodos hasta que deje de ser valido.
            Debe ser un número entre [0,1]
        
        intentos_mutacion (int, optional, defaults to 1) :
            Número de intentos de aplicar una mutación en un individuo.
            Hace que el número esperado de mutaciones sea `intentos_mutacion * probabilidad_mutacion`,
            siguiendo una distribución binomial.
            Debe ser un número entero mayor o igual a 1.
        
        p_optimizacion_deterministica (float, optional, defaults to 0.5) :
            Probabilidad que se realiza una optimización deterministica.
            Debe ser un número entre [0,1]
            
        id_nombre (str, defaults to None) :
            str que identifica la poblacion.
            
        random_seed (int, optional, defaults to None) :
            Si se escoge utilizar una semilla aleatoria inicial.
            Si None entonces no se asigna una semilla.
        
        Raises
        ------
        ValueError :
            Si alguno de los parámetros no cumple con su rango de valores permitidos.
        """
        
        #asignar random seed
        if random_seed is not None:
            rand.seed(random_seed)
            np.random.seed(random_seed)
        
        if not isinstance(id_nombre,str):
            raise ValueError(f"id_nombre tiene que ser str")
            
        if (generaciones is None) and (tiempo is None):
            raise ValueError(f"generaciones y tiempo no pueden ser ambos None")

        if (generaciones is not None):
            if generaciones <= 0:
                raise ValueError(f"generaciones debe ser un número entero mayor a 0")

        if (tiempo is not None):
            if tiempo <= 0:
                raise ValueError(f"tiempo debe ser un número entero mayor a 0")

        if (probabilidad_mutacion < 0) or (probabilidad_mutacion > 1):
            raise ValueError(f"p_mutacion debe ser un valor entre 0 y 1, valor actual={probabilidad_mutacion}")
        
        if (n <= 1) and (n % 2 == 1):
            raise ValueError(f"n debe ser un número par mayor o igual a 2, valor actual={n}")
        
        if peso_mutacion_mover_periodo < 0:
            raise ValueError(f"peso_mutacion_mover_periodo debe ser mayor o igual a 0, valor actual={peso_mutacion_mover_periodo}")
        
        if peso_mutacion_cambiar_task < 0:
            raise ValueError(f"peso_mutacion_cambiar_task debe ser mayor o igual a 0, valor actual={peso_mutacion_cambiar_task}")
        
        if (p_optimizacion_deterministica < 0) or (p_optimizacion_deterministica > 1):
            raise ValueError(f"p_optimizacion_deterministica debe ser un valor entre [0,1], valor actual={p_optimizacion_deterministica}")
        
        if intentos_mutacion < 0:
            raise ValueError(f"intentos_mutacion debe ser mayor o igual a 0, valor actual={intentos_mutacion}")
        
        self.id = id_nombre
        
        self.cantidad_individuos = n
        self.p_mutacion = probabilidad_mutacion
        self.cantidad_maxima_generaciones = generaciones
        self.tiempo_maximo = tiempo
        self.p_optimizacion_deterministica = p_optimizacion_deterministica
        
        self.params_inicializar = {
            "probabilidad_saltar_periodo":p_saltar_periodo
            , "peso_seleccion_paso":peso_seleccion_paso
            , "peso_seleccion_demanda":peso_seleccion_demanda
        }
        
        self.params_mutacion = {
            "peso_mover_periodo" : peso_mutacion_mover_periodo
            , "peso_cambiar_task" : peso_mutacion_cambiar_task
        }
        
        self.intentos_mutacion = intentos_mutacion
        
        self.params_mutacion_mover_periodos = {
            "probabilidad_reducir" : prob_mutacion_mover_periodo_reducir
            , "probabilidad_completo" : prob_mutacion_mover_periodo_completa
        }
        
        inicio = time.time()
        
        self.individuos: list[IndividuoA] = [
            IndividuoA(inicializar=True,kwargs_inicializar=self.params_inicializar) for _ in range(self.cantidad_individuos)
        ]
        
        self.aptitudes = [[individuo.aptitud() for individuo in self.individuos]]
        
        self.makespan = [[individuo.aptitud(peso_makespan=1,peso_energia=0) for individuo in self.individuos]]
        self.costo = [[individuo.aptitud(peso_makespan=0,peso_energia=1) for individuo in self.individuos]]
        
        self.tiempos= [time.time()-inicio]
        self.individuo_incumbente : IndividuoA = None
        self.medida_busqueda = ["inicializar"]

    def mutar_individuo(self
            , individuo : IndividuoA
            , intentos : int = 1
        ) -> IndividuoA:
        """
        mutar_individuo - 
        
        Realizar la mutacion de un individuo.
        
        Para más información revisa `IndividuoA.mutacion`
        
        Parameters
        ----------
        individuo (IndividuoA) :
            El individuo a mutar.
        
        Returns
        -------
        IndividuoA :
            El individuo mutado.
        
        """
        
        for _ in range(intentos):
            if rand.random() < self.p_mutacion:
                individuo.mutacion(
                    peso_mover_periodo=self.params_mutacion["peso_mover_periodo"]
                    , peso_cambiar_task=self.params_mutacion["peso_cambiar_task"]
                    , kwargs_mover_periodo=self.params_mutacion_mover_periodos
                    , intentos_maximo=self.intentos_mutacion
                )

        return individuo
    
    def crear_descendientes(
            self
            , madre : IndividuoA
            , padre : IndividuoA
            , n_descendientes_regresados : int = 2
            , n_descendientes_creados : int = 4
            , probabilidad_optimizacion_deterministica : float = 0.5
            , verbose : bool = False
            , peso_makespan : float = 1
            , peso_energia : float = 1
        ) -> list[IndividuoA]:
        """
        crear_descendientes - 
        
        Crea `n_descendientes_creados` IndividuosA utilizando los individuos
        ascendientes `madre` y `padre` utilizando `IndividuoA.cruce()`.
        
        De los `n_descendientes_creados` Individuos creados, se regresan los 
        `n_descendientes_regresados` mejores.
        
        Los individuos creados pasan por un proceso de mutacion.
        
        Para más información revisa `IndividuoA.cruce()`
        
        Parameters
        ----------
        madre (IndividuoA) :
            Una instancia de `IndividuoA`
        
        padre (IndividuoA) :
            Una instancia de `IndividuoA`
        
        n_descendientes_regresados (int, optional, defaults to 2) :
            Número de descendientes que se uniran a la población.
        
        n_descendientes_creados (int, optional, defaults to 4) :
            Número de descendientes creados en total. 
        
        Returns
        -------
        list[IndividuoA] :
            Lista con los individuos más aptos.
        
        Raises
        ------
        ValueError :
            `n_descendientes_regresados` debe ser menor o igual a `n_descendientes_creados`
        
        """
        
        if n_descendientes_regresados > n_descendientes_creados:
            raise ValueError("n_descendientes_regresados debe ser menor o igual a n_descendientes_creados")
        
        hijos = []
        aptitudes_hijos = []
        
        for _ in range(n_descendientes_creados):
            hijo, _ = madre.cruce_time_leap(padre=padre)
            
            hijo = self.mutar_individuo(hijo, intentos=self.intentos_mutacion)
            if rand.random() < probabilidad_optimizacion_deterministica:
                hijo.optimizacion_deterministica()
            
            aptitud_hijo = hijo.aptitud(
                peso_makespan=peso_makespan,peso_energia=peso_energia
            )
            
            hijos.append(hijo)
            aptitudes_hijos.append(aptitud_hijo)
        
        #ordenar hijos dependiendo de las aptitudes, de menor a mayor
        pares_ordenados = sorted(zip(hijos, aptitudes_hijos), key=lambda x: x[1])
        
        hijos = [ind for ind, _ in pares_ordenados]
        aptitudes_hijos = [apt for _, apt in pares_ordenados]
        
        if verbose:
            print(f"Aptitudes de todos hijos creados: {aptitudes_hijos}")
        
        return hijos[:n_descendientes_regresados]

    def crear_generacion(
            self
            , verbose : bool = False
            , peso_makespan : float = 1
            , peso_energia : float = 1
        ):
        """
        crear_generacion - 
        
        Crea una nueva generacion de individuos (población)
        
        Realiza los pasos de cruce y mutación.
        
        Revisa `self.crear_descendientes` y `self.mutar_individuo` para más información.
        """
        
        generacion_actual = self.individuos.copy()
        rand.shuffle(generacion_actual)
        
        generacion_nueva: list[IndividuoA] = []
        
        if verbose:
            print("*"*10)
            print("Creando generacion nueva")
        
        while len(generacion_nueva) != self.cantidad_individuos:
            madre = generacion_actual.pop(0)
            padre = generacion_actual.pop(0)
            
            if verbose:
                print(f"Aptitud madre {madre.aptitud(peso_makespan=peso_makespan,peso_energia=peso_energia):.2f}")
                print(f"Aptitud padre {padre.aptitud(peso_makespan=peso_makespan,peso_energia=peso_energia):.2f}")
            
            hijos_nuevos: list[IndividuoA] = self.crear_descendientes(
                madre=madre
                ,padre=padre
                ,probabilidad_optimizacion_deterministica=self.p_optimizacion_deterministica
                ,n_descendientes_creados=4
                ,peso_energia=peso_energia
                ,peso_makespan=peso_makespan
                ,verbose=verbose
            )
            
            for hijo in hijos_nuevos:
                if verbose:
                    print(f"Aptitud hijo {hijo.aptitud(peso_makespan=peso_makespan,peso_energia=peso_energia):.2f}")
                generacion_nueva.append(hijo)

            if verbose:
                print(f"Cantidad individuos {len(generacion_nueva)}")
        
        self.individuos = generacion_nueva
        
        aptitudes_nuevas = [individuo.aptitud(
            peso_makespan=peso_makespan, peso_energia=peso_energia
            ) for individuo in self.individuos]
        
        makespan_nuevas = [individuo.aptitud(
            peso_makespan=1,peso_energia=0) for individuo in self.individuos]
        
        costo_nuevas = [individuo.aptitud(
            peso_makespan=0,peso_energia=1) for individuo in self.individuos]
        if verbose:
            print("Aptitudes nueva generacion")
            print(aptitudes_nuevas)
        
        self.aptitudes.append(aptitudes_nuevas)
        self.makespan.append(makespan_nuevas)
        self.costo.append(costo_nuevas)

    def calcular_solucion(
            self
            , verbose : bool = False
            , ciclo : dict[str,int] | None = None
            , iniciar_makespan : bool | None = None
        ):
        """
        calcular_solucion - 
        
        Corre la simulación de la población.
        
        Cuando `ciclo` es `None` la aptitud es el promedio del `makespan`
        y del `costo totaL de energía`.
        
        Cuando `ciclo` es un diccionario con llaves `makespan` y `energia`,
        y valores números enteros mayor o igual a 1. Se optimiza solo una
        medida durante esa cantidad de generaciones, y una vez llegado
        al límite en el diccionario se cambia a la otra medida, sucesivamente
        hasta llegar el límite de la simulación.
        
        Parameters
        ----------
        verbose (bool, optional, defaults to False) :
            Si se imprime el progreso en la consola.
        
        ciclo (dict[str,int] | None, optional, defaults to None) :
            * None para utilizar el promedio de `makespan` y `energia`.
            * diccionario con la cantidad de generaciones para el ciclo.
                En caso de ser menor o igual a 0, se fija a 1.
        
        iniciar_makespan (bool | None, optional, defaults to None) :
            Si en caso de ciclo se inicia con `makespan` o en caso contrario
            con `energia`.
            Si es None se fija a iniciar con `makespan` si se utiliza el ciclo.
        
        """
        
        time_start = time.time()
        generacion = 1
        ciclo_iteracion = 1
        
        if ciclo is not None:
            generaciones_makespan = ciclo.get("makespan",1)
            generaciones_energia = ciclo.get("energia",1)
            
            if generaciones_makespan <= 0:
                generaciones_makespan = 1
            
            if generaciones_energia <= 0:
                generaciones_energia = 1
            
            if iniciar_makespan is None:
                medida = "makespan"
            else:
                if iniciar_makespan:
                    medida = "makespan"
                else:
                    medida = "energia"
        else:
            medida = "promedio"
        
        if verbose:
            print("Iniciando")
            print("*"*20)

        continuar = True
        while continuar:
            inicio_generacion = time.time()
            
            #sí se utilizará ciclo
            if ciclo is not None:
                if medida == "makespan":
                    peso_makespan = 1
                    peso_energia = 0
                elif medida == "energia":
                    peso_makespan = 0
                    peso_energia = 1
            else:
                peso_makespan = 1
                peso_energia = 1
            
            self.crear_generacion(
                verbose=verbose
                , peso_makespan=peso_makespan
                , peso_energia=peso_energia
            )
            self.tiempos.append(time.time()-inicio_generacion)
            self.medida_busqueda.append(medida)
            
            aptitudes_actual = self.aptitudes[-1]
            if verbose:
                print(
                    f"Generación {generacion} creada|" + f"Valor optimo: {min(aptitudes_actual)}|" +f"Tiempo total: {time.time() - time_start:.2f} segundos"
                    , end=f"\r"
                )
            
            generacion += 1
            ciclo_iteracion += 1
            
            #revisar siguiente ciclo
            if ciclo is not None:
                if medida == "energia":
                    if ciclo_iteracion > generaciones_energia:
                        ciclo_iteracion = 1
                        medida = "makespan"
                elif medida == "makespan":
                    if ciclo_iteracion > generaciones_makespan:
                        ciclo_iteracion = 1
                        medida = "energia"
            
            #revisar si terminar simulación
            if self.cantidad_maxima_generaciones is not None:
                if generacion > self.cantidad_maxima_generaciones:
                    continuar = False
            if self.tiempo_maximo is not None:
                if time.time() - time_start > self.tiempo_maximo:
                    continuar = False
    
    def incumbente(self) -> IndividuoA:
        """
        incumbente - 
        
        Calcula el individuo incumbente, es decir el individuo con la mejor solución.
        
        Returns
        -------
        IndividuoA :
            El mejor individuo de la generacion actual
        """
        lista_individuos = self.individuos.copy()
        lista_aptitudes = self.aptitudes[-1]
        
        self.individuo_incumbente : IndividuoA = min(zip(lista_individuos, lista_aptitudes), key=lambda x: x[1])[0]
        
        return self.individuo_incumbente
    
    def guardar(self, path : str = None):
        """
        guardar - 
        
        Guarda los resultados de la población
        
        Parameters
        ----------
        path (str, optional, defaults to None) :
            Ubicacion donde se guardará la informacion. No el nombre del archivo.
            Archivo guardado en `os.path.join(path,f"{self.id}.txt")`
        """
        individuo = self.incumbente()
        
        if path is None:
            path = os.path.join("Datos Tesina", "algoritmo genetico")
        # Crear las carpetas si no existen
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path,f"{self.id}.txt"),"w", encoding="utf-8") as archivo:
            archivo.write(f"nombre: {self.id}")
            archivo.write(f"\nresultado: {individuo.aptitud()}")
            archivo.write(f"\nmakespan={individuo.aptitud(peso_energia=0)},energia={individuo.aptitud(peso_makespan=0)}")
            archivo.write(f"\nParámetros")
            archivo.write(f"\ncantidad_individuos: {self.cantidad_individuos}")
            archivo.write(f"\np_mutacion: {self.p_mutacion}")
            archivo.write(f"\ncantidad_maxima_generaciones: {self.cantidad_maxima_generaciones}")
            archivo.write(f"\ntiempo_maximo: {self.tiempo_maximo}")
            archivo.write(f"\np_optimizacion_deterministica: {self.p_optimizacion_deterministica}")
            archivo.write(f"\nprobabilidad_saltar_periodo: {self.params_inicializar["probabilidad_saltar_periodo"]}")
            archivo.write(f"\npeso_seleccion_paso: {self.params_inicializar["peso_seleccion_paso"]}")
            archivo.write(f"\npeso_seleccion_demanda: {self.params_inicializar["peso_seleccion_demanda"]}")
            archivo.write(f"\npeso_mover_periodo: {self.params_mutacion["peso_mover_periodo"]}")
            archivo.write(f"\npeso_cambiar_task: {self.params_mutacion["peso_cambiar_task"]}")
            archivo.write(f"\nintentos_mutacion: {self.intentos_mutacion}")
            archivo.write(f"\nprobabilidad_reducir: {self.params_mutacion_mover_periodos["probabilidad_reducir"]}")
            archivo.write(f"\nprobabilidad_completo: {self.params_mutacion_mover_periodos["probabilidad_completo"]}")
            archivo.write(f"\n\nValores Generaciones")
            for g in range(len(self.aptitudes)):
                archivo.write(f"\nGeneracion {g}")
                archivo.write(f"\naptitudes {self.aptitudes[g]}")
                promedio = sum(self.aptitudes[g]) / len(self.aptitudes[g])
                archivo.write(f"\npromedio de aptitud {promedio}")
                archivo.write(f"\ntiempo de creacion de generacion (segundos) {self.tiempos[g]:.4f}")
                if self.medida_busqueda[g] in ("energia","makespan"):
                    archivo.write(f"\noptimizando: {self.medida_busqueda[g]}")
                else:
                    archivo.write("\noptimizando: otro")
            archivo.write(f"\n\nValores Generaciones makespan")
            for g in range(len(self.makespan)):
                archivo.write(f"\nGeneracion {g}")
                archivo.write(f"\nmakespan {self.makespan[g]}")
                promedio = sum(self.makespan[g]) / len(self.makespan[g])
                archivo.write(f"\npromedio de makespan {promedio}")
                archivo.write(f"\ntiempo de creacion de generacion (segundos) {self.tiempos[g]:.4f}")
                if self.medida_busqueda[g] in ("energia","makespan"):
                    archivo.write(f"\noptimizando: {self.medida_busqueda[g]}")
                else:
                    archivo.write("\noptimizando: otro")
            archivo.write(f"\n\nValores Generaciones costo")
            for g in range(len(self.costo)):
                archivo.write(f"\nGeneracion {g}")
                archivo.write(f"\ncosto {self.costo[g]}")
                promedio = sum(self.costo[g]) / len(self.costo[g])
                archivo.write(f"\npromedio de costo {promedio}")
                archivo.write(f"\ntiempo de creacion de generacion (segundos) {self.tiempos[g]:.4f}")
                if self.medida_busqueda[g] in ("energia","makespan"):
                    archivo.write(f"\noptimizando: {self.medida_busqueda[g]}")
                else:
                    archivo.write("\noptimizando: otro")
