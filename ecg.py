import wfdb
import os
import matplotlib.pyplot as plt
import numpy as np

db_name = 'mitdb' # base de datos de physionet
local_dir = 'data_ecg' # nombre de carpeta
descargar = [
    '100', '101', '102', '103', '104',
    '105', '106', '107', '108', '109'
]

# Crear la carpeta si no existe
if not os.path.exists(local_dir):
    os.makedirs(local_dir)
    print(f"Carpeta '{local_dir}' creada.")
print("Inicializando descarga")

wfdb.dl_database(
    db_name,
    records=descargar,
    dl_dir=local_dir
)
print("Descarga completada")

# lectura de directiorio local
carpeta_registro_base = local_dir.replace('\\', '/') 

# funcion de graficacion
def graficar_dato_ecg():
    
    num_registro = None

    while num_registro not in descargar:
        num_registro = input(f"Ingrese el numero de registro (disponibles: {', '.join(descargar)}): ")
        if num_registro not in descargar:
            print("Numero de registro no existe")
    limit = 5000  
    print("Cargando datos...")

    ruta_registro = os.path.join(carpeta_registro_base, num_registro).replace('\\', '/')
    
    # Cargar la señal y la metadata usando la ruta
    try:
        record = wfdb.rdrecord(ruta_registro, sampto=limit)
        annotation = wfdb.rdann(ruta_registro, 'atr', sampto=limit)
    except Exception as e:
        print(f"\nNo se pudo leer el archivo: {e}")
        return

    # extracion de datos
    signal = record.p_signal
    fs = record.fs  
    
    # generacion de tiempo
    tiempo = np.arange(len(signal)) / fs 

    plt.figure(figsize=(12, 6))
    plt.plot(tiempo, signal[:, 0], label=record.sig_name[0], color='blue', linewidth=1)

    # Picos QRS o latidos
    qrs_indices_in_range = annotation.sample[annotation.sample < limit]
    qrs_tiempo = qrs_indices_in_range / fs

    plt.plot(qrs_tiempo, signal[qrs_indices_in_range, 0], 'ro', marker='o', markersize=4, label='Picos QRS (Latidos)')
    plt.title(f'Señal ECG - Registro {num_registro} ({record.sig_name[0]})')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Voltaje (mV)')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    graficar_dato_ecg()