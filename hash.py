import os
from kax import acts # type: ignore
import time

# --- CONFIGURACIÓN DEL CLIENTE Y CONSTANTES ---
# Se utilizan las direcciones IP y puertos proporcionados en el documento de prueba.
acts.setUrl("http://148.247.201.210:5060/api")      # Control de metadata
acts.setStorageUrl("http://148.247.201.210:5070/api") # Almacenamiento
acts.setBrokerPort(1883)                             # Broker Pub/Sub
acts.setBrokerUrl("148.247.201.226")                 # Broker Pub/Sub URL

# --- RUTAS Y ARCHIVOS DE PRUEBA ---
RUTA_BASE = os.path.expanduser("/mnt/c/Users/jasil/OneDrive/Documentos/CINVES SEP-DIC 2025/CLASES/Introd a Ing.yTecnologias comp_Dr. JoseJuan_Compean/esteban/ANA/")

# NOTA: Debes cambiar estas rutas a directorios válidos en tu WSL.
#RUTA_ARCHIVO_ORIGINAL = os.path.expanduser("~/f4mb.pdf") #editar rutas segun la ubicacion de los datos ECG
RUTAS_ARCHIVOS_ORIGINALES = [
    os.path.expanduser("~/archivo1.pdf"),
    os.path.expanduser("~/archivo2.pdf"),
    os.path.expanduser("~/archivo(n).pdf"),
    # Agrega segun numero de archivos 
]
RUTA_DESCARGA = "/mnt/c/Users/jasil/OneDrive/Desktop/descarga_Proy1" #Designar ubicacion de archivos descarcargados
NOMBRE_NUEVO_ARCHIVO = "descargado_ECG.pdf"
NOMBRE_ARCHIVO_RESULTADOS = "resultados_pruebas_multiarchivo.txt" # Nuevo archivo de salida 

# Asegurar que la ruta de descarga exista
if not os.path.exists(RUTA_DESCARGA):
    os.makedirs(RUTA_DESCARGA)
    print(f"Directorio de descarga creado: {RUTA_DESCARGA}")

# Verificar si el (los) archivo(s) de prueba existe(n)
archivos_faltantes = [ruta for ruta in RUTAS_ARCHIVOS_ORIGINALES if not os.path.exists(ruta)]
if archivos_faltantes:
    print(f"\n[ERROR] Archivos no encontrados: {archivos_faltantes}. Saliendo del programa.")
    exit()

# --- CONSTANTE DE PRUEBAS ---
NUM_PRUEBAS = 45  #Preguntar a Esteban cuantas pruebas vamos a hacer
NUM_ARCHIVOS = len(RUTAS_ARCHIVOS_ORIGINALES) # Nuevo contador de archivos

# --- ACUMULADORES DE TIEMPO ---
# Se inicializan a 0 para sumar el tiempo de cada prueba.
total_tiempo_paso1 = 0.0 # Disco -> RAM
total_tiempo_paso2 = 0.0 # RAM -> Cloud
total_tiempo_paso3 = 0.0 # Cloud -> RAM
total_tiempo_paso4a = 0.0 # RAM -> Datos 
total_tiempo_paso4b = 0.0 # Datos -> Disco 
total_limpieza = 0.0
pruebas_exitosas = 0 # Total de pruebas que completaron todo el ciclo

print("-" * 70)
print(f"Iniciando {NUM_PRUEBAS} ciclos de prueba")
print("-" * 70)

