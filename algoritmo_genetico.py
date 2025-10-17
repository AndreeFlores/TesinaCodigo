import pandas as pd
from Carga_Datos import Datos, PATH_INPUT, task_mode_a_str, str_a_task_mode
import numpy as np
from typing import Any, Literal
import random as rand
from graficas import task_array_to_dataframe, grafica_gantt_plt, dataframe_to_array
import os

class IndividuoBase:
    
    def __init__(self):
        
        self.datos = Datos(PATH_INPUT)
        
        self.maquinas = self.datos.machines_id
        
        self.periodos : list[int] = self.datos.periodos
        
        self.energia_solar_cantidad = np.zeros(
            (len(self.periodos))
        )
        
        self.energia_socket_precio = np.zeros(
            (len(self.periodos))
        )
        
        for periodo in self.periodos:
            solar_cantidad = self.datos.energy[periodo]['Solar']['amount']
            socket_precio = self.datos.energy[periodo]['Socket Energy']['price']
            
            self.energia_solar_cantidad[periodo - 1] = solar_cantidad
            self.energia_socket_precio[periodo - 1] = socket_precio
        
        self.task_mode_energy = dict()
        for _, task_dict in self.datos.tasks.items():
            for task_mode, energy in task_dict.items():
                self.task_mode_energy[task_mode] = energy['power']
        
        self.cromosoma = np.full(
            shape = (len(self.maquinas.keys()), len(self.periodos)),
            fill_value = "",
            dtype = 'object'
        )
        
        self.cambio_turno : list[int] = self.datos.time['time_leap']
    
    def __modificar_array(self
            , array : np.ndarray
            , maquina : str
            , periodo : int
            , valor : Any
        ) -> np.ndarray[tuple[Any, ...], np.dtype[Any]]:
        """
        __modificar_array - 
        
        Modifica un `ndarray` en la posición `[maquina, periodo]`
        con la variable `valor` dada.
        
        Parameters
        ----------
        array (np.ndarray) :
            Array a modificar.
        
        maquina (str) :
            Maquina donde se modificará el array
        
        periodo (int) :
            Periodo donde se modificará el array
        
        valor (Any) :
            Valor que se cambiará en el array
        
        Returns
        -------
        array :
            Una copia del array `array` modificado
        
        Raises
        ------
        ValueError :
            Si `maquina` no es uno de `["MAQ118", "MAQ119", "MAQ120"]`
        
        ValueError :
            Si periodo no es un periodo existente.
        
        TypeError :
            Si `array` no es `np.ndarray`
        
        """
        
        if maquina not in self.maquinas:
            raise ValueError(f'La maquina {maquina} no esta disponible')
        
        if periodo not in self.periodos:
            raise ValueError(f'Periodo {periodo} no es válido')
    
        if not isinstance(array, np.ndarray):
            raise TypeError(f'array no es de la clase correcta')
    
        array[self.maquinas[maquina], periodo - 1] = valor
        
        return array.copy()
    
    def __es_vacio_array(self
            , maquina : str
            , periodo : int
            , array : np.ndarray = None
        )  -> bool:
        """
        __es_vacio_array - 
        
        Revisa si la posicion `[maquina, periodo]` del `array`
        tiene es vacio, se consideran vacios los siguientes valores:
        * `False`
        * `0`
        * `""`
        
        Parameters
        ----------
        maquina (str) :
            Maquina donde se revisará el array
        
        periodo (int) :
            Periodo donde se modificará el array
            
        array (np.ndarray, optional, defaults to None) :
            Array a analizar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        bool :
            * `True` si es vacio
            * `False` si tiene un valor
        """
        if array is None:
            array = self.cromosoma
        
        valor = array[self.maquinas[maquina], periodo - 1]
        
        return not valor
    
    def __gen(self
            , producto : str
            , demanda : int
            , task_mode : str
            , intervalo : int
            , paso : int
            , sep : str = "|"
        ) -> str:
        """
        __gen - 
        
        Crea el valor del gen para la información dado.
        
        Parameters
        ----------
        producto (str) :
            Producto procesado.
        
        demanda (int) :
            Número de demanda del producto.
        
        task_mode (str) :
            task_mode del producto procesado.
        
        intervalo (int) :
            Uno de los intervalos del task_mode.
        
        paso (int) :
            Paso de la receta de producción del producto.
        
        sep (str, optional, defaults to "|") :
            Separador, que separa la información del gen.
        
        Returns
        -------
        str :
            El valor del gen el cual contiene toda la información.
        
        """
        return task_mode_a_str(
            producto=producto
            , demanda=demanda
            , task_mode=task_mode
            , intervalo=intervalo
            , paso=paso
            , sep=sep
        )
    
    def __gen_inverso(
            self
            , gen : str
            , sep : str = "|"
        )  -> tuple[str, int, str, int, int]:
        """
        __gen_inverso - 
        
        Obtiene la información guardada en el gen dado.
        
        Parameters
        ----------
        gen (str) :
            El valor del gen.
        
        sep (str, optional, defaults to "|") :
            El separador utilizado para guardar la información en el gen.
        
        Returns
        -------
        tuple[str, int, str, int] :
            Tuple con los siguientes elementos:
            * Producto
            * Demanda
            * task_mode
            * intervalo
            * paso
        
        """
        
        #print("__gen_inverso",gen) #TODO agregar verbose
        
        return str_a_task_mode(
            info=gen
            , sep=sep
        )
    
    def __makespan(self
            , array : np.ndarray = None
        ) -> int:
        """
        __makespan - 
        
        Calcula el `makespan` del individuo
        
        Parameters
        ----------
        array (np.ndarray, optional, defaults to None) :
            Array a analizar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        int :
            Valor que representa el ultimo periodo activo
            es decir el `makespan`
        
        """
        if array is None:
            array = self.cromosoma
        
        produccion : np.ndarray = np.apply_along_axis(np.any, 0, array != "")
        
        hay_produccion_indices = np.where(produccion)[0]
        
        if hay_produccion_indices.size > 0:
            return hay_produccion_indices[-1] + 1
        else:
            return 0
    
    def __gen_a_energia_utilizada(
            self
            , gen : str
            , sep : str = "|"
        ) -> float:
        """
        __gen_a_energia_utilizada - 
        
        Regresa la cantidad de energia utilizada para le gen dado.
        
        Parameters
        ----------
        gen (str) :
            El valor del gen.
        
        sep (str, optional, defaults to "|") :
            El separador utilizado para guardar la información en el gen.
        
        Returns
        -------
        float :
            * 0 si la maquina no es utilizada
            * La cantidad de energia utilizada si la maquina es utilizada
        
        """
        
        if gen == "":
            return 0
        else:
            _, _, task_mode, intervalo, _ = self.__gen_inverso(
                gen=gen, sep=sep
            )
            return self.task_mode_energy[task_mode][intervalo]
    
    def __energia_precio(self
            , array : np.ndarray = None
            , save : bool = False
        ) -> float:
        """
        __energia_precio - 
        
        Calcula el precio de la energia total del individuo
        
        Parameters
        ----------
        array (np.ndarray, optional, defaults to None) :
            Array a analizar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        float :
            El precio total de la energia de todas las actividades en todos los periodos
        
        """
        if array is None:
            array = self.cromosoma

        if save:
            np.savetxt(
                "cromosoma.csv", array, delimiter=",", fmt="%s"
                , encoding="utf-8"
            )

        energia_utilizada : np.ndarray = np.array(
            [[self.__gen_a_energia_utilizada(i) for i in row] for row in array]
        ).sum(axis=0)
        
        if save:
            np.savetxt(
                "energia_utilizada.csv", energia_utilizada, delimiter=","
            )
        
        if save:
            np.savetxt(
                "energia_solar_cantidad.csv", self.energia_solar_cantidad, delimiter=","
            )
        
        energia_socket = np.maximum(energia_utilizada - self.energia_solar_cantidad, 0)
        
        if save:
            np.savetxt(
                "energia_socket.csv", energia_socket, delimiter=","
            )
        
        if save:
            np.savetxt(
                "energia_socket_precio.csv", self.energia_socket_precio, delimiter=","
            )
        
        return np.dot(energia_socket, self.energia_socket_precio)

    def aptitud(
            self
            , peso_makespan : float = 1
            , peso_energia : float = 1
            , array : np.ndarray = None
        ) -> float:
        """
        aptitud - 
        
        Calcula la aptitud del individuo.
        
        Parameters
        ----------
        peso_makespan (float, optional, defaults to 1) :
            El peso que se considera para el `makespan`.
            Debe ser mayor o igual a 0.
        
        peso_energia (float, optional, defaults to 1) :
            El peso que se considera para el `precio de la energia`.
            Debe ser mayor o igual a 0.
        
        array (np.ndarray, optional, defaults to None) :
            Array a analizar.
            Si es None se utiliza `self.cromosoma`
        
        La suma de peso_makespan y peso_energia debe ser mayor a 0.
        
        Returns
        -------
        float :
            La aptitud del individuo
        
        Raises
        ------
        ValueError :
            Si los pesos no son correctos
        
        """
        
        if peso_makespan < 0:
            raise ValueError(f"peso_makespan debe ser mayor o igual a 0")
        if peso_energia < 0:
            raise ValueError(f"peso_energia debe ser mayor o igual a 0")
        if peso_energia + peso_energia <= 0:
            raise ValueError(f"peso_energia + peso_makespan debe ser mayor a 0")
        
        if array is None:
            array = self.cromosoma
        
        makespan = self.__makespan(array=array)
        precio_energia = self.__energia_precio(array=array)
        
        return (peso_makespan * makespan + peso_energia * precio_energia) / (peso_energia + peso_makespan)
    
    def __revisar_cambio_turno(
            self
            , array : np.ndarray = None
        ) -> tuple[bool, list[dict[str,str|int]]]:
        """
        __revisar_cambio_turno - 
        
        Revisa si un task se procesa durante un cambio de turno.
        
        No se puede iniciar y terminar un task durante distintos turnos,
        todos los task se tienen que terminar en el mismo turno que se inicia.
        
        Además se regresa una lista donde se encuentran los errores
        que se deben cambiar.
        
        Parameters
        ----------
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[bool, list[dict[str,str|int]]] :
            1er elemento: un bool si se cumple o no esta condición. 
            
            2do elemento: lista con los errores a cambiar donde cada elemento es un dict.
                El dict tiene como llaves los siguientes elementos: ["producto", "demanda", "task_mode", "paso", "periodo", "maquina]
                el cual tiene el valor correspondiente.
        
        """
        if array is None:
            array = self.cromosoma

        resultado = True
        lista_errores = list()

        for periodo in self.cambio_turno:
            for maquina, maquina_pos in self.maquinas.items():
                array_a_revisar = array[maquina_pos, [periodo-1, periodo]]
                
                antes : str = array_a_revisar[0]
                despues : str = array_a_revisar[1]
                
                #si un periodo es vacio entonces no importa si el otro periodo esta ocupado
                if (antes == "") or (despues == ""):
                    continue
                    
                producto_antes, demanda_antes, task_mode_antes, _, paso_antes =self.__gen_inverso(
                    gen = antes
                )
                
                producto_despues, demanda_despues, task_mode_despues, _, paso_despues =self.__gen_inverso(
                    gen = despues
                )
                
                #mismo producto
                if (producto_antes == producto_despues) \
                    and (demanda_antes == demanda_despues) \
                    and (task_mode_antes == task_mode_despues) \
                    and (paso_antes == paso_despues):
                    
                    #con solo un proceso que pase el cambio de turno, ya no es viable
                    resultado = False
                    
                    lista_errores.append(
                        {
                            "producto" : producto_antes
                            , "demanda" : demanda_antes
                            , "task_mode" : task_mode_antes
                            , "paso" : paso_antes
                            , "periodo" : periodo
                            , "maquina" : maquina
                        }
                    )

        return resultado, lista_errores
    
    def __revisar_produccion_completa(
            self
            , array : np.ndarray = None
        ) -> tuple[bool, list[dict[str,str|int]]]:
        """
        __revisar_produccion_completa - 
        
        Revisa si se cumple las condiciones de producción:
        * El deadline del producto si tiene.
        * Si el producto es procesado por todos los pasos
        
        Parameters
        ----------
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[bool, list[dict[str,str|int]]] :
            1er elemento: un bool si se cumple o no esta condición. 
            
            2do elemento: lista con los errores a cambiar donde cada elemento es un dict.
        
        """
        if array is None:
            array = self.cromosoma
            
        resultado = True
        revisar_list = list()
        revisar_dict = dict()
        
        for producto, demanda in self.datos.iterar_productos():
            if producto not in revisar_dict:
                revisar_dict[producto] = dict()

            if demanda not in revisar_dict[producto]:
                revisar_dict[producto][demanda] = dict()
                
                revisar_dict[producto][demanda]["receta"] = dict()
        
        #iterar en todos los genes
        for periodo in self.periodos:
            for maquina, maquina_pos in self.maquinas.items():
                elemento = array[maquina_pos , periodo - 1]
            
                if elemento == "":
                    continue
                
                producto, demanda, task_mode, intervalo, paso= self.__gen_inverso(
                    gen = elemento
                )
                
                #si no esta el dict de paso se agrega
                if paso not in revisar_dict[producto][demanda]["receta"]:
                    revisar_dict[producto][demanda]["receta"][paso] = dict()
                    periodo_guardado = 0 #si no se tiene guardado un periodo se regresa 0
                else:
                    periodo_guardado = revisar_dict[producto][demanda]["receta"][paso]["periodo_final"]
                
                #se guarda el ultimo periodo donde se realiza el task_mode, es utilizado
                #en la revisión del deadline
                revisar_dict[producto][demanda]["receta"][paso] = {
                    "maquina" : maquina
                    , "task_mode" : task_mode
                    , "periodo_final" : max(periodo, periodo_guardado)
                }
        
        #iterar deadlines
        for producto, demanda, deadline in self.datos.iterar_deadlines():
            revisar_dict[producto][demanda]["deadline"] = deadline
        
        #iterar para revisar si se cumple produccion
        for producto in revisar_dict:
            receta = self.datos.receta_producto(producto=producto)
            ultimo_paso = len(receta)
            
            for demanda in revisar_dict[producto]:
                deadline = np.inf
                
                #revisar deadline
                if "deadline" in revisar_dict[producto][demanda]:
                    deadline = revisar_dict[producto][demanda]["deadline"]
                
                if ultimo_paso in revisar_dict[producto][demanda]["receta"]:
                    if revisar_dict[producto][demanda]["receta"][ultimo_paso]["periodo_final"] > deadline:
                        resultado = False
                        revisar_list.append(
                            {
                                "tipo" : "deadline"
                                , "producto" : producto
                                , "demanda" : demanda
                                , "maquina" : revisar_dict[producto][demanda]["receta"][ultimo_paso]["maquina"]
                                , "periodo_final_task_mode" : revisar_dict[producto][demanda]["receta"][ultimo_paso]["periodo_final"]
                                , "periodo_deadline" : deadline
                            }
                        )
                
                #revisar que se procesen todos los pasos en orden
                dict_revisar_produccion = {
                    "tipo" : "produccion"
                    , "producto" : producto
                    , "demanda" : demanda
                    , "pasos_orden" : list()
                    , "pasos_orden_bool" : True
                    , "pasos_faltan" : list()
                    , "pasos_faltan_bool" : True
                }
                
                for paso in range(len(receta)):
                    if paso not in revisar_dict[producto][demanda]["receta"]:
                        resultado = False
                        dict_revisar_produccion["pasos_faltan"].append(
                            paso
                        )
                        dict_revisar_produccion["pasos_faltan_bool"] = False
                    else:
                        dict_revisar_produccion["pasos_orden"].append(
                            {
                                "paso" : paso
                                , "periodo_final" : revisar_dict[producto][demanda]["receta"][paso]["periodo_final"]
                            }
                        )
                
                lista_orden = list()
                for paso in dict_revisar_produccion["pasos_orden"]:
                    lista_orden.append(paso["paso"])
                
                dict_revisar_produccion["pasos_orden_bool"] = all(lista_orden[i] < lista_orden[i+1] for i in range(len(lista_orden) - 1))
        
                #si no se cumple el orden
                if not dict_revisar_produccion["pasos_orden_bool"]:
                    resultado = False
                
                    revisar_list.append(
                        dict_revisar_produccion
                    )    
        
        return resultado, revisar_list

    def es_viable(
            self
            , array : np.ndarray = None
        ) -> dict:
        """
        es_viable - 
        
        Revisa si el array dado es viable.
        
        Parameters
        ----------
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        dict :
            Diccionario con los cambios necesarios
            
        .. code-block:: python
            {
                'todo' : {
                    'bool' : bool_si_el_individuo_es_viable
                }
                , 'cambio_turno' : {
                    'bool' : bool_si_cumple_el_cambio_turno
                    , 'lista' : lista_con_los_cambios_necesarios
                }
                , 'produccion' : {
                    'boo' : bool_si_cumple_la_produccion
                    , 'lista' : lista_con_los_cambios_necesarios
                }
            }
            
        """
        if array is None:
            array = self.cromosoma
        
        es_viable_cambio_turno_bool, es_viable_cambio_turno_lista= self.__revisar_cambio_turno(array)
        es_viable_produccion_completa_bool, es_viable_produccion_completa_lista = self.__revisar_produccion_completa(array)
        
        return {
            "todo" : {
                "bool" : all([es_viable_cambio_turno_bool, es_viable_produccion_completa_bool])
            }
            , "cambio_turno" : {
                "bool" : es_viable_cambio_turno_bool
                , "lista" : es_viable_cambio_turno_lista
            }
            , "produccion" : {
                "bool" : es_viable_produccion_completa_bool
                , "lista" : es_viable_produccion_completa_lista
            }
        }
    
    def agregar_task_mode(
            self
            , maquina : str
            , periodo : int
            , producto : str
            , paso : int
            , demanda : int
            , task_mode : str
            , array : np.ndarray = None
        ) -> tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]]:
        """
        agregar_task_mode - 
        
        Agrega un task_mode en el array
        en la `maquina` y `periodo` dado.
        
        Parameters
        ----------
        maquina (str) :
            Maquina donde se agregará el task_mode.
        
        periodo (int) :
            El periodo donde se inicia el task_mode, se llena
            todos los periodos necesarios para tener todos los
            intervalos activos.
        
        producto (str) :
            El producto que el task_mode procesará
        
        paso (int) :
            Número de paso de la receta de producción del producto
        
        demanda (int) :
            El número demandado del producto que el task_mode procesará
        
        task_mode (str) :
            El task_mode a implementar
            
        array (np.ndarray, optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
            Tupla con los siguientes elementos:
            * Maquina donde se ubica el task_mode agregado
            * Periodo donde se inicia el task_mode agregado
            * `True` si se agregó el task_mode, o `False` si no se agregó el task_mode
            * Una copia del array `array` modificado, si no hubo modificacion se regresa una copia del array original
        
        """
        if array is None:
            array = self.cromosoma
        
        intervalos = self.datos.intervalos(task_mode=task_mode)
        
        es_viable : True
        #revisar si es viable agregar el task_mode
        for i in range(len(intervalos)):
            es_viable = self.__es_vacio_array(
                array = array
                , maquina = maquina
                , periodo = periodo+i
            )
            
            #no es viable, un periodo ya esta ocupado
            if not es_viable:
                return maquina, periodo, False, array.copy()
        
        #es viable, por lo tanto se agrega el task_mode
        for i in range(len(intervalos)):
            
            gen = self.__gen(
                    producto = producto
                    , demanda = demanda
                    , task_mode = task_mode
                    , intervalo = i
                    , paso = paso
                )
            
            #print("gen a agregar:",gen) #TODO agregar verbose
            
            array_modificado = self.__modificar_array(
                array
                , maquina = maquina
                , periodo = periodo + i
                , valor = gen
            )
        
        #print("agregar_task_mode resultado",array_modificado) #TODO agregar verbose
        
        #se agrego el task mode exitosamente
        return maquina, periodo, True, array_modificado

    def __buscar_inicio_task_mode(
            self
            , maquina : str
            , periodo : int
            , array : np.ndarray = None
        ) -> tuple[str, int]:
        """
        __buscar_inicio_task_mode - 
        
        Busca la posicion donde se encuentra el inicio del task_mode
        de la posición dada.
        
        En caso que no esta activo se regresa la posición 
        de los parametros.
        
        Parameters
        ----------
        maquina (str) :
            Maquina a revisar
        
        periodo (int) :
            Periodo a revisar
            
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[str, int] :
            Tupla con los siguientes elementos:
            1. maquina revisada
            2. periodo inicial si se encuentra activo en caso 
                contrario se regresa `periodo` de los parametros
        
        """
        if array is None:
            array = self.cromosoma
        
        gen = array[self.maquinas[maquina], periodo - 1]
        
        #es vacio por lo tanto no tiene inicio
        if gen == "":
            return maquina, periodo
        
        _, _, _, intervalo, _ = self.__gen_inverso(
            gen=gen
        )
        
        return maquina, periodo - intervalo
    
    def remover_task_mode(
            self
            , maquina : str
            , periodo : int
            , array : np.ndarray = None
        ) -> tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]]:
        """
        remover_task_mode - 
        
        Elimina el task mode ubicado en `[maquina,periodo]`
        
        Esta funcion busca el inicio del task_mode para
        empezar a eliminar el task_mode.
        
        En caso de que la posición dada no se realiza un proceso, la funcion hace nada.
        
        Parameters
        ----------
        maquina (str) :
            Maquina donde se realiza el task_mode
        
        periodo (int) :
            Periodo donde se realiza el task_mode
            
        array (np.ndarray, optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
            Tupla con los siguientes elementos:
            * Maquina donde se ubica el task_mode eliminado
            * Periodo donde se inicia el task_mode eliminado
            * `True` si se eliminó el task_mode, o `False` si no había task_mode a eliminar
            * Una copia del array `array` modificado, si no hubo modificacion se regresa una copia del array original
        
        """
        if array is None:
            array = self.cromosoma
        
        gen = array[self.maquinas[maquina], periodo - 1]
        #es vacio por lo tanto no se puede borrar
        if gen == "":
            return maquina, periodo, False, array.copy()
        
        
        maquina, periodo = self.__buscar_inicio_task_mode(
            maquina=maquina, periodo=periodo, array=array
        )
        
        _, _, task_mode, _, _ = self.__gen_inverso(
            gen=gen
        )
        
        intervalos = self.datos.intervalos(task_mode=task_mode)
        
        for i in range(len(intervalos)):    
            array_modificado = self.__modificar_array(
                array=array
                , maquina = maquina
                , periodo = periodo + i
                , valor = ""
            )
        
        return maquina, periodo, True, array_modificado

    def revisar_task_mode_en_maquina(
            self
            , maquina : str
            , task_mode : str
            , array : np.ndarray = None
            , inicio : int = None
            , termina : int = None
        ) -> tuple[bool, list[int]]:
        """
        revisar_task_mode_en_maquina - 
        
        Revisa si es posible agregar un task_mode en el
        scheduling de la maquina.
        
        Se regresa si es posible agregar o no por motivos
        de la configuracion de la maquina.
        
        Y regresa los periodos donde es posible agregar el task_mode.
        
        Parameters
        ----------
        maquina (str) :
            Maquina donde se realiza el task_mode
        
        task_mode (str) :
            task_mode a revisar
        
        array (np.ndarray, optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        inicio (int, optional, defaults to None) :
            Periodo inicial que se revisará.
            Si None se selecciona el primer periodo de los datos
        
        termina (int, optional, defaults to None) :
            Periodo final que se revisará.
            Si None se selecciona el ultimo periodo de los datos
        
        Returns
        -------
        tuple[bool, list[int]] :
            Posibles resultados:
            * `False, list()` no es posible agregar por la configuración de la maquina
            * `True, list()` es posible agrega el task_mode en las siguientes posiciones,
                la lista puede ser vacia y quiere decir si es posible agregar el task_mode
                pero no se encontró un espacio disponible adecuado

        """

        #revisa si la maquina puede procesar el task_mode:
        if task_mode not in self.datos.machines[maquina]:
            return False, list()

        #revisa si es posible agregar el task_mode en la maquina
        if array is None:
            array = self.cromosoma
        
        #se llena elementos temporales para evitar agregar un task en diferentes time leaps
        array = array.copy()
        for periodo in self.datos.time['time_leap']:
            array[:,periodo-1] = "a"
        
        intervalos : int = len(self.datos.intervalos(task_mode=task_mode))
        
        posiciones = list()
        #for periodo in self.periodos:
        #    if all(array[self.maquinas[maquina],periodo - 1 + i] == "" for i in range(intervalos)):
        #        posiciones.append(periodo)
        if inicio is None:
            inicio = min(self.periodos)
        
        if termina is None:
            termina = max(self.periodos)
        
        for periodo in range(inicio, termina - intervalos + 1):
            if all(array[self.maquinas[maquina],periodo - 1 + i] == "" for i in range(intervalos)):
                posiciones.append(periodo)

        return True, posiciones
    
    def __mover_periodo_task_mode(
            self
            , maquina : str
            , periodo : int
            , tipo_movimiento : Literal[-1,1] = -1
            , completa : bool = True
            , array : np.ndarray = None
        ) -> tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
        """
        __mover_periodo_task_mode - 
        
        Mueve el task_mode a traves del periodo, 
        dentro del scheduling de la maquina.
        
        Parameters
        ----------
        maquina (str) :
            Máquina a revisar.
        
        periodo (int) :
            Periodo a inicial a revisar.
        
        tipo_movimiento (Literal[-1,1], optional, defaults to -1) :
            Como se moverá el gen:
            * `-1` disminuyendo el periodo
            * `1` aumentando el periodo
        
        completa (bool, optional, defaults to True) :
            * `True` para mover hasta "chocar" con otro gen
            * `False` para mover solo un periodo
            
        array (np.ndarray, optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[str, int, bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
            Tupla con los siguientes elementos:
            * Maquina donde se ubica el task_mode eliminado
            * Periodo donde se inicia el task_mode eliminado
            * `True` si se movió el task_mode, o `False` si no se movió el task_mode
            * Una copia del array `array` modificado, si no hubo modificacion se regresa una copia del array original
        """
        
        if tipo_movimiento not in [-1,1]:
            raise ValueError(f'Tipo de movimiento no válido')
        
        if array is None:
            array = self.cromosoma

        array_cambiado = array.copy()
        array_revisar = array.copy()
        
        gen = array_revisar[self.maquinas[maquina], periodo - 1]
        #es vacio por lo tanto no se puede mover
        if gen == "":
            return maquina, periodo, False, array_revisar
        
        #busca el inicio del task_mode
        maquina, periodo = self.__buscar_inicio_task_mode(
            maquina=maquina
            , periodo=periodo
            , array=array
        )
        
        producto, demanda, task_mode, _, paso = self.__gen_inverso(
            gen=gen
        )
        
        #si el tipo de moviento es -1 se busca a la izquierda este ajuste es 0
        #si el tipo de movimiento es 1 se busca a la derecha este ajuste es igual a la cantidad
        #de intervalos en el task_mode
        intervalos : int = len(self.datos.intervalos(task_mode=task_mode))
        ajuste_intervalo = 0 if tipo_movimiento == -1 else intervalos
        
        es_viable = True
        while es_viable:
            #calcula el periodo a revisar
            periodo_revisar = periodo + tipo_movimiento + ajuste_intervalo
            #no se puede revisar un periodo que no existe
            if periodo_revisar not in self.periodos:
                break

            disponible = self.__es_vacio_array(
                array=array_revisar
                , maquina=maquina
                , periodo=periodo_revisar
            )
            
            #no hay espacio disponible para mover
            if not disponible:
                break
            
            #si es posible mover el task_mode 
            #remover task_mode
            _, _, actualizado, array_revisar = self.remover_task_mode(
                maquina=maquina
                , periodo=periodo
                , array=array_revisar
            )
            
            if not actualizado:
                raise ValueError(f"Error al remover el task_mode {task_mode} en periodo = {periodo}, maquina = {maquina}")
            
            #agregar task_mode en nueva posicion
            _, _ , actualizado, array_revisar = self.agregar_task_mode(
                maquina=maquina
                , periodo=periodo + tipo_movimiento
                , producto=producto
                , paso=paso
                , demanda=demanda
                , task_mode=task_mode
                , array=array_revisar
            )
            
            if not actualizado:
                raise ValueError(f"Error al agregar el task_mode {task_mode} en periodo = {periodo + tipo_movimiento}, maquina = {maquina}")
            
            #revisar si es viable
            es_viable = self.es_viable(array_revisar)["todo"]["bool"]
            
            if es_viable:
                periodo += tipo_movimiento
            
                array_cambiado = array_revisar.copy()
            
            #si no es completa
            if not completa:
                break
        
        return maquina, periodo, True, array_cambiado
    
    def __cambiar_task_mode(
            self
            , maquina_origen : str
            , periodo_origen : int
            , maquina_nueva : str
            , array : np.ndarray = None
            , inicio : int = None
            , termina : int = None
        ) -> tuple[bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
        """
        __cambiar_task_mode - 
        
        Cambia el `task mode` en la posicion [`maquina_origen`,`periodo_origen`]
        a un `task mode` en la máquina `maquina_nueva` en el periodo más reciente
        disponible.
        
        El metodo respeta el mismo tipo de `task` y la información del producto.
        
        Parameters
        ----------
        maquina_origen (str) :
            La maquina donde se ubica el `task mode` original.
        
        periodo_origen (int) :
            Periodo donde se ubica el `task mode` original.
        
        maquina_nueva (str) :
            La maquina a donde se agregará el nuevo `task mode`.
        
        array (np.ndarray, optional, defaults to None) :
            Array a modificar.
            Si es None se utiliza `self.cromosoma`
        
        inicio (int, optional, defaults to None) :
            Periodo inicial que se revisará.
            Si None se selecciona el primer periodo de los datos
        
        termina (int, optional, defaults to None) :
            Periodo final que se revisará.
            Si None se selecciona el ultimo periodo de los datos
        
        Returns
        -------
        tuple[bool, np.ndarray[tuple[Any, ...], np.dtype[Any]]] :
            * Si True se cambió el task mode exitosamente, False en otro caso
            * Una copia del array `array` modificado, si no hubo modificacion se regresa una copia del array original
        
        Raises
        ------
        ValueError :
            Si la maquina nueva no puede procesar el tipo de `task` del `task mode` de origen.
        
        IndexError :
            Si no hay un periodo disponible en la maquina nueva.
        
        ValueError :
            No fue posible agregar el nuevo `task mode` en la maquina nueva.
        
        ValueError :
            No fue posible eliminar el `task mode` original en la maquina original.
        
        """
        
        if array is None:
            array = self.cromosoma

        array_revisar = array.copy()
        
        gen = array_revisar[self.maquinas[maquina_origen], periodo_origen - 1]
        #es vacio por lo tanto no se puede mover
        if gen == "":
            return False, array_revisar
        
        #busca el inicio del task_mode
        maquina_origen, periodo_origen = self.__buscar_inicio_task_mode(
            maquina=maquina_origen
            , periodo=periodo_origen
            , array=array_revisar
        )
        
        producto, demanda, task_mode, _, paso = self.__gen_inverso(
            gen=gen
        )
        
        #calcular el task_mode nuevo a agregar
        task = self.datos.obtener_task(task_mode=task_mode)
        task_mode_nuevo = self.datos.obtener_task_mode(task=task, maquina=maquina_nueva)
        
        if task_mode_nuevo is None:
            raise ValueError(f"La maquina {maquina_nueva} no puede procesar el task '{task}' original")
        
        #revisar si es posible agregar el nuevo task en la otra maquina
        if inicio is None:
            inicio = min(self.periodos)
        
        if termina is None:
            termina = max(self.periodos)
        
        bool_resultado, periodos_disponibles = self.revisar_task_mode_en_maquina(
            maquina=maquina_nueva
            , task_mode=task_mode_nuevo
            , array=array_revisar
            , inicio=inicio
            , termina=termina
        )
        
        if not bool_resultado: #bool_resultado == False
            raise IndexError(
                "No hay periodos disponibles para "
                ,f"agregar el task_mode {task_mode_nuevo} "
                ,f"en la maquina {maquina_nueva}"
            )
        
        #arbitrario, se selecciona el periodo minimo para minimizar el makespan
        #es posible cambiar el algoritmo de selección
        periodo_nuevo = min(periodos_disponibles)
        
        #agregar task mode nuevo
        maquina_nueva, periodo_nuevo, bool_agregar, array_revisar = self.agregar_task_mode(
            maquina=maquina_nueva
            , periodo=periodo_nuevo
            , producto=producto
            , paso=paso
            , demanda=demanda
            , task_mode=task_mode_nuevo
            , array=array_revisar
        )
        
        if not bool_agregar: #bool_agregar == False
            raise ValueError(
                f"No fue posible agregar el task mode {task_mode_nuevo}"
                , f" en periodo {periodo_nuevo}, maquina {maquina_nueva}"
            )
            
        #eliminar task mode anterior
        maquina_origen, periodo_origen, bool_eliminar, array_revisar = self.remover_task_mode(
            maquina=maquina_origen
            , periodo=periodo_origen
            , array=array_revisar
        )
        
        if not bool_eliminar: #bool_agregar == False
            raise ValueError(
                f"No fue posible eliminar el task mode {task_mode}"
                , f" en periodo {periodo_origen}, maquina {maquina_origen}"
            )
        
        return True, array_revisar
    
    def __buscar_ocupado(
            self
            , maquina : str
            , periodo : int
            , tipo_movimiento : Literal[-1 ,1] = -1 
            , considerar_actual : bool = True 
            , array : np.ndarray = None
        ) -> tuple[str, int, bool]:
        """
        __buscar_ocupado -
        
        Busca el siguiente periodo donde se encuentra un task mode asignado en la máquina.
        
        Parameters
        ----------
        maquina (str) :
            Máquina a revisar.
        
        periodo (int) :
            Periodo a inicial a revisar.
        
        tipo_movimiento (Literal[-1,1], optional, defaults to -1) :
            Como se moverá la búsqueda:
            * `-1` disminuyendo el periodo
            * `1` aumentando el periodo
        
        considerar_actual (bool, optional, defaults to True) :
            Si la posición incial a revisar está ocupado, se considera a revisar o no.
            * Si True, sí se considera, por lo tanto se regresa el periodo inicial del task mode en la posición a buscar.
            * Si False, no se considera, por lo tanto se busca el siguiente periodo ocupado.
        
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        tuple[str, int, bool] :
            La maquina y periodo final si se encuentra un periodo ocupado:
            * Maquina a revisar.
            * Periodo ocupado encontrado.
            * `True`, indicando que se encontró un periodo ocupado.
            
            Si no se encuentra un periodo ocupado se regresa la información de los parámetros
            * Maquina a revisar.
            * Periodo inicial, igual al parámetro ingresado. 
            * `False`, indicando que no se encontró un periodo ocupado.
        
        """
        if tipo_movimiento not in [-1,1]:
            raise ValueError(f'Tipo de movimiento no válido')
        
        if array is None:
            array = self.cromosoma
        
        gen = array[self.maquinas[maquina], periodo - 1]
        
        maquina_inicio = maquina
        periodo_inicio = periodo
        
        if gen != "": #el periodo actual esta ocupado
            maquina, periodo = self.__buscar_inicio_task_mode(
                maquina=maquina
                , periodo=periodo
                , array=array
            )
            
            if considerar_actual: #se considera el task mode actual, por lo tanto se regresa el inicio del task mode
                return maquina, periodo, True
            
            else: #NO se considera el task mode actual, por lo tanto se busca el siguiente task mode    
                gen= array[self.maquinas[maquina], periodo - 1] #ya se revisó, no es vacio
                _,_, task_mode,_,_=self.__gen_inverso(gen=gen)
                #si el tipo de moviento es -1 se busca a la izquierda este ajuste es 0
                #si el tipo de movimiento es 1 se busca a la derecha este ajuste es igual a la cantidad
                #de intervalos en el task_mode
                intervalos : int = len(self.datos.intervalos(task_mode=task_mode))
                periodo = periodo + (0 if tipo_movimiento == -1 else intervalos)
                
        while True:
            #calcula el periodo a revisar
            periodo = periodo + tipo_movimiento
            
            #no se puede revisar un periodo que no existe
            if periodo not in self.periodos:
                return maquina_inicio, periodo_inicio, False

            if self.__es_vacio_array(
                    array=array
                    , maquina=maquina
                    , periodo=periodo
                ):
                continue
            else:
                break
        
        maquina, periodo = self.__buscar_inicio_task_mode(
            maquina=maquina
            , periodo=periodo
            , array=array
        )
        
        return maquina, periodo, True
    
    def obtener_gen(
            self
            , periodo : int
            , maquina : str
            , array : np.ndarray = None
        ) -> str:
        """
        obtener_gen - 
        
        Obtiene el gen ubicado en [maquina, periodo]
        
        Parameters
        ----------
        periodo (int) :
            Periodo a buscar.
        
        maquina (str) :
            Maquina a buscar.
        
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        Returns
        -------
        str :
            El gen ubicado en maquina, periodo
        
        """
        
        if array is None:
            array = self.cromosoma
        
        return array[self.maquinas[maquina], periodo - 1]
    
    def __buscar_task_mode(
            self
            , producto_buscar : str
            , demanda_buscar : int
            , paso_buscar : int
            , array : np.ndarray = None
            , inicio : bool = True
            , verbose : bool = False
        ) -> tuple[str, int]:
        """
        __buscar_task_mode - 
        
        Busca el `periodo` y `maquina` que procesa el `task mode` buscado por los
        parámetros.
        
        Parameters
        ----------
        producto_buscar (str) :
            El producto a buscar.
        
        demanda_buscar (int) :
            Número de demanda del producto a buscar.
        
        paso_buscar (int) :
            Paso de la receta del producto a buscar.
        
        array (np.ndarray, optional, defaults to None) :
            Array a revisar.
            Si es None se utiliza `self.cromosoma`
        
        inicio (bool) :
            Si True, busca el periodo donde se inicia el task_mode (primer intervalo)
            Si False, busca el periodo donde se termina el task_mode (ultimo intervalo)
        
        Returns
        -------
        tuple[str, int] :
            * (str) Código de la máquina encontrada
            * (int) Periodo del task mode encontrado
        
        Raises
        ------
        ValueError :
            Si no se encuentra un `task mode` que cumple las condiciones de los parámetros.
        
        """
        if verbose:
            print("Metodo:__buscar_task_mode")
            print(f"Buscando,Producto:{producto_buscar},Demanda:{demanda_buscar},Paso:{paso_buscar}")
        
        if array is None:
            array = self.cromosoma
            if verbose:
                print("Utilizando cromosoma")
        
        periodo_maximo = max(self.periodos)
        for maquina in self.maquinas:
            if verbose:
                print(f"Revisando Maquina:{maquina}")
            periodo = 1
            while periodo <= periodo_maximo:
                maquina, periodo, bool_encontrado= self.__buscar_ocupado(
                    maquina=maquina
                    , periodo=periodo
                    , tipo_movimiento=1
                    , considerar_actual=False
                    ,array=array
                )
                if verbose:
                    print(f"Revisando,Maquina:{maquina},Periodo:{periodo}")
                
                if not bool_encontrado:
                    break
                
                gen = self.obtener_gen(periodo=periodo,maquina=maquina,array=array)
                if verbose:
                    print(f"Gen Revisando:{gen}")
                
                producto , demanda, task_mode, _, paso = self.__gen_inverso(
                    gen=gen
                )
                
                if (producto==producto_buscar) and (demanda==demanda_buscar) and (paso==paso_buscar):
                    maquina, periodo = self.__buscar_inicio_task_mode(maquina=maquina, periodo=periodo, array=array)
                    if inicio:
                        return maquina, periodo
                    else:
                        return maquina, periodo + len(self.datos.intervalos(task_mode=task_mode))
                
                #periodo += 1
        
        raise ValueError("No se encontró el task mode buscado")
    
    def inicializar(
            self
        ):
        
        raise NotImplementedError()
    
    def mezcla(
            self
        ):
        
        raise NotImplementedError()
    
    def mutacion(
            self
        ):
        
        raise NotImplementedError()

class IndividuoA(IndividuoBase):
    
    def __init__(
            self
            , inicializar : bool = False
            , saved_path : str = None 
            , random_seed : int = None
            , kwargs_inicializar : dict = None
        ):
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
            _,_ , resultado, array_resultado =self._IndividuoBase__mover_periodo_task_mode(
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

    def cruce(
            self
            , padre : "IndividuoA"
        ) -> tuple["IndividuoA",int]:
        """
        cruce - Realiza el cruce con otra instancia de `IndividuoA`
        
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
        aptitudes = np.array([aptitud_madre, aptitud_padre])+1 
        probabilidad = 1-aptitudes / aptitudes.sum()

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
        
        grafica_gantt_plt(
            df=df
            , time_leaps=self.cambio_turno
            , min_value_x=min(self.periodos)-1 
            , max_value_x=max(self.periodos)+1
            , costo_energia=energia
            , makespan=makespan
            , save_path=path_save_fig
            , kwargs_fig=kwargs_fig
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
    hijo, resultado = madre.cruce(
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
    
def main():
    figura_muestra_mutacion()
    
if __name__ == "__main__":
    main()
    