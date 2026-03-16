
import pandas as pd
import numpy as np
from typing import Any
import random as rand
from graficas import (
    task_array_to_dataframe
    , grafica_gantt_plt
    , dataframe_to_array
)
from .IndividuoBase import IndividuoBase

class IndividuoA(IndividuoBase):
    """
    IndividuoA - 
    
    Clase que representa un individuo, es decir una solución del problema
    de optimización.
    """
    
    def __init__(
            self
            , inicializar : bool = False
            , saved_path : str = None 
            , random_seed : int = None
            , kwargs_inicializar : dict = None
        ):
        """
        __init__ - 
        
        Inicializa un individuo con una solucion valida.
        
        Parameters
        ----------
        inicializar (bool, optional, defaults to False) :
            Si se inicializa o no, utilizado para crear un hijo.
            False si es un hijo. True si se crea una nueva solucion.
        
        saved_path (str, optional, defaults to None) :
            Si se carga una solucion guardada previamente.
            Tiene que ser una ubicacion valida.
        
        random_seed (int, optional, defaults to None) :
            Si se escoge utilizar una semilla aleatoria inicial.
            Si None entonces no se asigna una semilla.
        
        kwargs_inicializar (dict, optional, defaults to None) :
            kwargs de `self.inicializar`
        
        """
        super().__init__()
        
        #asignar random seed
        if random_seed is not None:
            rand.seed(random_seed)
            np.random.seed(random_seed)
        
        #intentar cargar el cromosoma guardado
        if saved_path is not None:
            if str(saved_path).endswith(".csv"):
                try:
                    df = pd.read_csv(saved_path)
                    self.cromosoma = dataframe_to_array(
                        df
                        , dict_maquinas=self.datos.machines_id
                        , periodos=max(self.datos.periodos)
                    )
                    #print("Lectura de dataframe exitosa")
                    #ya se cargó exitosamente el cromosoma
                    return
                except Exception as e:
                    print(f"Error leyendo DataFrame a csv: {e}\nSiguiendo proceso segun el parametro inicializar")
        
        #no hay kwargs se agregan valores default para crear figuras de la tesina
        if kwargs_inicializar is None: #parametros para figuras
            kwargs_inicializar = {
                "probabilidad_saltar_periodo":0.33
                , "peso_seleccion_paso":1.5
                , "peso_seleccion_demanda":3
            }
        
        #generar hasta que sea viable
        es_viable = False
        while (not es_viable) and inicializar:
            self.inicializar(
                **kwargs_inicializar
            )
            es_viable : bool = self.es_viable()["todo"]["bool"]
            
    def inicializar(
            self
            , probabilidad_saltar_periodo : float = 0.05
            , peso_seleccion_paso : float = 1.5
            , peso_seleccion_demanda : float = 5
        ):
        """
        inicializar - Inicializa los cromosomas (scheduling) del individuo
        
        1.- Revisa periodo por periodo, iniciando con los más cercanos (los que tienen menor valor numerico):
        2.- Revisa si se salta el periodo, una revisión en cada máquina
        3.- Revisa si la combinación periodo-máquina ya esta ocupada.
        4.- Si se puede agregar un task mode, se ordena aleatoriamente todos los productos que faltan de terminar de producir
        5.- Se revisa maquina por maquina disponibles
        6.- Se revisa producto por producto hasta que se pueda agregar un task mode
        6.1.- Se revisa si se puede agregar un task mode por el criterio de time leap en la maquina.
        6.2.- Se selecciona aletoriamente un número de demanda (product request) del producto del paso 6, revisar la distribución aleatoria en (*)
        6.3.- Si se agrega exitosamente, se actualiza los datos del producto-demanda agregado
        7.- Si durante el paso 6 no se pudo agregar un task mode, se considera que la maquina esta "ocupada" y ya no se busca agregar un task mode
        8.- Si todas las maquinas estan ocupadas en este periodo, se regresa al paso 1 con el siguiente periodo, 
            si ya no hay más periodos que revisar se termina el proceso de inicialización.
        
        (*) Al agregar un task mode, se selecciona aleatoriamente un producto (con igual probabilidad) y se selecciona
        el número de demanda aleatoriamente con el siguiente peso:
        `(paso de la receta)*peso_seleccion_paso + ((cantidad total demanda del producto) - (número de demanda))*peso_seleccion_demanda`
        
        Parameters
        ----------
        probabilidad_saltar_periodo (float, optional, defaults to 0.05) :
            Al revisar un periodo en una máquina, se tiene una probabilidad `probabilidad_saltar_periodo`
            de dejar el periodo sin un task mode asignado.
            Al ser una probabilidad debe ser igual a un número entre 0 y 1.
        
        peso_seleccion_paso (float, optional, defaults to 1.5) :
            Para la fórmula del peso de selección del producto de demanda representa un factor
            que da prioridad a los productos que le faltan menos pasos para terminar su producción.
        
        peso_seleccion_demanda (float, optional, defaults to 5) :
            Para la fórmula del peso de selección del producto de demanda representa un factor
            que da prioridad a los productos que que tienen un número de demanda menor, y por lo tanto van terminandose
            antes que los demás productos de la misma clase pedidos.
        
        """
        
        if (probabilidad_saltar_periodo < 0) or (probabilidad_saltar_periodo > 1):
            raise ValueError(f"probabilidad_saltar_periodo debe ser un número entre 0 y 1, valor: {probabilidad_saltar_periodo}")
        
        if (peso_seleccion_paso < 0):
            raise ValueError(f"peso_seleccion_paso debe ser un número mayor o igual a 0, valor: {peso_seleccion_paso}")
        
        if (peso_seleccion_demanda < 0):
            raise ValueError(f"peso_seleccion_demanda debe ser un número mayor o igual a 0, valor: {peso_seleccion_demanda}")
        
        periodo = 1
        maquinas_set = set(self.maquinas.keys())
        maquinas_en_periodo = set()
        
        tasks_a_agregar = dict()
        lista_productos_por_terminar = list()
        
        for producto, demanda in self.datos.iterar_productos():
            if producto not in lista_productos_por_terminar:
                lista_productos_por_terminar.append(producto)
            
            if producto not in tasks_a_agregar:
                tasks_a_agregar[producto] = dict()
                tasks_a_agregar[producto]["demanda"] = dict()
                tasks_a_agregar[producto]["receta"] = self.datos.receta_producto(producto=producto)
            
            tasks_a_agregar[producto]["demanda"][demanda] = dict()
            tasks_a_agregar[producto]["demanda"][demanda]["paso_actual"] = 0
            tasks_a_agregar[producto]["demanda"][demanda]["terminado"] = False
            
            #contiene el ultimo periodo donde se realiza cada paso
            tasks_a_agregar[producto]["demanda"][demanda]["pasos"] = {i: 0 for i in range(len(tasks_a_agregar[producto]["receta"]))}
        
        while periodo in self.periodos:
            #print("periodo actual revisando", periodo)
            
            if len(lista_productos_por_terminar) == 0: #se agregaron todos los productos
                break
            
            for maquina in maquinas_set: #revisar las maquinas en el periodo
                if not self._IndividuoBase__es_vacio_array( #revisa si la maquina esta ocupada
                        periodo=periodo
                        , maquina=maquina
                    ):
                    maquinas_en_periodo.add(maquina)
                    continue
                
                if (rand.random() < probabilidad_saltar_periodo): #saltar periodo para cada maquina
                    maquinas_en_periodo.add(maquina)
            
            #si todas las maquinas estan ocupadas seguir al siguiente periodo
            if maquinas_set == maquinas_en_periodo:
                maquinas_en_periodo = set()
                periodo = periodo + 1
                continue

            maquinas_faltantes = maquinas_set.difference(maquinas_en_periodo)
            
            #si time leap = 192
            #si periodo = 192
            #valor esperado: 1
            
            #si time leap = 192
            #si periodo = 191
            #valor esperado: 2
            intervalos_time_leap = min(
                (ct for ct in self.cambio_turno if ct >= periodo)
                , default=max(self.periodos)) - periodo + 1
            
            lista_aleatoria = lista_productos_por_terminar
            rand.shuffle(lista_aleatoria)
            
            producto_agregado = False
            for producto in lista_aleatoria:
                demanda_incompleta = list()
                demanda_pesos = list()
                cantidad_productos_demandados = len(tasks_a_agregar[producto]["demanda"])
                
                demanda_info = dict()
                
                for demanda in tasks_a_agregar[producto]["demanda"]:
                    
                    if tasks_a_agregar[producto]["demanda"][demanda]["terminado"]:
                        continue #producto (demanda) terminado
                    
                    paso_actual : int = tasks_a_agregar[producto]["demanda"][demanda]["paso_actual"]
                    #revisa si el paso anterior se ha terminado de procesar
                    if paso_actual != 0:
                        periodo_paso_anterior = tasks_a_agregar[producto]["demanda"][demanda]["pasos"][paso_actual - 1]
                        
                        if not (periodo_paso_anterior < periodo): #aun no se ha terminado el paso anterior no se puede agregar
                            continue
                    
                    hay_espacio = False
                    hay_maquinas = False
                    for task_mode, maquinas in tasks_a_agregar[producto]["receta"][paso_actual][1].items():
                        #revisa si hay suficientes periodos disponibles para agregar el task mode
                        espacio_task_mode = (
                            len(self.datos.intervalos(task_mode=task_mode)) 
                            <= intervalos_time_leap
                        )
                        
                        #revisa si hay task mode en maquina faltante
                        set_maquinas_task_mode = set()
                        for maquina in maquinas:
                            set_maquinas_task_mode.add(maquina)
                            
                        maquinas_agregar = maquinas_faltantes.intersection(set_maquinas_task_mode)
                        if (espacio_task_mode) and (len(maquinas_agregar) != 0):
                            
                            if demanda not in demanda_info:
                                demanda_info[demanda] = list()
                            
                            hay_espacio = True
                            hay_maquinas = True
                            for maquina in maquinas_agregar:
                                demanda_info[demanda].append((task_mode, maquina))
                    
                    if (not hay_maquinas): #no hay maquina para agregar task mode en esta demanda
                        continue
                    
                    if (not hay_espacio): #no hay espacio para agregar task mode en esta demanda
                        continue
                    
                    #agregar demanda disponible
                    demanda_incompleta.append(demanda)
                    demanda_pesos.append(
                        #aumentar la probabilidad de seleccionar los productos a punto de terminar
                        (tasks_a_agregar[producto]["demanda"][demanda]["paso_actual"]) * peso_seleccion_paso
                        
                        #aumentar la probabilidad de seleccionar demandas menores
                        + (cantidad_productos_demandados - demanda) * peso_seleccion_demanda 
                    ) 
                
                #si no hay productos (demanda) disponibles para agregar buscar siguiente producto
                if len(demanda_incompleta) == 0:
                    continue
            
                #seleccionar demanda
                demanda_seleccionada = rand.choices(
                    population=demanda_incompleta
                    , weights=demanda_pesos
                    , k = 1
                )[0]
                
                task_mode_seleccionado, maquina_seleccionada = rand.choices(
                    demanda_info[demanda_seleccionada]
                    , k = 1
                )[0]
                
                paso_actual : int = tasks_a_agregar[producto]["demanda"][demanda_seleccionada]["paso_actual"]
                
                #agregar producto
                _, _, agregado, _ = self.agregar_task_mode(
                    maquina= maquina_seleccionada
                    , periodo= periodo
                    , producto= producto
                    , paso= paso_actual
                    , demanda= demanda_seleccionada
                    , task_mode= task_mode_seleccionado
                )
                
                if agregado:
                    tasks_a_agregar[producto]["demanda"][demanda]["pasos"][paso_actual] = periodo + len(self.datos.intervalos(task_mode=task_mode_seleccionado)) - 1
                    
                    tasks_a_agregar[producto]["demanda"][demanda_seleccionada]["paso_actual"] = paso_actual + 1
                    producto_agregado = True
                    
                    if len(tasks_a_agregar[producto]["receta"]) <= (paso_actual + 1):
                        tasks_a_agregar[producto]["demanda"][demanda_seleccionada]["terminado"] = True

                else:
                    continue
                
                #revisar si se termino de agregar todas las demandas del producto
                lista_revisar_demanda = list()
                for demanda in tasks_a_agregar[producto]["demanda"].keys():
                    lista_revisar_demanda.append(
                        tasks_a_agregar[producto]["demanda"][demanda]["terminado"]
                    )
                if all(lista_revisar_demanda):
                    lista_productos_por_terminar.remove(producto)
                                
            #no se agrego producto seguir al siguiente periodo
            if not producto_agregado:
                maquinas_en_periodo = set()
                periodo = periodo + 1
                continue
    
    def mutacion_mover_periodo(
            self
            , array : np.ndarray[tuple[int, int], str] = None
            , maquina : str = None
            , periodo : int = None
            , probabilidad_reducir : float = 0.5
            , probabilidad_completo : float = 0.5
            , guardar_en_cromosoma : bool = True
        ) -> tuple[np.ndarray[tuple[Any, ...], np.dtype[Any]], bool, int]:
        """
        mutacion_mover_periodo - 
        
        Mutacion que mueve los intervalos de un task_mode a travez de los periodos dentro de la misma máquina.
        
        Parameters
        ----------
        array (np.ndarray[tuple[int, int], str], optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        maquina (str, optional, defaults to None) :
            Maquina donde se moverá el task mode.
            Si es None se escoge una maquina aleatoriamente con igual probabilidad.
        
        periodo (int, optional, defaults to None) :
            Periodo donde se moverá el task mode.
            Si es None se escoge un periodo aleatoriamente con igual probabilidad.
        
        probabilidad_reducir (float, optional, defaults to 0.5) :
            Se genera un número aleatorio, si es menor a `probabilidad_reducir`
            se mueve el task_mode reduciendo el valor del periodo, en caso contrario se mueve
            aumentando el periodo.
        
        probabilidad_completo (float, optional, defaults to 0.5) :
            Se genera un número aleatorio, si es menor a `probabilidad_completo`
            se mueve hasta chochar con otro task_mode, en caso contrario solo se mueve
            un periodo.
        
        guardar_en_cromosoma (bool, optional, defaults to True) :
            Si la mutacion es viable se guardará el array resultado en `self.cromosoma` si True.
        
        Returns
        -------
        tuple[np.ndarray[tuple[Any, ...], np.dtype[Any]], bool] :
            * np.ndarray[tuple[Any, ...], np.dtype[Any]] : el array modificado si la mutación fue exitosa,
                en caso contrario se regresa `array`.
            * bool: si se pudo realizar la mutación o no.
            * int: motivo de falla o exito, 1 si la mutación fue exitosa, -1 si error en el cambio del task mode,
                    -2 si la mutación no es viable,
                    -4 si el espacio seleccionado no tiene un task asignado
        
        Raises
        ------
        ValueError :
            Si `probabilidad_reducir` no es un valor entre 0 y 1.
        
        ValueError :
            Si `probabilidad_completo` no es un valor entre 0 y 1.
        
        """

        if (probabilidad_reducir < 0) or (probabilidad_reducir > 1):
            raise ValueError("probabilidad_reducir debe ser un valor entre 0 y 1")
        if (probabilidad_completo < 0) or (probabilidad_completo > 1):
            raise ValueError("probabilidad_completo debe ser un valor entre 0 y 1")
        
        #si no se da un array se selecciona el cromosoma (solucion actual)
        if array is None:
            array = self.cromosoma
        
        #si no da una maquina, se selecciona aleatoriamente una
        if maquina is None:
            maquina = rand.choice(list(self.maquinas.keys()))
        
        #si no da un periodo, se selecciona aleatoriamente uno
        if periodo is None:
            periodo = rand.choice(self.periodos)

        #se revisa si maquina-periodo seleccionados esta ocupada
        es_vacio = self._IndividuoBase__es_vacio_array(
            maquina=maquina
            , periodo=periodo
            , array=array
        )
        
        #es vacio por lo tanto no hay cambio que reailizar
        if es_vacio:
            return array, False, -4

        #se busca el inicio del task_mode de maquina-periodo
        maquina, periodo = self._IndividuoBase__buscar_inicio_task_mode(
            maquina = maquina
            , periodo = periodo
            , array = array
        )
        
        #se mueve el task_mode
        try: #la mutacion fue exitosa
            _,_ , resultado, array_resultado =self.mover_periodo_task_mode(
                maquina=maquina
                , periodo=periodo
                , tipo_movimiento=(-1 if rand.random() < probabilidad_reducir else 1)
                , completa=(True if rand.random() < probabilidad_completo else False)
                , array=array
            )
        except: #la mutacion no fue exitosa
            return array, False, -1
        
        if resultado and self.es_viable(array_resultado)["todo"]["bool"]:
            if guardar_en_cromosoma:
                self.cromosoma = array_resultado.copy()
            return array_resultado, True, 1
        else:
            return array, False, -2
    
    def mutacion_cambiar_task_mode(
            self
            , array : np.ndarray[tuple[int, int], str] = None
            , maquina : str = None
            , periodo : int = None
            , guardar_en_cromosoma : bool = True
            , verbose : bool = False
        ) -> tuple[np.ndarray[tuple[Any, ...], np.dtype[Any]], bool, int]:
        """
        mutacion_cambiar_task_mode - 
        
        Mueve un task mode compatible a otra maquina.
        
        Parameters
        ----------
        array (np.ndarray[tuple[int, int], str], optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        maquina (str, optional, defaults to None) :
            Maquina donde se moverá el task mode.
            Si es None se escoge una maquina aleatoriamente con igual probabilidad.
        
        periodo (int, optional, defaults to None) :
            Periodo donde se moverá el task mode.
            Si es None se escoge un periodo aleatoriamente con igual probabilidad.
        
        guardar_en_cromosoma (bool, optional, defaults to True) :
            Si la mutacion es viable se guardará el array resultado en `self.cromosoma` si True.
        
        verbose (bool, optional, defaults to False) :
            Si se imprime información adicional para debug.
        
        Returns
        -------
        tuple[np.ndarray[tuple[Any, ...], np.dtype[Any]], bool] :
            * np.ndarray[tuple[Any, ...], np.dtype[Any]] : el array modificado si la mutación fue exitosa,
                en caso contrario se regresa `array`.
            * bool: si se pudo realizar la mutación o no.
            * int: motivo de falla o exito, 1 si la mutación fue exitosa, -1 si error en el cambio del task mode,
                    -2 si la mutación no es viable, -3 el task no tiene otra maquina donde procesarse,
                    -4 si el espacio seleccionado no tiene un task asignado
        """
        
        if verbose:
            print("Metodo:mutacion_cambiar_task_mode")
        
        #si no se da un array se selecciona el cromosoma (solucion actual)
        if array is None:
            array = self.cromosoma
            if verbose:
                print("Utilizando cromosoma")

        #si no da una maquina, se selecciona aleatoriamente una
        if maquina is None:
            maquina = rand.choice(list(self.maquinas.keys()))

        #si no da un periodo, se selecciona aleatoriamente uno
        if periodo is None:
            periodo = rand.choice(self.periodos)
        
        if verbose:
            print(f"Maquina:{maquina},Periodo:{periodo}")
            
        #se revisa si maquina-periodo seleccionados esta ocupada
        es_vacio = self._IndividuoBase__es_vacio_array(
            maquina=maquina
            , periodo=periodo
            , array=array
        )
        
        #es vacio por lo tanto no hay cambio que reailizar
        if es_vacio:
            if verbose:
                print("No hay task mode asignado en esta maquina y periodo")
            return array, False, -4

        #se busca el inicio del task_mode de maquina-periodo
        maquina, periodo = self._IndividuoBase__buscar_inicio_task_mode(
            maquina = maquina
            , periodo = periodo
            , array = array
        )
        producto, demanda, task_mode, _, paso = self._IndividuoBase__gen_inverso(
            self.obtener_gen(periodo=periodo, maquina=maquina, array=array)
        )
        
        if verbose:
            print(f"Producto:{producto},Demanda:{demanda},Task mode:{task_mode},Paso:{paso}")
        
        receta = self.datos.receta_producto(producto=producto)
        ultimo_paso = receta[-1][2]
        if verbose:
            print(f"Receta:{receta}\nUltimo paso:{ultimo_paso}")
        
        if paso==ultimo_paso:
            maximo_periodo : int = max(self.periodos)
        else:
            maximo_periodo : int = self._IndividuoBase__buscar_task_mode(
                producto_buscar=producto, demanda_buscar=demanda, paso_buscar=paso+1,array=array)[1]-1
        
        if paso==0:
            minimo_periodo : int = min(self.periodos)
        else:
            minimo_periodo : int = self._IndividuoBase__buscar_task_mode(
                producto_buscar=producto, demanda_buscar=demanda, paso_buscar=paso-1,array=array,inicio=False)[1]+1 

        _, dict_task_modes, _ = receta[paso]
        lista_disponible = list()
        for task_mode_receta in dict_task_modes:
            if task_mode == task_mode_receta:
                continue
            for maquina_nueva in dict_task_modes[task_mode_receta]:
                if maquina_nueva == maquina:
                    continue
                lista_disponible.append(maquina_nueva)
        #no hay maquina disponible a cambiar
        if len(lista_disponible) == 0:
            return array, False, -3
        maquina_nueva : str = rand.choice(lista_disponible) #se selecciona una maquina aleatoria
        
        #intentar cambiar el task mode
        try:
            #el cambio fue exitoso
            resultado, array_resultado = self._IndividuoBase__cambiar_task_mode(
                maquina_origen=maquina
                , periodo_origen=periodo
                , maquina_nueva=maquina_nueva
                , array=array
                , inicio=minimo_periodo
                , termina=maximo_periodo
            )
        except:
            #el cambio no fue exitoso
            return array, False, -1
        
        if resultado and self.es_viable(array_resultado)["todo"]["bool"]:
            if guardar_en_cromosoma:
                self.cromosoma = array_resultado.copy()
            return array_resultado, True, 1
        else:
            return array, False, -2
    
    def mutacion(
            self
            , peso_mover_periodo : int = 1
            , peso_cambiar_task : int = 1
            , kwargs_mover_periodo : dict = None
            , kwargs_cambiar_task : dict = None
            , intentos_maximo : int = 1
        ) -> bool:
        """
        mutacion - Realiza una mutación a esta instancia.
        
        Se realiza uno de los 2 tipos de mutación:
        * Mover periodo: mueve el task_mode a travez de los periodos. (Revisa self.mutacion_mover_periodo para más información)
        * Cambiar task: cambia el task_mode del task. (Revisa self.mutacion_cambiar_task_mode para más información)
        
        Si la mutación no es viable, no se hace el cambio.
        
        Parameters
        ----------
        peso_mover_periodo (int, optional, defaults to 1) :
            Peso de seleccionar la mutacion Mover periodo. Debe ser un número mayor o igual a 0.
        
        peso_cambiar_task (int, optional, defaults to 1) :
            Peso de seleccionar la mutacion Cambiar task. Debe ser un número mayor o igual a 0.
        
        kwargs_mover_periodo (dict, optional, defaults to None) :
            kwargs para Mover periodo. Revisa self.mutacion_mover_periodo para más información
        
        kwargs_cambiar_task (dict, optional, defaults to None) :
            kwargs para Cambiar task. Revisa self.mutacion_cambiar_task_mode para más información
        
        Returns
        -------
        bool :
            True si la mutación fue aplicada correctamente, False en caso contrario.
        
        Raises
        ------
        ValueError :
            Si `peso_mover_periodo` o `peso_cambiar_task` son menores que 0.
        
        """
        
        if (peso_mover_periodo < 0):
            raise ValueError(f"peso_mover_periodo debe ser mayor o igual 0")

        if (peso_cambiar_task < 0):
            raise ValueError(f"peso_cambiar_task debe ser mayor o igual 0")

        if (intentos_maximo <= 0):
            raise ValueError(f"intentos_maximo debe ser mayor a 0")
        
        mutacion = rand.choices(
            ["mover_periodo","cambiar_task"]
            , weights=[peso_mover_periodo,peso_cambiar_task]
            , k=1
        )
        
        array_resultado = self.cromosoma.copy()
        bool_resultado = False
        motivo_resultado = 0
        match mutacion:
            case "mover_periodo":
                if kwargs_mover_periodo is None:
                    kwargs_mover_periodo = dict()
                
                array_resultado, bool_resultado, motivo_resultado = self.mutacion_mover_periodo(**kwargs_mover_periodo)
            case "cambiar_task":
                if kwargs_cambiar_task is None:
                    kwargs_cambiar_task = dict()
                    
                array_resultado, bool_resultado, motivo_resultado = self.mutacion_cambiar_task_mode(**kwargs_cambiar_task)

        if bool_resultado:
            self.cromosoma = array_resultado
        
        return bool_resultado

    def cruce_task_mode(
            self
            , padre : "IndividuoA"
        ) -> tuple["IndividuoA",int]:
        """
        cruce_task_mode - Realiza el cruce con otra instancia de `IndividuoA`
        
        Si el descendiente resulta no ser viable se elige aleatoriamente, con probabilidad
        basada en la aptitud de los ascendientes. Revisa Probabilidad para revisar el calculo.
        
        Algoritmo de cruce:
        1.- Se itera todos los productos y pasos.
        1.1.- Se escoge aleatoriamente un ascediente para agregar un paso de producción.
        1.2.- Si 1.1 falla al no poder agregar el task_mode se selecciona el otro ascediente.
        1.3.- Si 1.2 falla al no poder agregar, ya no se intenta agragar este paso de la receta.
        2.- Se itera nuevamente todos los productos y pasos.
        2.1.- Si el paso para un producto esta asignado, se revisa el siguiente.
        2.2.- Si no esta asignado, se agrega un task mode aleatoriamente. Respentando los periodos de inicio del paso anterior.
        3.- Si el descediente no es viable, se selecciona aleatoriamente la asignacion completa de uno de los ascedientes 
            utilizando la probabilidad en `Probabilidad`.
        
        Probabilidad
        ------------
        * Se calcula la aptitud de madre y padre, a cada una de estas aptitudes se agrega 1 para evitar probabilidad 0.
        * Se calcula p = aptitud / suma_aptitud para cada ascediente.
        * La probabilidad de elegir a cada ascediente es 1-p, esto es para dar más peso al individuo que tenga una aptitud menor.
            Esto funciona porque se tiene p + q = 1 => 2 - (p+q) = 2 - 1 => (1-p) + (1-q) = 1
        
        .. code-block:: python
            aptitud_madre = self.aptitud()
            aptitud_padre = padre.aptitud()
            aptitudes = np.array([aptitud_madre, aptitud_padre])+1 
            probabilidad = 1-aptitudes / aptitudes.sum()
        
        Returns
        -------
        tuple[IndividuoA, int] :
            Una tupla con elementos:
            * 1ro: Un individuo creado a partir de dos ascendientes.
            * 2do: Número que representa el origen del cromosoma, 1 si copia completamente la asignación de esta intancia,
                2 si copia completamente la asignación de `padre`, 3 si es una combinación de los 2 ascedientes.
        
        Raises
        ------
        ValueError :
            Si `padre` no es estancia de `IndividuoA`
        
        ValueError :
            Si en el dataframe asociado a cada individuo. Se encontró un paso de la produccion de un producto
            con 2 o más task asignados.
        """

        if not isinstance(padre, IndividuoA):
            raise ValueError("padre debe ser una instancia de IndividuoA")
        
        df_madre = self.dataframe()
        df_padre = padre.dataframe()
        
        aptitud_madre = self.aptitud()
        aptitud_padre = padre.aptitud()
        #aptitudes = np.array([aptitud_madre, aptitud_padre])+1 
        #probabilidad = 1-aptitudes / aptitudes.sum()

        probabilidad = self.__probabilidades(aptitud_madre, aptitud_padre)

        descendiente = IndividuoA()
        
        diccionario_pasos = dict()
        for producto, demanda in self.datos.iterar_productos():
            receta = self.datos.receta_producto(producto=producto)
            cantidad_pasos = len(receta)
            
            for paso in range(cantidad_pasos):
                diccionario_pasos[(producto,demanda,paso)] = {
                    "origen" : ""
                    , "periodo_inicio" : None
                    , "Maquina" : None
                }
        
        #inicializar
        for key in diccionario_pasos.keys(): #iterar de esta manera mantiene el orden es importante para revisar los pasos
            primero = rand.choices(
                ["madre", "padre"], weights=probabilidad, k=1
            )[0]
            producto_str = str(key[0])
            demanda_str = str(key[1])
            paso_str = str(key[2])
            
            #primer ascendiente
            if primero == "madre":
                fila = df_madre.loc[(df_madre["Producto"] == producto_str) & (df_madre["Demanda"] == demanda_str) & (df_madre["paso"] == paso_str)]
            else:
                fila = df_padre.loc[(df_padre["Producto"] == producto_str) & (df_padre["Demanda"] == demanda_str) & (df_padre["paso"] == paso_str)]
            
            if fila.shape[0] != 1:
                #print(df_padre.loc[df_padre["Producto"] == producto_str])
                #print(df_padre.loc[df_padre["Demanda"] == int(demanda_str)])
                #print(df_padre.loc[df_padre["paso"] == int(paso_str)])
                #print(key,fila)
                raise ValueError(f"Se detectaron varios valores en Producto={producto_str},Demanda={demanda_str},paso={paso_str} en {primero}")
            
            _,_, resultado_bool, _=descendiente.agregar_task_mode(
                maquina=fila.iloc[0]["Maquina"]
                , periodo=fila.iloc[0]["Start"]
                , producto=producto_str
                , paso=paso_str
                , demanda=demanda_str
                , task_mode=fila.iloc[0]["task_mode"]
            )
            
            if resultado_bool:
                diccionario_pasos[key]["origen"] = primero
                diccionario_pasos[key]["periodo_inicio"] = fila.iloc[0]["Start"]
                diccionario_pasos[key]["Maquina"] = fila.iloc[0]["Maquina"]
                continue
            
            #no se pudo agregar, revisando segundo ascendiente
            if primero == "madre":
                fila = df_padre.loc[(df_padre["Producto"] == producto_str) & (df_padre["Demanda"] == demanda_str) & (df_padre["paso"] == paso_str)]
            else:
                fila = df_madre.loc[(df_madre["Producto"] == producto_str) & (df_madre["Demanda"] == demanda_str) & (df_madre["paso"] == paso_str)]
            
            if fila.shape[0] != 1:
                print(key,fila)
                raise ValueError(f"Se detectaron varios valores en Producto={producto_str},Demanda={demanda_str},paso={paso_str} en {primero}")
            
            _,_, resultado_bool, _=descendiente.agregar_task_mode(
                maquina=fila.iloc[0]["Maquina"]
                , periodo=fila.iloc[0]["Start"]
                , producto=producto_str
                , paso=paso_str
                , demanda=demanda_str
                , task_mode=fila.iloc[0]["task_mode"]
            )
            
            if resultado_bool:
                diccionario_pasos[key]["origen"] = "padre" if primero == "madre" else "madre"
                diccionario_pasos[key]["periodo_inicio"] = fila.iloc[0]["Start"]
                diccionario_pasos[key]["Maquina"] = fila.iloc[0]["Maquina"]
                continue
            
        #revisar si falta agregar task modes
        for key in diccionario_pasos.keys(): #iterar de esta manera mantiene el orden es importante para revisar los pasos
            if diccionario_pasos[key]["origen"] != "": #ya se agregó no es necesario revisar este paso
                continue
            
            producto, demanda, paso = key #obtener informacion del producto
            #obtener la información de la receta y del paso
            receta = self.datos.receta_producto(producto=producto)
            dict_task_modes = receta[paso][1]
            
            lista_task_modes = list() #task_modes donde se agregaran las opciones maquina-task_mode
            
            for task_mode in dict_task_modes:
                for maquina in dict_task_modes[task_mode]:
                    lista_task_modes.append((maquina,task_mode))
            
            if len(lista_task_modes) == 0: #si la lista esta vacia salir, no será viable
                break
            
            rand.shuffle(lista_task_modes) #mover aleatoriamente las opciones maquina-task_mode
            
            #intentar agregar cada maquina-task_mode
            for intento in lista_task_modes:
                maquina, task_mode = intento
                periodo_minimo : int = 1 if paso == 0 else diccionario_pasos[(producto,demanda,paso-1)]["periodo_inicio"]
                
                #revisa si se puede agregar el task mode en la maquina
                resultado, periodos_lista = descendiente.revisar_task_mode_en_maquina(
                    maquina=maquina
                    , task_mode=task_mode
                    , inicio=periodo_minimo
                )
                
                if len(periodos_lista) == 0:
                    continue
                
                if not resultado: #no se puede agregar, revisar siguiente opcion
                    continue
            
                #intentar agregar el task_mode
                _,_,resultado_agregar, _ = descendiente.agregar_task_mode(
                    maquina=maquina
                    ,periodo=min(periodos_lista)
                    ,producto=producto
                    ,paso=paso
                    ,demanda=demanda
                    ,task_mode=task_mode
                )
                
                if resultado_agregar:
                    #si se pudo agregar salir del loop de lista_task_modes
                    break
                
                #no se agrego, revisar siguiente intento
                #else:
                    #continue
        
        if descendiente.es_viable()["todo"]["bool"]:
            #el descendiente es viable dar resultado
            return descendiente, 3
        else:
            #el descendiente no es viable, por lo tanto se regresará aleatoriamente uno de los ascedenetes
            primero = rand.choices(
                ["madre", "padre"], weights=probabilidad, k=1
            )[0]
            
            if primero == "madre":
                descendiente.cromosoma = self.cromosoma
                return descendiente, 1
            else:
                descendiente.cromosoma = padre.cromosoma
                return descendiente, 2

    def grafica_gantt(
            self
            , path_save_df : str = ""
            , path_save_fig : str = ""
            , kwargs_to_csv : dict = None
            , kwargs_fig : dict = None
            , kwargs_grafica : dict = None
            , min_value_x : int = None
            , max_value_x : int = None
            , kwargs_suptitle : dict = None
            , kwargs_subtitle : dict = None
            , kwargs_label : dict = None
            , kwargs_ticks : dict = None
            , titulo : str = "Gráfica Gantt de tasks"
        ):
        """
        grafica_gantt - 
        
        Crea una gráfica Gantt del scheduling (self.cromosoma)
        del individuo.
        
        Parameters
        ----------
        path_save_df (str, optional, defaults to "") :
            Ubicación donde se guardará el dataframe en un formato .csv.
            Debe ser una cadena que termine en ".csv" para que se guarde el archivo.
            Si es `""`, no se guardará.
            
        path_save_fig (str, optional, defaults to "") :
            Ubicación donde se guardará la figura de matplotlib en un formato compatible.
            Si es `""`, no se guardará.
        
        kwargs_to_csv (dict, optional, defaults to None) :
            Parametros de `DataFrame.to_csv()`
        
        kwargs_fig (dict, optional, defaults to None) :
            Parametros de matplotlib `savefig`
        
        kwargs_fig (dict, optional, defaults to None) :
            Parametros de grafica_gantt_plt de `graficas.py`
        
        """
        
        if kwargs_to_csv is None:
            kwargs_to_csv = dict()
        
        df = self.dataframe(
            path_save=path_save_df, kwargs_to_csv = kwargs_to_csv
        )
        
        makespan : int = self._IndividuoBase__makespan()
        energia : float = self._IndividuoBase__energia_precio()
        
        if kwargs_fig is None:
            kwargs_fig = dict()
            
        if kwargs_grafica is None:
            kwargs_grafica = dict()
        
        if min_value_x is None:
            min_value_x=min(self.periodos)-1
        
        if max_value_x is None:
            max_value_x=max(self.periodos)+1
        
        grafica_gantt_plt(
            df=df
            , time_leaps=self.cambio_turno
            , min_value_x=min_value_x
            , max_value_x=max_value_x
            , costo_energia=energia
            , makespan=makespan
            , save_path=path_save_fig
            , kwargs_fig=kwargs_fig
            , kwargs_suptitle = kwargs_suptitle
            , kwargs_subtitle=kwargs_subtitle
            , kwargs_label=kwargs_label
            , kwargs_ticks=kwargs_ticks
            , titulo = titulo
            , **kwargs_grafica
        )

    def dataframe(self
            , path_save : str = ""
            , kwargs_to_csv : dict = None
        ) -> pd.DataFrame:
        """
        dataframe - 
        
        Crea un dataframe del cromosoma.
        Si `path_save` es una cadena no vacía que termina en `".csv"`, se guardará el dataframe en esa ubicación.
        Si `path_save` no es una cadena o no termina en `".csv"`, el DataFrame no se guardará y no se lanzará ningún error.
        
        Parameters
        ----------
        path_save (str, optional, defaults to "") :
            Ubicación donde se guardará el dataframe en un formato .csv.
            Debe ser una cadena que termine en ".csv" para que se guarde el archivo.
            Si es `""`, no se guardará.
        
        kwargs_to_csv (dict, optional, defaults to None) :
            Parametros de `DataFrame.to_csv()`
        
        Returns
        -------
        DataFrame :
            DataFrame que tiene la información del individuo.
        
        """
        df = task_array_to_dataframe(
            array=self.cromosoma
        )
        
        if kwargs_to_csv is None:
            kwargs_to_csv = dict()
        
        if str(path_save).endswith(".csv"):
            try:
                df.to_csv(path_save, **kwargs_to_csv)
            except Exception as e:
                print(f"Error guardando DataFrame a csv: {e}")
        
        return df

    def optimizacion_deterministica(self
            , save_path : str = None
        ):
        """
        optimizacion_deterministica - 
        
        Optimiza al individuo reduciendo el periodo todos los task modes
        utilizando `mover_periodo_task_mode` con `completa = True`
        """
        
        df = self.dataframe()
        
        df.sort_values(by="Start", inplace=True)
        
        if save_path is not None:
            df.to_csv(save_path, index=False)
        
        #print(f"optimizacion deterministica")
        #print(f"Aptitud previa {self.aptitud()}")
        for idx, row in df.iterrows():
            
            periodo = int(row["Start"])-1
            maquina = str(row["Maquina"])
            
            _, _, resultado, array_modificado = self.mover_periodo_task_mode(
                maquina=maquina
                , periodo=periodo
                , tipo_movimiento=-1
                , completa=True
            )
            
            if resultado:
                self.cromosoma = array_modificado
        
        #print(f"Aptitud despues {self.aptitud()}")

    def __probabilidades(
            self
            , aptitud_1 : float
            , aptitud_2 : float
        ) -> tuple[float, float]:
        
        #promedio = (aptitud_1 + aptitud_2) / 2
        #valores = [(aptitud_1 + 1) / promedio, (aptitud_2 + 1) / promedio]
        #probabilidad = np.exp(valores) / sum(np.exp(valores)) #softmax
        
        aptitudes = np.array([aptitud_1, aptitud_2])+1 
        probabilidad = 1-aptitudes / aptitudes.sum()
        
        return probabilidad[0], probabilidad[1]

    def cruce_time_leap(
            self
            , padre : "IndividuoA"
        ) -> tuple["IndividuoA",int]:
        """
        cruce_time_leap - Realiza el cruce con otra instancia de `IndividuoA`
        
        Si el descendiente resulta no ser viable se elige aleatoriamente, con probabilidad
        basada en la aptitud de los ascendientes. Revisa Probabilidad para revisar el calculo.
        
        Algoritmo de cruce:
        1.- Se itera todos los "turnos laborales" limitados por los periodos en `time_leap`, y en cada conjunto de 
            periodos se iteran todas las máquinas.
        1.1.- Se escoge aleatoriamente un ascediente para agregar los task modes en el turno.
        1.2.- Si una combinación de producto-demanda-paso ya se ha agregado anteriormente no se agrega al descendiente.
        2.- Se itera nuevamente todos los productos y pasos.
        2.1.- Si el paso para un producto esta asignado, se revisa el siguiente.
        2.2.- Si no esta asignado, se agrega un task mode aleatoriamente. Respentando los periodos de inicio del paso anterior.
        3.- Si el descediente no es viable, se selecciona aleatoriamente la asignacion completa de uno de los ascedientes 
            utilizando la probabilidad en `Probabilidad`.
        
        Probabilidad
        ------------
        * Se calcula en base de la aptitud de madre y padre, utilizando la funcion en `self.__probabilidad()`
        
        Returns
        -------
        tuple[IndividuoA,int] :
            Una tupla con elementos:
            * 1ro: Un individuo creado a partir de dos ascendientes.
            * 2do: Número que representa el origen del cromosoma, 1 si copia completamente la asignación de esta intancia,
                2 si copia completamente la asignación de `padre`, 3 si es una combinación de los 2 ascedientes.
        
        Raises
        ------
        ValueError :
            Si `padre` no es estancia de `IndividuoA`
        
        """
        
        if not isinstance(padre, IndividuoA):
            raise ValueError("padre debe ser una instancia de IndividuoA")

        #calcular lista de cortes
        periodos_time_leap : list[int] = self.datos.time['time_leap']
        # lista: lista de límites superiores, p.ej. [192,384,576,768,960]
        lista_inicio : list[int] = [1] + [x + 1 for x in periodos_time_leap]
        # calcular paso para extender el último intervalo (si hay al menos 2 elementos)
        last_step = (periodos_time_leap[1] - periodos_time_leap[0]) if len(periodos_time_leap) >= 2 else periodos_time_leap[0]
        lista_final : list[int] = periodos_time_leap + [periodos_time_leap[-1] + last_step]
        
        lista_opciones : list[tuple[str,int,int]] = list()
        for i in range(len(lista_inicio)):
            for maquina in self.maquinas:
                lista_opciones.append((maquina,lista_inicio[i],lista_final[i]))

        #calcular probabilidades
        df_madre = self.dataframe()
        df_padre = padre.dataframe()
        
        aptitud_madre = self.aptitud()
        aptitud_padre = padre.aptitud()

        probabilidad = self.__probabilidades(aptitud_madre, aptitud_padre)

        #crear descendiente sin inicializar
        descendiente = IndividuoA()

        dict_pasos = dict()
        
        for producto, demanda in self.datos.iterar_productos():
            receta = self.datos.receta_producto(producto=producto)
            for paso in range(len(receta)):
                dict_pasos[(producto,demanda,paso)] = {
                    "periodo_inicio" : None
                    , "maquina" : None
                }
        
        def revisa_paso(producto_input,demanda_input,paso_input):
            """revisa si ya se agregó este paso"""
            periodo = dict_pasos[(producto_input,demanda_input,paso_input)]["periodo_inicio"]
            
            if periodo is not None:
                return True
            else:
                return False
        
        def agregar_paso(
                maquina_input,periodo_input,producto_input,paso_input,demanda_input,task_mode_input
            ):
            """agrega el paso"""
            _,_, bool_resultado, _ = descendiente.agregar_task_mode(
                maquina=maquina_input
                ,periodo=periodo_input
                ,producto=producto_input
                ,paso=paso_input
                ,demanda=demanda_input
                ,task_mode=task_mode_input
            )
                    
            if bool_resultado:
                dict_pasos[(producto_input,demanda_input,paso_input)] = {
                    "periodo_inicio" : periodo_input
                    , "maquina" : maquina_input
                }
            
            return bool_resultado
        
        #itera entre todos los turnos y todas las maquinas
        for i in range(len(lista_opciones)):
            opcion_time_leap: tuple[str, int, int] = lista_opciones[i]
            #print(f"revisando turno {opcion_time_leap}")
            
            #escoger ascendiente del time leap
            ascendiente = rand.choices(
                ["madre", "padre"], weights=probabilidad, k=1
            )[0]
            
            maquina, periodo_inicio, periodo_final = opcion_time_leap
            
            #datos ascendiente
            if ascendiente == "madre":
                df_time_leap = df_padre.loc[(df_padre["Maquina"] == maquina) & (df_padre["Start"] >= periodo_inicio) & (df_padre["Start"] <= periodo_final)]
            else:
                df_time_leap = df_madre.loc[(df_madre["Maquina"] == maquina) & (df_madre["Start"] >= periodo_inicio) & (df_madre["Start"] <= periodo_final)]

            for _, fila in df_time_leap.iterrows():
                maquina_fila = fila["Maquina"]
                periodo_inicio_fila = int(fila["Start"])
                producto_fila = str(fila["Producto"])
                demanda_fila = int(fila["Demanda"])
                paso_fila = int(fila["paso"])
                task_mode_fila = str(fila["task_mode"])
                
                #aun no se ha agregado este producto
                if not revisa_paso(producto_input=producto_fila,demanda_input=demanda_fila,paso_input=paso_fila):
                    agregar_paso(
                        maquina_input=maquina_fila
                        , periodo_input=periodo_inicio_fila
                        , producto_input=producto_fila
                        , paso_input=paso_fila
                        , demanda_input=demanda_fila
                        , task_mode_input=task_mode_fila
                    )
        
        #revisar si falta agregar task modes
        for key in dict_pasos.keys(): #iterar de esta manera mantiene el orden es importante para revisar los pasos
            if dict_pasos[key]["periodo_inicio"] is not None: #ya se agregó no es necesario revisar este paso
                continue
            
            producto, demanda, paso = key #obtener informacion del producto
            #obtener la información de la receta y del paso
            receta = self.datos.receta_producto(producto=producto)
            dict_task_modes = receta[paso][1]
            
            lista_task_modes = list() #task_modes donde se agregaran las opciones maquina-task_mode
            
            for task_mode in dict_task_modes:
                for maquina in dict_task_modes[task_mode]:
                    lista_task_modes.append((maquina,task_mode))
            
            if len(lista_task_modes) == 0: #si la lista esta vacia salir, no será viable
                break
            
            rand.shuffle(lista_task_modes) #mover aleatoriamente las opciones maquina-task_mode
            
            #intentar agregar cada maquina-task_mode
            for intento in lista_task_modes:
                maquina, task_mode = intento
                periodo_minimo : int = 1 if paso == 0 else dict_pasos[(producto,demanda,paso-1)]["periodo_inicio"]
                
                #revisa si se puede agregar el task mode en la maquina
                resultado, periodos_lista = descendiente.revisar_task_mode_en_maquina(
                    maquina=maquina
                    , task_mode=task_mode
                    , inicio=periodo_minimo
                )
                
                if len(periodos_lista) == 0:
                    continue
                
                if not resultado: #no se puede agregar, revisar siguiente opcion
                    continue
            
                #intentar agregar el task_mode
                _,_,resultado_agregar, _ = descendiente.agregar_task_mode(
                    maquina=maquina
                    ,periodo=min(periodos_lista)
                    ,producto=producto
                    ,paso=paso
                    ,demanda=demanda
                    ,task_mode=task_mode
                )
                
                if resultado_agregar:
                    #si se pudo agregar salir del loop de lista_task_modes
                    break
                
                #no se agrego, revisar siguiente intento
                #else:
                    #continue
        
        if descendiente.es_viable()["todo"]["bool"]:
            #el descendiente es viable dar resultado
            return descendiente, 3
        else:
            #el descendiente no es viable, por lo tanto se regresará aleatoriamente uno de los ascedenetes
            primero = rand.choices(
                ["madre", "padre"], weights=probabilidad, k=1
            )[0]
            
            if primero == "madre":
                descendiente.cromosoma = self.cromosoma
                return descendiente, 1
            else:
                descendiente.cromosoma = padre.cromosoma
                return descendiente, 2           

