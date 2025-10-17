import json
import os
import numpy as np
from typing import Any, Generator

PATH_INPUT = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Datos Tesina','Input_JSON_Schedule_Optimization.json')

def cargar_datos(archivo : str | os.PathLike) -> dict:
    """
    cargar_datos - 
    
    Carga datos desde un archivo JSON y devuelve un diccionario con los datos.
    
    Parameters
    ----------
    archivo (str | os.PathLike) :
        Ruta al archivo JSON que contiene los datos a cargar.
    
    Returns
    -------
    dict :
        Un diccionario con los datos cargados desde el archivo JSON.
    
    """
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos
    except FileNotFoundError:
        print(f"Error: El archivo {archivo} no se encuentra.")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {archivo} no es un JSON válido.")
        return None

class Datos:
    """
    Datos - 
    
    Clase que contiene los datos de la tesina
    """
    
    def __init__(self, path = PATH_INPUT):
        datos = cargar_datos(path)
        
        #crear diccionario de maquinas
        """
        self.machines : {
            "Machine_0" : [ #maquina 0
                "task_mode_0", #modo de actividad 0
                ...
                "task_mode_a" #modo de actividad a
            ], ...
            "Machine_m" : [ #maquina m
                "task_mode_0", #modo de actividad 0
                ...
                "task_mode_b" #modo de actividad b
            ],
        }
        """
        self.machines = dict()
        
        for m in datos['cells'][0]['machines']:
            self.machines[m] = dict()
            
            for i in datos['machines']:
                if m != i['id']:
                    continue
                
                #agregar actividades que se pueden procesar en cada maquina
                self.machines[m] = i['task_modes']
        
        i = 0
        self.machines_id : dict[str,int] = dict()
        for maq in list(self.machines.keys()):
            self.machines_id[maq] = i
            i += 1
        
        #crear diccionario de actividades
        """
        self.tasks : {
            "task_0" : { #actividad task_0
                "task_mode_0" : { #modo de actividad 0
                    "power" : [t_0,t_1,...,t_a] #energia utilizada en cada intervalo
                }, ...
                "task_mode_n" : { #modo de actividad n
                    "power" : [t_0,t_1,...,t_b] #energia utilizada en cada intervalo
                }
            }, ...
            "task_m" : { #actividad task_m
                "task_mode_0" : { #modo de actividad 0
                    "power" : [t_0,t_1,...,t_a] #energia utilizada en cada intervalo
                }, ...
                "task_mode_n" : { #modo de actividad n
                    "power" : [t_0,t_1,...,t_b] #energia utilizada en cada intervalo
                }
            }
        }
        """
        self.tasks = dict()
        
        for t in datos['tasks']:
            task = t['id']
            task_modes = t['task_modes']
            
            self.tasks[task] = dict()
            
            for tm in datos['task_modes']:
                if tm['id'] in task_modes:
                    self.tasks[task][tm['id']] = dict()
                    self.tasks[task][tm['id']]['power'] = tm['power']

                    for machine, task_modes_machine in self.machines.items():
                        if tm['id'] in task_modes_machine:
                            self.tasks[task][tm['id']]['machine'] = machine
        
        #crear diccionario de energia
        """
        self.energy : {
            t_0 : { #periodo 0
                "Socket Energy" : { #energia red electrica
                    "amount" : Infinity, #cantidad ilimitada
                    "price" : p_0 #precio en el periodo 0
                },
                "Solar" : { #energia solar
                    "amount" : a_0, #cantidad disponible en el periodo 0
                    "price" : 0 #energia gratis, precio = 0
                }
            }, ...
            t_n : {
                "Socket Energy" : {
                    "amount" : Infinity,
                    "price" : p_n
                },
                "Solar" : {
                    "amount" : a_n,
                    "price" : 0
                }
            }
        }     
        """
        self.energy = dict()
        socket = datos['energy_sources'][0]['price']
        solar = datos['energy_sources'][1]['availability']
        
        if len(socket) != len(solar):
            raise ValueError(f"No hay la misma cantidad en energias socket ({len(socket)}) y solar ({len(solar)}). ")
        else:
            self.periodos : list[int] = [i for i in range(1,len(solar)+1)]
            
            for i in self.periodos:
                self.energy[i] = dict()
                self.energy[i]['Socket Energy'] = {
                    'price' : float(socket[i-1]),
                    'amount' : np.inf #infinito
                }
                self.energy[i]['Solar'] = {
                    'price' : 0.0,
                    'amount' : solar[i-1]
                }
        
        self.solar_amount = np.array(solar)
        self.socket_price = np.array(socket)
        
        #crear diccionario de productos
        """
        self.products : {
            product_0 : {
                "request" : d_0, #el producto product_0 tiene una demanda de d_0 unidades
                "tasks" : {
                    {
                        "task_0" : r_0, #repite r_0 veces la actividad
                        "order" : 0
                    }, 
                    ...
                    {
                        "task_m" : r_m,
                        "order" : m
                    }
                }
            }, ...
            product_n : {
                "request" : d_n,
                "tasks" : {
                    {
                        "task_0" : r_0, #repite r_0 veces la actividad
                        "order" : 0
                    }, 
                    ...
                    {
                        "task_m" : r_m,
                        "order" : m
                    }
            }
        }
        """
        self.products = dict()
        
        for p in datos['products']:
            self.products[p['id']] = dict()
            self.products[p['id']]['tasks'] = dict()
            self.products[p['id']]['request'] = 0
            self.products[p['id']]['deadline'] = list()
            #print(p)
            
            i = 0 ##revisar order
            for t in p['tasks']:
                self.products[p['id']]['tasks'][t['task']] = {'runs' : t['runs'] , 'order' : i}
                i += 1
        
        for p in datos['product_requests']:
            self.products[p['product']]['request'] += p['amount']
            
            if 'deadline' in p:
                if isinstance(p['deadline'], int):
                    self.products[p['product']]['deadline'].append(p['deadline'])
                if isinstance(p['deadline'], list):
                    self.products[p['product']]['deadline'].extend(p['deadline'])
        
        #crear diccionario de periodos
        """
        self.time : {
            "time_leap" : [t_0, ... ,t_n] #cuando sucede un cambio de dia, 
                # por lo tanto una actividad no puede suceder antes y despues de este periodo
        }
        """
        self.time = dict()
        self.time['time_leap'] = datos['configuration']['time_leap']
    
    def energia_periodo(self, t : int) -> dict[str, dict[str, Any]]:
        """
        energia_periodo - 
        
        Trae la información de la energía en el periodo dado
        
        Parameters
        ----------
        t (int) :
            Periodo
        
        Returns
        -------
        dict[str, dict[str, Any]] :
            Diccionario que tiene el tipo de energia en str como llave y como valor otro diccionario
            con el precio y la cantidad disponible en el periodo.
        
        Raises
        ------
        ValueError :
            Si el periodo `t` no existe en los datos
        
        """
        
        if t < 1 or t > (max(self.periodos)):
            raise ValueError(f't tiene que ser entre 1 y {max(self.periodos)} inclusivo')
              
        resultado = {
            'Solar' : {
                'price' : self.energy[t]['Solar']['price']
                , 'amount' : self.energy[t]['Solar']['amount']
            },
            'Socket Energy' : {
                'price' : self.energy[t]['Socket Energy']['price']
                , 'amount' : self.energy[t]['Socket Energy']['amount']
            }
        }

        return resultado
    
    def receta_producto(self, producto : str) -> list[tuple[str, dict[str, list[str]], int]]:
        """
        receta_producto - 
        
        Da un una lista con la receta de como crear un producto, es decir,
        cada elemento de la lista es una actividad (o paso) y da la informacion de
        cuales maquinas y task_modes se pueden utilizar para completar ese paso.
        
        Parameters
        ----------
        producto (str) :
            Nombre del producto a consultar
        
        Returns
        -------
        list[tuple[str, dict[str, list[str]], int]] :
            lista con los pasos para crear el producto, cada elemento contiene una tupla con:
                
            * primer elemento: un string con el nombre de la actividad
            * segundo elemento: un dict donde:
            
                - la llave es el task_mode para realizar la actividad
                - el valor es una lista con las maquinas válidas para operar el task_mode
            * tercer elemento: el numero del paso en la receta
            
        Example
        -------
        .. code-block:: python
            [
                ('task_0', {'task_mode_0': ['Machine_1'], 'task_mode_1': ['Machine_2']}, 0),
                ('task_1', {'task_mode_2': ['Machine_1', 'Machine_2']}, 1)
            ]
            
        """
        
        resultado = []
        producto_dict = self.products[producto]

        num_paso = 0
        for task, value in producto_dict['tasks'].items(): #orden de task
            
            for _ in range(value['runs']): #cuantas veces se tiene que correr el task
                
                paso = dict()
                
                for task_mode in self.tasks[task]: #revisar los task_mode para cada task
                    maquinas = [] #lista de maquinas que pueden correr el task_mode
                    
                    for machine, value_machine in self.machines.items(): #revisar en cuales maquinas se puede correr el task_mode
                        if task_mode in value_machine:
                            maquinas.append(machine) #agregar maquina

                    if len(maquinas) != 0: #si hay maquinas agregar, se encontró que no maquina de los datos corre "Harden[1] TM2"
                        paso[task_mode] = maquinas.copy()
                
                resultado.append((task, paso, num_paso))
                num_paso += 1
        
        return resultado

    def iterar_completo(self) -> Generator[tuple[str, int, int, str, str, str, int], Any, None]:
        """
        iterar_completo - 
        
        Itera todas las posibles variables del modelo
        
        Yields
        ------
        Generator[tuple[str, int, int, str, str, int], Any, None] :
            - Elemento 0 (str): nombre del `producto`
            - Elemento 1 (int): `numero` de produccion de este producto, entre `0` y `demanda - 1` inclusivo
            - Elemento 2 (int): `paso` de la receta para producir el producto
            - Elemento 3 (str): `task` actividad del paso
            - Elemento 4 (str): `task_mode` del paso de la receta
            - Elemento 5 (str): codigo de la `maquina` donde se realiza el `task_mode`
            - Elemento 6 (int): intervalo de tiempo para realizar el `task_mode`, entre `0` 
                y `len(tasks[task][task_mode]["power"]))-1` inclusivo
          
        """

        for producto, v in self.products.items(): #iterar entre los productos
            for demanda in range(v['request']): #iterar en la cantidad de elementos requeridos para producit
                receta = self.receta_producto(producto=producto) #receta del producto
                for paso in receta: #iterar entre los pasos de la receta
                    task, task_modes , paso_num = paso #extender el paso
                    for task_mode, maquinas in task_modes.items(): #iterar entre el task_mode y las maquinas que lo pueden procesar
                        for maquina in maquinas: #iterar entre las maquinas
                            for intervalo in range(len(self.tasks[task][task_mode]["power"])): #intervar entre el tiempo que se tarda en completar el task_mode
                                yield (producto, demanda, paso_num, task, task_mode, maquina, intervalo)

    def iterar_productos(self) -> Generator[tuple[str, int], Any, None]:
        """
        iterar_productos - 
        
        Itera todos los productos demandados por el problema
        
        Yields
        ------
        Generator[tuple[str, int], Any, None] :
            - Elemento 0 (str): nombre del `producto`
            - Elemento 1 (int): `numero` de produccion de este producto, entre `0` y `demanda - 1` inclusivo
            
        """
        
        for producto, v in self.products.items():
            for demanda in range(v['request']):
                
                yield (producto, demanda)

    def energia_task_intervalo(self, task : str, task_mode : str, intervalo : int = 0) -> float:
        """
        energia_task_intervalo - 
        
        Regresa la energia utilizada para realizar el `intervalo` en el `task` y `task_mode`.
        
        Cada `task_mode` tiene un perfil de uso de energia.
        
        Parameters
        ----------
        task (str) :
            Actividad que realiza la maquina
        
        task_mode (str) :
            Modo de actividad del `task`
        
        intervalo (int, optional, defaults to 0) :
            Intervalo del perfil de energia.
        
        Returns
        -------
        float :
            Energia utilizada en ese intervalo
        
        """
        
        return self.tasks[task][task_mode]['power'][intervalo]
    
    def obtener_task(self, task_mode : str) -> str:
        """
        obtener_task - 
        
        Se obtiene el `task` para el `task_mode` dado.
        
        Parameters
        ----------
        task_mode (str) :
            nombre del `task_mode`
        
        Returns
        -------
        str :
            nombre del `task`
        
        Raises
        ------
        ValueError :
            Si no se encuentra el task que pertenece el task_mode
        
        """
        
        for t, task_mode_dict in self.tasks.items():
            if task_mode in task_mode_dict:
                return t 
        else:
            raise ValueError(f"{task_mode} no encontrado en un task")
     
    def intervalos(self, task_mode : str) -> list[int]:
        """
        intervalos -
        
        Regresa una lista de los intervalos para completar el `task_mode`
        dado. Donde los valores son la energía utilizada.
        
        Parameters
        ----------
        task_mode (str) :
            `task_mode` de un task
        
        Returns
        -------
        list[int] :
            Lista de intervalos del task_mode
        
        Example
        -------
        .. code-block:: python
            res = intervalos("Harden[1] TM2") 
            print(res) # resultado esperado: [1167,1167,1167,1196,1155]
            
        
        """
        for task in self.tasks:
            if task_mode in self.tasks[task]:
                
                return self.tasks[task][task_mode]['power']
    
    def iterar_deadlines(self) -> Generator[tuple[str, int, int], Any, None]:
        """
        iterar_deadlines - 
        
        Itera todos los productos demandados que tienen un límite de tiempo.
        
        Yields
        ------
        Generator[tuple[str, int, int], Any, None] :
            - Elemento 0 (str): nombre del `producto`
            - Elemento 1 (int): `numero` de produccion de este producto, entre `0` y `demanda - 1` inclusivo
            - Elemento 2 (int): el periodo limite de produccion.
        
        """
        
        for producto, v in self.products.items():
            for demanda in range(len(v['deadline'])):
                yield (producto, demanda, v['deadline'][demanda])
    
    def obtener_task_mode(self, task : str, maquina : str) -> str | None:
        """
        obtener_task_mode - 
        
        Calcula el `task_mode` disponible para la `maquina` y `task` dados.
        
        Parameters
        ----------
        task (str) :
            Actividad que realiza la maquina.
        
        maquina (str) :
            Maquina que realizará el task.
        
        Returns
        -------
        str | None :
            * str con el task_mode disponible.
            * `None` si no es posible realizar el task en esa maquina.
        
        """
        
        resultado = None
        
        for key, value in self.tasks[task].items():
            if maquina == value["machine"]:
                return key
            
        return resultado
    
