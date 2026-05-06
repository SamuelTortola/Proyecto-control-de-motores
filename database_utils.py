import sqlite3
import os
import sys
import shutil

# ----------------------------------------------------------------------
# FUNCION PARA LEER RECURSOS (SOLO LECTURA)
# ----------------------------------------------------------------------
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso.
    SOLO para lectura (iconos, PDF, BD plantilla).
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)  # Directorio actual del script

    return os.path.join(base_path, relative_path)
            #os.path.join sirve para unir rutas de forma correcta según el SO


# ----------------------------------------------------------------------
# RUTA BASE DEL PROGRAMA (ESCRITURA)
# ----------------------------------------------------------------------
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) # Si está congelado con PyInstaller, obtiene la ruta del ejecutable
    else:
        return os.path.dirname(os.path.abspath(__file__)) #os.path.abspath obtiene la ruta absoluta, que es útil si se ejecuta desde otro directorio


BASE_PATH = get_base_path()
DATA_DIR = os.path.join(BASE_PATH, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data_base.db")


# ----------------------------------------------------------------------
# INICIALIZAR BASE DE DATOS (UNA SOLA VEZ)
# ----------------------------------------------------------------------
def inicializar_base_datos():
    os.makedirs(DATA_DIR, exist_ok=True) # Crea el directorio "data" si no existe

    if not os.path.exists(DATABASE_PATH): # Si la base de datos no existe, la copia desde los recursos
        db_origen = resource_path(os.path.join("Recursos", "Data_base.db")) # Ruta del archivo de base de datos de origen
        shutil.copy2(db_origen, DATABASE_PATH) # Copia el archivo de base de datos al directorio de datos


# ----------------------------------------------------------------------
# CONEXIÓN SQLITE
# ----------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
