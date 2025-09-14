from Carga_Datos import Datos, PATH_INPUT, task_mode_a_str, str_a_task_mode
import numpy as np
from typing import Any, Literal

class Individuo:
    
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
            shape = (len(self.maquinas.keys()), len(self.periodos))
            , fill_value = ""
        )
        
        self.cambio_turno : list[int] = self.datos.time['time_leap']
    
    def __modificar_array(self
            , array : np.ndarray
            , maquina : str
            , periodo : int
            , valor : Any
        ):
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
        
        Raises
        ------
        ValueError :
            Si `maquina` no es uno de `"MAQ118", "MAQ119", "MAQ120"])`
        
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
    
    def __es_vacio_array(self
            , array : np.ndarray
            , maquina : str
            , periodo : int
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
        array (np.ndarray) :
            Array a revisar.
        
        maquina (str) :
            Maquina donde se revisará el array
        
        periodo (int) :
            Periodo donde se modificará el array
        
        Returns
        -------
        bool :
            * `True` si es vacio
            * `False` si tiene un valor
        """
        
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
            , gene : str
            , sep : str = "|"
        )  -> tuple[str, int, str, int, int]:
        """
        __gen_inverso - 
        
        Obtiene la información guardada en el gen dado.
        
        Parameters
        ----------
        gene (str) :
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
        
        return str_a_task_mode(
            info=gene
            , sep=sep
        )
    
    def __makespan(self) -> int:
        """
        __makespan - 
        
        Calcula el `makespan` del individuo
        
        Returns
        -------
        int :
            Valor que representa el ultimo periodo activo
            es decir el `makespan`
        
        """
        
        produccion : np.ndarray = np.apply_along_axis(np.any, 0, self.cromosoma != "")
        
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
        gene (str) :
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
                gene=gen, sep=sep
            )
            return self.task_mode_energy[task_mode][intervalo]
    
    def __energia_precio(self) -> float:
        """
        __energia_precio - 
        
        Calcula el precio de la energia total del individuo
        
        Returns
        -------
        float :
            El precio total de la energia de todas las actividades en todos los periodos
        
        """

        energia_utilizada : np.ndarray = np.array(
            [[self.__gen_a_energia_utilizada(i) for i in row] for row in self.cromosoma]
        ).sum(axis=0)
        
        energia_socket = np.maximum(energia_utilizada - self.energia_solar_cantidad, 0)
        
        return np.dot(energia_socket, self.energia_socket_precio)

    def aptitud(
            self
            , peso_makespan : float = 1
            , peso_energia : float = 1
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
        
        return (peso_makespan * self.__makespan + peso_energia * self.__energia_precio) / (peso_energia + peso_makespan)
    
    def __revisar_cambio_turno(self) -> tuple[bool, list[dict[str,str|int]]]:
        """
        __revisar_cambio_turno - 
        
        Revisa si un task se procesa durante un cambio de turno.
        
        No se puede iniciar y terminar un task durante distintos turnos,
        todos los task se tienen que terminar en el mismo turno que se inicia.
        
        Además se regresa una lista donde se encuentran los errores
        que se deben cambiar.
        
        Returns
        -------
        tuple[bool, list[dict[str,str|int]]] :
            1er elemento: un bool si se cumple o no esta condición. 
            
            2do elemento: lista con los errores a cambiar donde cada elemento es un dict.
                El dict tiene como llaves los siguientes elementos: ["producto", "demanda", "task_mode", "paso", "periodo", "maquina]
                el cual tiene el valor correspondiente.
        
        """

        resultado = True
        lista_errores = list()

        for periodo in self.cambio_turno:
            for maquina, maquina_pos in self.maquinas.items():
                array_a_revisar = self.cromosoma[maquina_pos, [periodo, periodo-1]]
                
                antes : str = array_a_revisar[0]
                despues : str = array_a_revisar[1]
                
                #si un periodo es vacio entonces no importa si el otro periodo esta ocupado
                if (antes == "") or (despues == ""):
                    continue
                    
                producto_antes, demanda_antes, task_mode_antes, _, paso_antes =self.__gen_inverso(
                    gene = antes
                )
                
                producto_despues, demanda_despues, task_mode_despues, _, paso_despues =self.__gen_inverso(
                    gene = despues
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
    
    def __revisar_produccion_completa(self) -> tuple[bool, list[dict[str,str|int]]]:
        #TODO terminar
        resultado = True
        revisar_dict = dict()
        
        for producto, demanda in self.datos.iterar_productos():
            if producto not in revisar_dict:
                revisar_dict[producto] = dict()

            if demanda not in revisar_dict[producto]:
                revisar_dict[producto][demanda] = dict()
        
        for periodo in self.periodos:
            for maquina, maquina_pos in self.maquinas.items():
                elemento = self.cromosoma[maquina_pos , periodo]
            
                if elemento == "":
                    continue
                
                producto, demanda, task_mode, intervalo, paso= self.__gen_inverso(
                    gene = elemento
                )
                
                
        
        return resultado, [revisar_dict]
            
    def es_viable(self) -> dict:
        
        es_viable_cambio_turno_bool, es_viable_cambio_turno_lista= self.__revisar_cambio_turno()
        es_viable_produccion_completa_bool, es_viable_produccion_completa_lista = self.__revisar_produccion_completa()
        
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
        ) -> bool:
        """
        agregar_task_mode - 
        
        Agrega un task_mode en el array `cromosoma`
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
        
        Returns
        -------
        bool :
            * True si se implementó exitosamente
            * False si NO se implementó exitosamente
        
        """
        
        intervalos = self.datos.intervalos(task_mode=task_mode)
        
        es_viable : True
        #revisar si es viable agregar el task_mode
        for i in range(len(intervalos)):
            es_viable = self.__es_vacio_array(
                self.cromosoma
                , maquina = maquina
                , periodo = periodo+i
            )
            
            #no es viable, un periodo ya esta ocupado
            if not es_viable:
                return False
        
        #es viable, por lo tanto se agrega el task_mode
        for i in range(len(intervalos)):
            
            self.__modificar_array(
                self.cromosoma
                , maquina = maquina
                , periodo = periodo + i
                , valor = self.__gen(
                    producto = producto
                    , demanda = demanda
                    , task_mode = task_mode
                    , intervalo = i
                    , paso = paso
                )
            )
        
        #se agrego el task mode exitosamente
        return True

    def buscar_inicio_task_mode(
            self
            , maquina : str
            , periodo : int
        ):
        
        
        pass
    
    def remover_task_mode(
            self
        ):
        
        pass
    

def main():
    individuo = Individuo()
    
    
    
if __name__ == "__main__":
    main()
    