def task_mode_a_str(
        producto : str
        , demanda : int
        , task_mode : str
        , intervalo : int
        , paso : int
        , sep : str = "|"
    ) -> str:
    """
    task_mode_a_str - 
    
    Crea un valor str para la información dada del task_mode.
    
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
        Número de paso de la receta de producción.
        
    sep (str, optional, defaults to "|") :
        Separador, que separa la información.
    
    Returns
    -------
    str :
        El valor el cual contiene toda la información.
    
    """
    return producto + sep + str(demanda) + sep + task_mode + sep + str(intervalo) + sep + str(paso)

def str_a_task_mode(
        info : str
        , sep : str = "|"
    )  -> tuple[str, int, str, int, int]:
    """
    str_a_task_mode - 
    
    Obtiene la información del task_mode guardada en el str.
    
    Parameters
    ----------
    info (str) :
        El valor guardado.
    
    sep (str, optional, defaults to "|") :
        El separador utilizado para guardar la información.
    
    Returns
    -------
    tuple[str, int, str, int, int] :
        Tuple con los siguientes elementos:
        * Producto
        * Demanda
        * task_mode
        * intervalo
        * paso
    
    """
    
    valores : list[str] = info.split(sep=sep)
    
    return str(valores[0]), int(valores[1]), str(valores[2]), int(valores[3]), int(valores[4])

