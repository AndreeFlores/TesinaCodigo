from Carga_Datos import Datos
import numpy as np
from typing import Any, Literal
import re

class Individuo:
    
    def __init__(self):
        
        self.datos = Datos()
        
        i = 0
        self.maquinas : dict[str,int] = dict()
        for maq in list(self.datos.machines.keys()):
            self.maquinas[maq] = i
            i += 1
        
        self.periodos : list[int] = self.datos.periodos
        
        self.energy = np.zeros(
            (len(self.maquinas.keys()), len(self.periodos))
        )
        
        self.cromosoma = np.full(
            shape = (len(self.maquinas.keys()), len(self.periodos))
            , fill_value = ""
        )
    
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
    
    def __esvacio_array(self
            , array : np.ndarray
            , maquina : str
            , periodo : int
        )  -> bool:
        """
        __esvacio_array - 
        
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
        
        sep (str, optional, defaults to "|") :
            Separador, que separa la información del gen.
        
        Returns
        -------
        str :
            El valor del gen el cual contiene toda la información.
        
        """
        
        return producto + sep + str(demanda) + sep + task_mode + sep + str(intervalo)
    
    def __gen_inverso(
            self
            , gene : str
            , sep : str = "|"
        )  -> tuple[str, int, str, int]:
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
        
        """
        
        valores : list[Any] = re.split(sep, gene)
        
        return str(valores[0]), int(valores[1]), str(valores[2]), int(valores[3])
    
    def agregar_task_mode(
            self
            , maquina : str
            , periodo : int
            , producto : str
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
            es_viable = self.__esvacio_array(
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
    