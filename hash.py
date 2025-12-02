from kax import acts
from pprint import pprint
import os
import shutil
import time

# nombre de la careta donde estan todos los archivos
DIRECTORIO = os.path.join('data_ecg') # directorio original
DIRECTORIO_COPIA = os.path.join('data_ecg_copia') # directorio para las copias
DATA_ECG = [f for f in os.listdir(DIRECTORIO) if os.path.isfile(os.path.join(DIRECTORIO, f))] # itera los archivos en el directorio guardado en la variable DIRECTORIO
USER = os.getenv("USER") # usuario por defecto

# conexion a servidor
acts.setUrl("http://148.247.201.210:5060/api") 
acts.setStorageUrl("http://148.247.201.210:5070/api") 
acts.setBrokerPort(1883)
acts.setBrokerUrl("148.247.201.226")

tamTotal = len(DATA_ECG)

#print(DATA_ECG); 

# Uso de storage 
# Uso de storage 
# Uso de storage 

archivos_para_copiar = os.listdir(DIRECTORIO)
for i in archivos_para_copiar:
    inicio = time.time()
    ruta_completa_origen = os.path.join(DIRECTORIO, i)
    ruta_completa_destino = os.path.join(DIRECTORIO_COPIA, i)
    shutil.copy(ruta_completa_origen, ruta_completa_destino)
    fin = time.time()
    duracion = fin - inicio
    print(duracion)

    file_path = os.path.join("TLocal.txt")
    
    try:
        with open(file_path, "a") as file:
            file.write(str(duracion)+ '\n')
    except IOError as e:
        print("Error")
