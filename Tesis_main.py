from algoritmo_genetico import (
    buscar_mejor_parametros
    , optimizacion_final_tesis
    , optimizacion_prueba
)

from algoritmo_mip import (
    optimize_model
)

from Carga_Datos import (
    PATH_INPUT
    , PATH_INPUT_TEST
)

def main():
    while True:
        print("\n=== Menú principal ===")
        print("1) Mostrar rutas de entrada")
        print("2) (Modelo genético) Buscar parametros")
        print("3) (Modelo genético) Hacer prueba")
        print("4) (Modelo genético) Ejecutar modelo")
        print("5) (Modelo lineal) Hacer prueba")
        print("6) (Modelo lineal) Ejecutar modelo")
        print("0) Salir")
        
        opcion = input("Elige una opción: ").strip()
        
        match opcion:
            case "0":
                print("Saliendo...")
                break
            case "1":
                print(f"PATH_INPUT = {PATH_INPUT}")
                print(f"PATH_INPUT_TEST = {PATH_INPUT_TEST}")
            case "2":
                print("Buscar parametros modelo genético")
                buscar_mejor_parametros()
            case "3":
                print("Ejecutar prueba de modelo genético")
                optimizacion_prueba()
            case "4":
                print("Ejecutar modelo genético")
                optimizacion_final_tesis()
            case "5":
                print("Ejecutar prueba de modelo lineal")
                optimize_model(
                    path_datos=PATH_INPUT_TEST
                    ,  save="variables_test.csv"
                )
            case "6":
                print("Ejecutar de modelo lineal")
                optimize_model(
                    path_datos=PATH_INPUT
                    ,  save="variables.csv"
                )
            case _:
                print("Opción no válida, intenta de nuevo.")  

if __name__ == "__main__":
    main()
