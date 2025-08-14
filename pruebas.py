
key_0 = ("a",0)
key_1 = ("b",1)
key_2 = ("a",1)

dict_prueba = dict()

if key_0 not in dict_prueba:
    dict_prueba[key_0] = "a0"

if key_1 not in dict_prueba:
    dict_prueba[key_1] = "b1"
    
if key_0 not in dict_prueba:
    dict_prueba[key_0] = "a2"
    dict_prueba[key_2] = "a1"
    
print(dict_prueba)