for i in range(1, NUM_PRUEBAS + 1):
    print(f"\n{'=' * 15} prueba #{i}/{NUM_PRUEBAS} {'=' * 15}")
    
    metadata_local = None
    download_metadata = None

    hashes_a_limpiar = []
        
    # --- PASO 1: DISCO LOCAL A MEMORIA RAM (MEMORIA COMPARTIDA LOCAL) ---
    try:
        start_time = time.time()
        metadata_local = acts.loadRes(RUTAS_ARCHIVOS_ORIGINALES) 
        end_time = time.time()
        duration = end_time - start_time
        total_tiempo_paso1 += duration
        
        file_info = metadata_local['resources'][0]
        hash_id = file_info['hash']
        hashes_a_limpiar = [res['hash'] for res in metadata_local['resources']]
    
        print(f"1.DISCO LOCAL -> RAM (loadRes) | Tiempo: {duration:.4f}s | Archivos cargados: {len(metadata_local['resources'])}")
    
    except Exception as e:
        print(f"   -> [ERROR] Salio mal el paso 1 (Carga local): {e}")
        continue
        
    # --- PASO 2: MEMORIA RAM A CLOUD (MEMORIA COMPARTIDA EN LA NUBE) ---
    try:
        start_time = time.time()
        acts.uploadToCloudFromMemory(metadata_local)
        end_time = time.time()
        duration = end_time - start_time
        total_tiempo_paso2 += duration
        print(f"2.RAM -> CLOUD (uploadToCloudFromMemory) | Tiempo: {duration:.4f}s")
        
    except Exception as e:
        print(f"   -> [ERROR] Salio mal el paso 2 (Subida a Cloud): {e}")
        # Intentar limpiar la RAM local para no dejar residuos
        for h in hashes_a_limpiar: acts.removeShm(h)
        continue
        
    # --- PASO 3: CLOUD A MEMORIA RAM (DESCARGA LOCAL) ---
    try:
        main_hash_id = hashes_a_limpiar[0]

        start_time = time.time()
        download_metadata = acts.downloadFromCloud(hash_id)
        end_time = time.time()
        duration = end_time - start_time
        total_tiempo_paso3 += duration
        print(f"3.CLOUD -> RAM (downloadFromCloud) | Tiempo: {duration:.4f}s")
        
    except Exception as e:
        print(f"   -> [ERROR] Salio mal el paso 3 (Descarga de Cloud): {e}")
        # Intentar limpiar la metadata del Cloud y la RAM local
        for h in hashes_a_limpiar:
            acts.removeShmFromCloud(h)
            acts.removeShm(h)
        continue

    # --- PASO 4: MEMORIA RAM A DISCO LOCAL (ALMACENAMIENTO) ---
    
    # 4a. Obtener los datos del segmento de memoria compartida.
    try:
        start_time = time.time()
        archivos_guardados = 0

        # 4a. Obtener los datos del segmento de memoria compartida.
        datos_archivo = acts.getRes(resource['file']) # type: ignore
            
            # 4b. Guardar los datos en el disco local.
        nombre_archivo = resource['file']  # type: ignore
        ruta_completa = os.path.join(RUTA_DESCARGA, nombre_archivo)
        acts.saveFile(RUTA_DESCARGA, datos_archivo, nombre_archivo)
        archivos_guardados += 1

        end_time = time.time()
        duration = end_time - start_time
        total_tiempo_paso4 += duration
        
        print(f"4.RAM -> DISCO LOCAL (Guardar {archivos_guardados} archivos). | Tiempo: {duration:.4f}s")
        
        # Si llega aquí, la prueba fue exitosa
        pruebas_exitosas += 1
        
    except Exception as e:
        print(f"   -> [ERROR] Fallo PASO 4 (Guardado de archivos): {e}")
        # Limpieza de lo subido al Cloud y la RAM local
        for h in hashes_a_limpiar:
            acts.removeShmFromCloud(h)
            acts.removeShm(h)
        continue
    # --- PASO 5: LIMPIEZA ---
    try:
        start_time = time.time()
        
        # Limpiar CADA hash individualmente
        for file_hash in hashes_a_limpiar:
            acts.removeShmFromCloud(file_hash)
            acts.removeShm(file_hash)
            
        end_time = time.time()
        duration = end_time - start_time
        total_limpieza += duration
        print(f"5. LIMPIEZA ({len(hashes_a_limpiar)} archivos) | Tiempo: {duration:.4f}s")

    except Exception as e:
        print(f"   -> [ADVERTENCIA] Fallo en la limpieza: {e}")


print(f"\n{'=' * 70}")
print(f"FINALIZADAS {NUM_PRUEBAS} PRUEBAS. CICLOS COMPLETADOS: {pruebas_exitosas}")
print(f"{'=' * 70}\n")

## RESULTADOS DE LOS TIEMPOS PROMEDIO

if pruebas_exitosas > 0:
    # Se calcula el tiempo promedio dividiendo el tiempo total de cada paso por el número de pruebas exitosas.
    # * Se agrupan los pasos de 'RAM a Cloud' y 'Cloud a RAM' por ser la transferencia más relevante.
    # * Se agrupan los pasos de 'RAM a Disco' (getRes + saveFile) para reflejar el proceso completo de guardado local.
    
    promedio_disco_a_ram = total_tiempo_paso1 / pruebas_exitosas
    promedio_ram_a_cloud = total_tiempo_paso2 / pruebas_exitosas
    promedio_cloud_a_ram = total_tiempo_paso3 / pruebas_exitosas
    promedio_ram_a_disco = (total_tiempo_paso4a + total_tiempo_paso4b) / pruebas_exitosas
    promedio_limpieza = total_limpieza / pruebas_exitosas
    
    print("--- TIEMPOS PROMEDIO POR NIVEL DE MEMORIA ---")
    print(f"* 1. DISCO LOCAL->RAM (loadRes):   **{promedio_disco_a_ram:.4f} segundos**")
    print(f"* 2. RAM -> CLOUD (upload):          **{promedio_ram_a_cloud:.4f} segundos**")
    print(f"* 3. CLOUD -> RAM (download):        **{promedio_cloud_a_ram:.4f} segundos**")
    print(f"* 4. RAM -> DISCO LOCAL (Guardado): **{promedio_ram_a_disco:.4f} segundos**")
    print(f"* 5. LIMPIEZA (Cloud y Local):         **{promedio_limpieza:.4f} segundos**")
    print("-" * 50)
    
else:
    print("No se pudo completar ni un solo ciclo de prueba exitosamente. No se puede calcular el promedio.")
    
print(resultados_txt) # type: ignore

try:
    with open(NOMBRE_ARCHIVO_RESULTADOS, "w") as f:
        f.write(resultados_txt) # type: ignore
    print(f"\n[EXITO] Resultados guardados en: {os.path.abspath(NOMBRE_ARCHIVO_RESULTADOS)}")
except Exception as e:
    print(f"\n[ERROR] No se pudo guardar el archivo de resultados: {e}")