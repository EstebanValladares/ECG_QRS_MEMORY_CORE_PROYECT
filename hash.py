from kax import acts
from pprint import pprint
import os
import shutil
import time

# --- CONFIGURACIÓN DE RUTAS Y ARCHIVOS ---
DIRECTORIO = os.path.join('data_ecg')         # Directorio original con los archivos
DIRECTORIO_COPIA = os.path.join('data_ecg_copia') # Directorio de destino para las copias

# Asegurar que el directorio de copias exista
if not os.path.exists(DIRECTORIO_COPIA):
    os.makedirs(DIRECTORIO_COPIA)
    print(f"Directorio de copias creado: {DIRECTORIO_COPIA}")

# Verificar si el directorio original existe y tiene archivos
if not os.path.isdir(DIRECTORIO):
    print(f"\n[ERROR] El directorio '{DIRECTORIO}' no existe. Saliendo del programa.")
    exit()

DATA_ECG = [f for f in os.listdir(DIRECTORIO) if os.path.isfile(os.path.join(DIRECTORIO, f))]
tamTotal = len(DATA_ECG)

if tamTotal == 0:
    print(f"\n[ADVERTENCIA] El directorio '{DIRECTORIO}' está vacío. Saliendo del programa.")
    exit()
    
USER = os.getenv("USER") # usuario por defecto

# --- CONEXIÓN A SERVIDOR KAX ---
acts.setUrl("http://148.247.201.210:5060/api") 
acts.setStorageUrl("http://148.247.201.210:5070/api") 
acts.setBrokerPort(1883)
acts.setBrokerUrl("148.247.201.226")

# --- FUNCIONES DE PRUEBA ---

def prueba_disco_local(origen, destino, nombre_archivo):
    """Mide el tiempo de copiado de archivo usando solo el disco (shutil.copy)."""
    try:
        start_time = time.time()
        # Copia directa de disco a disco
        shutil.copy(origen, destino)
        end_time = time.time()
        duration = end_time - start_time
        return duration, True
    except Exception as e:
        print(f"   -> [ERROR] Falló Disco Local para {nombre_archivo}: {e}")
        return 0.0, False

def prueba_ram_compartida(origen, destino_dir, nombre_archivo):
    """Mide el tiempo de copiado a través de la RAM compartida (loadRes + getRes + saveFile)."""
    hash_id = None
    try:
        # 1. Disco -> RAM (loadRes)
        metadata_local = acts.loadRes(origen)
        file_info = metadata_local['resources'][0]
        hash_id = file_info['hash']

        start_time = time.time()
        
        # 2. RAM -> Datos (getRes)
        datos_archivo = acts.getRes(metadata_local['resources'][0])
        
        # 3. Datos -> Disco (saveFile)
        acts.saveFile(destino_dir, datos_archivo, nombre_archivo)
        
        end_time = time.time()
        duration = end_time - start_time
        return duration, True
        
    except Exception as e:
        print(f"   -> [ERROR] Falló RAM Compartida para {nombre_archivo}: {e}")
        return 0.0, False
        
    finally:
        # Limpieza de RAM
        if hash_id:
            try:
                acts.removeShm(hash_id)
            except:
                pass

def prueba_cloud(origen, destino_dir, nombre_archivo):
    """Mide el tiempo de transferencia completa: Disco -> RAM -> Cloud -> RAM -> Disco."""
    hash_id = None
    try:
        # --- SUBIDA: Disco -> RAM -> Cloud ---
        metadata_local = acts.loadRes(origen)
        file_info = metadata_local['resources'][0]
        hash_id = file_info['hash']
        
        start_time = time.time()
        
        # 1. RAM -> Cloud (upload)
        acts.uploadToCloudFromMemory(metadata_local)
        
        # --- BAJADA: Cloud -> RAM -> Disco ---
        # 2. Cloud -> RAM (download)
        download_metadata = acts.downloadFromCloud(hash_id)
        
        # 3. RAM -> Datos -> Disco (getRes + saveFile)
        datos_archivo = acts.getRes(download_metadata['file'])
        acts.saveFile(destino_dir, datos_archivo, nombre_archivo)
        
        end_time = time.time()
        duration = end_time - start_time
        return duration, True
        
    except Exception as e:
        print(f"   -> [ERROR] Falló Cloud para {nombre_archivo}: {e}")
        return 0.0, False
        
    finally:
        # Limpieza: Cloud y RAM
        if hash_id:
            try:
                acts.removeShmFromCloud(hash_id)
                acts.removeShm(hash_id)
            except:
                pass


# --- BUCLE PRINCIPAL DE PRUEBAS ---
archivos_para_copiar = DATA_ECG

# Inicializar archivos de registro
with open("TLocal.txt", "w") as f: f.write("")
with open("TRAM.txt", "w") as f: f.write("")
with open("TCloud.txt", "w") as f: f.write("")

print("-" * 70)
print(f"Iniciando pruebas para {tamTotal} archivos.")
print("-" * 70)

for idx, nombre_archivo in enumerate(archivos_para_copiar, 1):
    ruta_completa_origen = os.path.join(DIRECTORIO, nombre_archivo)
    ruta_completa_destino = os.path.join(DIRECTORIO_COPIA, nombre_archivo)
    
    print(f"\n[{idx}/{tamTotal}] Procesando archivo: {nombre_archivo}")
    
    # --- PRUEBA 1: DISCO LOCAL (shutil.copy) ---
    duracion_local, exito_local = prueba_disco_local(ruta_completa_origen, ruta_completa_destino, nombre_archivo)
    
    if exito_local:
        print(f"  -> 1. DISCO LOCAL: {duracion_local:.4f}s")
        try:
            with open("TLocal.txt", "a") as file:
                file.write(f"{duracion_local}\n")
        except IOError:
            print("   -> [ERROR] No se pudo escribir en TLocal.txt")

    # --- PRUEBA 2: RAM COMPARTIDA (loadRes + saveFile) ---
    duracion_ram, exito_ram = prueba_ram_compartida(ruta_completa_origen, DIRECTORIO_COPIA, nombre_archivo)

    if exito_ram:
        print(f"  -> 2. RAM COMPARTIDA: {duracion_ram:.4f}s")
        try:
            with open("TRAM.txt", "a") as file:
                file.write(f"{duracion_ram}\n")
        except IOError:
            print("   -> [ERROR] No se pudo escribir en TRAM.txt")

    # --- PRUEBA 3: NUBE (Cloud) ---
    duracion_cloud, exito_cloud = prueba_cloud(ruta_completa_origen, DIRECTORIO_COPIA, nombre_archivo)

    if exito_cloud:
        print(f"  -> 3. CLOUD: {duracion_cloud:.4f}s")
        try:
            with open("TCloud.txt", "a") as file:
                file.write(f"{duracion_cloud}\n")
        except IOError:
            print("   -> [ERROR] No se pudo escribir en TCloud.txt")
        
    # Opcional: Eliminar el archivo copiado/descargado para evitar conflictos
    try:
        if os.path.exists(ruta_completa_destino):
            os.remove(ruta_completa_destino)
    except Exception as e:
        print(f"   -> [ADVERTENCIA] No se pudo eliminar la copia/descarga para el archivo {nombre_archivo}: {e}")

print(f"\n{'=' * 70}")
print(f"FINALIZADAS las pruebas para los {tamTotal} archivos.")
print("Los tiempos se han guardado en TLocal.txt, TRAM.txt y TCloud.txt.")
print(f"{'=' * 70}\n")