def str_a_energia(
        info : str
        , datos : Datos
        , sep : str = "|"
    ) -> float:
    """
    str_a_energia - 
    
    Lee la energia que se requiere para procesar el producto con la informacion `info` dada.
    
    Parameters
    ----------
    info (str) :
        El valor guardado.
    
    datos (Datos) :
        Una instancia de la clase Datos
    
    sep (str, optional, defaults to "|") :
        El separador utilizado para guardar la información.
    
    Returns
    -------
    float :
        La cantidad de energia utizada por el task_mode en el intervalo dado
    
    """
    
    _, _, task_mode, intervalo, _ = str_a_task_mode(
        info=info
        , sep = sep
    )
    
    task = datos.obtener_task(
        task_mode=task_mode
    )
    
    energia = datos.energia_task_intervalo(
        task = task
        , task_mode = task_mode
        , intervalo = intervalo
    )
    
    return energia

def main():
    # Cargar datos desde un archivo JSON específico
    archivo = PATH_INPUT
    print(f"Cargando datos desde: {archivo}")
    
    datos = cargar_datos(archivo)
    
    datos = Datos()
    
    print(datos.products)
    
    for x in datos.iterar_productos():
        print(x)
    
    for x in datos.iterar_deadlines():
        print(x)
        
if __name__ == "__main__":
    main()