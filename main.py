import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QApplication,QLineEdit,QFrame,QComboBox, QWidget, QScrollArea, QPushButton, QLabel, QInputDialog, QGridLayout, QGroupBox, QVBoxLayout, QSpacerItem, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QVBoxLayout, QListWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt,  QSize, QRect
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon, QImage, QPainter

import fitz  # PyMuPDF

from motores import VentanaLinea, SeleccionAreaDialog
from database_utils import get_db_connection, resource_path, inicializar_base_datos




OFFSET = 40


 #****************************************** Clase para eliminar un área o máquina**************************************************
class EliminarAreaMaquina(QDialog):
    def __init__(self, lineas, areas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eliminar Área/Máquina")
        self.setFixedSize(400, 350)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QComboBox {
                font-size: 18px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

        layout = QVBoxLayout()

        self.label_combo = QLabel("Seleccione la línea:")
        self.combo_lineas = QComboBox()
        self.combo_lineas.addItems(lineas)  # Añade las líneas al combo box
        self.combo_lineas.currentIndexChanged.connect(self.actualizar_areas)
        
        self.label_combo2 = QLabel("Seleccione el área/máquina a eliminar:")
        self.combo_areas = QComboBox()
        
        self.actualizar_areas()  # Llenar al inicio
        


        botones = QHBoxLayout()
        self.btn_ok = QPushButton("Eliminar")
        self.btn_ok.setFixedHeight(50)
        self.btn_ok.setFixedWidth(150)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(50)
        self.btn_cancelar.setFixedWidth(150)
        botones.addWidget(self.btn_ok)
        botones.addWidget(self.btn_cancelar)

        layout.addWidget(self.label_combo)
        layout.addWidget(self.combo_lineas)
        layout.addWidget(self.label_combo2)
        layout.addWidget(self.combo_areas)
        layout.addLayout(botones)
        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.eliminar)  # Conecta el botón de crear para obtener los datos
        #self.btn_ok.clicked.connect(self.accept)  # Cierra el diálogo y retorna los datos si se guardaron correctamente
        # Conecta el botón de cancelar para cerrar el diálogo
        self.btn_cancelar.clicked.connect(self.reject)
    
    def eliminar(self):
        nombre_linea = self.combo_lineas.currentText()
        nombre_area = self.combo_areas.currentText()
        if not nombre_linea or not nombre_area:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una línea y un área/máquina.")
            return None  # Retorna None si los datos no son válidos
        respuesta = QMessageBox.question(self, "Confirmar", "¿Está seguro de eliminar el área/máquina?", QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT codigo_motor
                    FROM motores
                    WHERE id_area = (
                        SELECT id_area FROM areas WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
                    )
                    """, (nombre_area, nombre_linea))
                motores = cursor.fetchall()


                for (codigo_motor,) in motores:

                    cursor.execute("""
                    SELECT id_termografia
                    FROM eventos
                    WHERE id_motor = (SELECT id_motor FROM motores WHERE codigo_motor = ?)
                    AND tipo_evento = "Inspección Termográfica"
                    """, (codigo_motor,))
                
                    eventos = cursor.fetchall()

                    for (id_termo,) in eventos:
                        # Paso 1: Obtener rutas de imágenes asociadas al id_termo
                        if id_termo:
                            cursor.execute("SELECT coj_delantero, coj_trasero, Estator FROM Termografia WHERE id_termo = ?", 
                                        (id_termo,))
                            rutas = cursor.fetchone() # Obtiene las rutas de las imágenes, fetchall() devuelve una tupla y fetchone() un solo registro
                            
                            if rutas:
                                # Paso 2: Borrar Archivos del Sistema Operativo
                                for ruta_imagen in rutas:
                                    if ruta_imagen and os.path.exists(ruta_imagen):
                                        try:
                                            # os.remove() borra un archivo. Si fueran carpetas, usaría shutil.rmtree()
                                            os.remove(ruta_imagen)
                                        # print(f"Archivo eliminado: {ruta_imagen}")
                                        except OSError as e:
                                            print(f"Error al eliminar archivo {ruta_imagen}: {e}")

    
                    cursor.execute("""
                        SELECT imagen_motor
                        FROM motores
                        WHERE codigo_motor = ?
                        """, (codigo_motor,))
                    resultado = cursor.fetchone()

                    # 1. Definir la carpeta donde se encuentran las imágenes
                    if getattr(sys, 'frozen', False):
                        base = os.path.dirname(sys.executable)
                    else:
                        base = os.path.dirname(os.path.abspath(__file__))

                    CARPETA_IMAGENES = os.path.join(base, "Fotos")
                    

                                    

                    if resultado:
                        nombre_archivo_motor = resultado[0] 
                        
                        if nombre_archivo_motor: # Se asegura de que el campo no sea nulo o vacío
                            
                            # CONSTRUIR LA RUTA COMPLETA 
                            ruta_completa_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo_motor)
                            

                            # Usar la ruta completa para verificar y eliminar
                            if os.path.exists(ruta_completa_imagen):
                                try:
                                    # USAR RUTA COMPLETA PARA ELIMINAR
                                    os.remove(ruta_completa_imagen)
                                    
                                # print(f"Imagen del motor eliminada: {ruta_completa_imagen}")

                                except OSError as e:
                                    # Esto sucede si el archivo existe pero no se tienen permisos para borrarlo
                                    print(f"Error al eliminar la imagen del motor {ruta_completa_imagen}: {e}")
                            
                            else:
                                print(f"Advertencia: El archivo '{nombre_archivo_motor}' no se encontró en la carpeta '{CARPETA_IMAGENES}'. ")



                cursor.execute("""
                    DELETE FROM areas
                    WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
                """, (nombre_area, nombre_linea))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Éxito", "Área/Máquina eliminada correctamente.")
                self.accept()  # Cierra el diálogo y retorna los datos si se guardaron correctamente
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el área/máquina: {e}")

    def actualizar_areas(self):
        nombre_linea = self.combo_lineas.currentText()
        self.combo_areas.clear()
        if not nombre_linea:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.nombre
            FROM areas a
            JOIN lineas l ON a.id_linea = l.id_linea
            WHERE l.nombre = ?
        """, (nombre_linea,))
        areas = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.combo_areas.addItems(areas)
        
#****************************************** Clase para eliminar un Motor**************************************************
class EliminarMotor(QDialog):
    def __init__(self, lineas, areas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eliminar Motor")
        self.setFixedSize(400, 350)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QComboBox {
                font-size: 18px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

        layout = QVBoxLayout()

        self.label_combo = QLabel("Seleccione la línea:")
        self.combo_lineas = QComboBox()
        self.combo_lineas.addItems(lineas)  # Añade las líneas al combo box
        self.combo_lineas.currentIndexChanged.connect(self.actualizar_areas)
        
        self.label_combo2 = QLabel("Seleccione el área/máquina:")
        self.combo_areas = QComboBox()
        
        self.actualizar_areas()  # Llenar al inicio
        self.combo_areas.currentIndexChanged.connect(self.actualizar_motores)
        
        self.label_combo3 = QLabel("Seleccione el motor a eliminar:")
        self.combo_motores = QComboBox()
        self.actualizar_motores()  # Llenar la lista de motores al inicio

        botones = QHBoxLayout()
        self.btn_ok = QPushButton("Eliminar")
        self.btn_ok.setFixedHeight(50)
        self.btn_ok.setFixedWidth(150)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(50)
        self.btn_cancelar.setFixedWidth(150)
        botones.addWidget(self.btn_ok)
        botones.addWidget(self.btn_cancelar)
        

        layout.addWidget(self.label_combo)
        layout.addWidget(self.combo_lineas)
        layout.addWidget(self.label_combo2)
        layout.addWidget(self.combo_areas)
        layout.addWidget(self.label_combo3)
        layout.addWidget(self.combo_motores)
        layout.addLayout(botones)

        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.eliminar)  
        
        # Conecta el botón de cancelar para cerrar el diálogo
        self.btn_cancelar.clicked.connect(self.reject)
    
    def actualizar_motores(self):
        nombre_linea = self.combo_lineas.currentText()
        nombre_area = self.combo_areas.currentText()
        self.combo_motores.clear()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.codigo_motor
                FROM motores m
                JOIN areas a ON m.id_area = a.id_area
                JOIN lineas l ON a.id_linea = l.id_linea
                WHERE l.nombre = ? AND a.nombre = ?
            """, (nombre_linea, nombre_area))
            motores = [row[0] for row in cursor.fetchall()]
            self.combo_motores.addItems(motores)
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron obtener los motores: {e}")

    
    def eliminar(self):
        nombre_linea = self.combo_lineas.currentText()
        nombre_area = self.combo_areas.currentText()
        codigo_motor = self.combo_motores.currentText()
        if not nombre_linea or not nombre_area or not codigo_motor:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una línea, un área/máquina y un motor.")
            return None
        respuesta = QMessageBox.question(self, "Confirmar", f"¿Está seguro de eliminar el motor '{codigo_motor}'?", QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                SELECT id_termografia
                FROM eventos
                WHERE id_motor = (SELECT id_motor FROM motores WHERE codigo_motor = ?)
                AND tipo_evento = "Inspección Termográfica"
                 """, (codigo_motor,))
            
                eventos = cursor.fetchall()

                for (id_termo,) in eventos:
                    # Paso 1: Obtener rutas de imágenes asociadas al id_termo
                    if id_termo:
                        cursor.execute("SELECT coj_delantero, coj_trasero, Estator FROM Termografia WHERE id_termo = ?", 
                                    (id_termo,))
                        rutas = cursor.fetchone() # Obtiene las rutas de las imágenes, fetchall() devuelve una tupla y fetchone() un solo registro
                        
                        if rutas:
                            # Paso 2: Borrar Archivos del Sistema Operativo
                            for ruta_imagen in rutas:
                                if ruta_imagen and os.path.exists(ruta_imagen):
                                    try:
                                        # os.remove() borra un archivo. Si fueran carpetas, usaría shutil.rmtree()
                                        os.remove(ruta_imagen)
                                       # print(f"Archivo eliminado: {ruta_imagen}")
                                    except OSError as e:
                                      print(f"Error al eliminar archivo {ruta_imagen}: {e}")

        

                cursor.execute("""
                    SELECT imagen_motor
                    FROM motores
                    WHERE codigo_motor = ?
                    """, (codigo_motor,))
                resultado = cursor.fetchone()

                # 1. Definir la carpeta donde se encuentran las imágenes
                if getattr(sys, 'frozen', False):
                    base = os.path.dirname(sys.executable)
                else:
                    base = os.path.dirname(os.path.abspath(__file__))

                CARPETA_IMAGENES = os.path.join(base, "Fotos")

               

                if resultado:
                    nombre_archivo_motor = resultado[0] 
                    
                    if nombre_archivo_motor: # Se asegura de que el campo no sea nulo o vacío
                        
                        # CONSTRUIR LA RUTA COMPLETA 
                        ruta_completa_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo_motor)

                        # Usar la ruta completa para verificar y eliminar
                        if os.path.exists(ruta_completa_imagen):
                            try:
                                # USAR RUTA COMPLETA PARA ELIMINAR
                                os.remove(ruta_completa_imagen)
                                
                               # print(f"Imagen del motor eliminada: {ruta_completa_imagen}")

                            except OSError as e:
                                # Esto sucede si el archivo existe pero no se tienen permisos para borrarlo
                                print(f"Error al eliminar la imagen del motor {ruta_completa_imagen}: {e}")
                           
                        else:
                            print(f"Advertencia: El archivo '{nombre_archivo_motor}' no se encontró en la carpeta '{CARPETA_IMAGENES}'. ")

                cursor.execute("""
                                    DELETE FROM motores
                                    WHERE codigo_motor = ? AND id_area = (
                                        SELECT id_area FROM areas WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
                                    )
                                """, (codigo_motor, nombre_area, nombre_linea))


                conn.commit()
                conn.close()
                QMessageBox.information(self, "Éxito", "Motor eliminado correctamente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el motor: {e}")
        
        
    def actualizar_areas(self):
        nombre_linea = self.combo_lineas.currentText()
        self.combo_areas.clear()
        if not nombre_linea:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.nombre
            FROM areas a
            JOIN lineas l ON a.id_linea = l.id_linea
            WHERE l.nombre = ?
        """, (nombre_linea,))
        areas = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.combo_areas.addItems(areas)   
        
        
        
 #****************************************** Clase para mostrar detalles rapidos de motor**************************************************
class DetalleMotorDialog(QDialog):
    def __init__(self, datos_motor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalle del Motor")
        self.setMinimumSize(600, 600)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 12px;
            }
            QLabel {
                font-size: 16px;
                color: #333;
                margin-bottom: 6px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            
            QPushButton:hover {
                background-color: #1565c0;
            }
            
            QScrollArea {
                border: none;
            }
        """)

        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        form_layout = QVBoxLayout(contenido)

        for clave, valor in datos_motor.items():
            if clave == "Nombre_persona":
                etiqueta = QLabel(f"<b>Nombre persona que registró  el motor:</b> {valor if valor else 'N/A'}")
            else:
                etiqueta = QLabel(f"<b>{clave.replace('_', ' ').capitalize()}:</b> {valor if valor else 'N/A'}")
            form_layout.addWidget(etiqueta)

        scroll.setWidget(contenido)
        layout.addWidget(scroll)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignCenter)

        self.setLayout(layout)

 #****************************************** Clase para crear nuevas áreas y máquinas**************************************************
class DialogoCrearAreaMaquina(QDialog):
    def __init__(self, lineas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Área/Máquina")
        self.setFixedSize(400, 350)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QComboBox {
                font-size: 18px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

        layout = QVBoxLayout()

        self.label_combo = QLabel("Seleccione la línea:")
        self.combo_lineas = QComboBox()
        self.combo_lineas.addItems(lineas)  # Añade las líneas al combo box

        self.label_area = QLabel("Nombre del área/máquina:")
        self.input_area = QLineEdit()
        self.input_area.setMaxLength(35)  # Limita a 35 caracteres

        botones = QHBoxLayout()
        self.btn_ok = QPushButton("Crear")
        self.btn_ok.setFixedHeight(50)
        self.btn_ok.setFixedWidth(150)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(50)
        self.btn_cancelar.setFixedWidth(150)
        botones.addWidget(self.btn_ok)
        botones.addWidget(self.btn_cancelar)

        layout.addWidget(self.label_combo)
        layout.addWidget(self.combo_lineas)
        layout.addWidget(self.label_area)
        layout.addWidget(self.input_area)
        layout.addLayout(botones)
        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.obtener_datos)  # Conecta el botón de crear para obtener los datos
        self.btn_ok.clicked.connect(self.accept)  # Cierra el diálogo y retorna los datos si se guardaron correctamente
        # Conecta el botón de cancelar para cerrar el diálogo
        self.btn_cancelar.clicked.connect(self.reject)

    
    def obtener_datos(self):
        nombre_linea = self.combo_lineas.currentText()
        nombre_area = self.input_area.text().strip()
        if not nombre_linea or not nombre_area:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una línea y escribir un nombre de área/máquina.")
            return None  # Retorna None si los datos no son válidos
        
        
         # Guardar en la base de datos
        try:
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
                # Verifica si ya existe un área con ese nombre en la misma línea
            cursor.execute("""
                SELECT 1 FROM areas
                WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
            """, (nombre_area, nombre_linea))
            existe = cursor.fetchone()
            if existe:
                QMessageBox.warning(self, "Duplicado", "Ya existe un área/máquina con ese nombre en la línea seleccionada.")
                conn.close()
                return
            
            
            
            # Si no existe, inserta el nuevo área/máquina
            cursor.execute("""
                INSERT INTO areas (nombre, id_linea)
                VALUES (?, (SELECT id_linea FROM lineas WHERE nombre = ?))
            """, (nombre_area, nombre_linea))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Área/Máquina creada correctamente.")
            return nombre_linea, nombre_area # Retorna los datos si se guardaron correctamente
            # Si se guardó correctamente, puedes cerrar el diálogo
            self.accept()  # Cierra el diálogo y retorna los datos
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el área/máquina: {e}")
            return None



 #****************************************** Clase para registrar un nuevo motor**************************************************
class DialogoCrearMotor(QDialog):
    def __init__(self, lineas, areas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Motor")
        self.setFixedSize(400, 350)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QComboBox {
                font-size: 18px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            
            
        """)

        layout = QVBoxLayout()

        self.label_combo = QLabel("Seleccione la línea:")
        self.combo_lineas = QComboBox()
        self.combo_lineas.addItems(lineas)  # Añade las líneas al combo box
        self.combo_lineas.currentIndexChanged.connect(self.actualizar_areas)
        
        self.label_combo2 = QLabel("Seleccione el área/máquina:")
        self.combo_areas = QComboBox()
        
        self.actualizar_areas()  # Llenar al inicio

        botones = QHBoxLayout()
        self.btn_ok = QPushButton("Crear")
        self.btn_ok.setFixedHeight(50)
        self.btn_ok.setFixedWidth(150)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(50)
        self.btn_cancelar.setFixedWidth(150)
        botones.addWidget(self.btn_ok)
        botones.addWidget(self.btn_cancelar)

        layout.addWidget(self.label_combo)
        layout.addWidget(self.combo_lineas)
        layout.addWidget(self.label_combo2)
        layout.addWidget(self.combo_areas)
        layout.addLayout(botones)
        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.crear_formulario)  # Conecta el botón de crear para obtener los datos
        #self.btn_ok.clicked.connect(self.accept)  # Cierra el diálogo y retorna los datos si se guardaron correctamente
        # Conecta el botón de cancelar para cerrar el diálogo
        self.btn_cancelar.clicked.connect(self.reject)

    
    def crear_formulario(self):
        nombre_linea = self.combo_lineas.currentText()
        nombre_area = self.combo_areas.currentText()
        if not nombre_linea or not nombre_area:
            QMessageBox.warning(self, "Advertencia", "Seleccione línea y área válidas.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_area FROM areas
            WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
        """, (nombre_area, nombre_linea))
        resultado = cursor.fetchone() # Obtiene el id del área seleccionada
        conn.close()

        if resultado:
            id_area = resultado[0]
            formulario = FormularioMotor(id_area)
            formulario.exec_()
            self.accept() # Cierra el diálogo y retorna los datos si se guardaron correctamente
        else:
            QMessageBox.critical(self, "Error", "Área no encontrada.")
            
    def actualizar_areas(self):
        nombre_linea = self.combo_lineas.currentText()
        self.combo_areas.clear()
        if not nombre_linea:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.nombre
            FROM areas a
            JOIN lineas l ON a.id_linea = l.id_linea
            WHERE l.nombre = ?
        """, (nombre_linea,))
        areas = [row[0] for row in cursor.fetchall()]  # Obtiene las áreas de la línea seleccionada
        #feature: fetchall() obtiene todas las filas del resultado de la consulta
         #feature: cursor es un objeto que permite ejecutar consultas y recuperar resultados
        conn.close()
        self.combo_areas.addItems(areas)


 #****************************************** Clase para realizar el formulario para un nuevo motor**************************************************
class FormularioMotor(QDialog):
    def __init__(self, id_area, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar nuevo motor")
        self.setFixedSize(900, 700)  # Más ancho y alto
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.id_area = id_area

        # Widget contenedor para el formulario
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QComboBox {
                font-size: 18px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)


        self.campos = {}
        campos_motor = [
            "Código de motor", "Código de equipo", "Modelo de motor", "Función", "Marca", "Tipo de motor", "Potencia (HP,KW)", "Voltaje Armadura (V)",
            "Voltaje fuente/campo (V)", "Amperaje (A)", "Revoluciones por minuto (rpm)", "Frecuencia (Hz)", "Amperaje de excitación (A)", "Temperatura de trabajo", "Antigüedad",
            "Ubicación o posición de montaje", "Cojinete frontal y Código de repuesto", "Cojinete trasero y Código de repuesto", "Ciclo mantenimiento", "Observaciones", "Nombre persona que registra motor"
        ]
        for campo in campos_motor:
            label = QLabel(campo.replace("_", " ").capitalize() + ":") # Reemplaza guiones bajos por espacios y capitaliza, capataliza quiere decir que pone la primera letra en mayúscula
            label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1976d2;")
           
            
            layout.addWidget(label)
            
            # Detecta campos especiales
            if campo == "Temperatura de trabajo":
                sub_layout = QHBoxLayout()
                entrada = QLineEdit()
                unidad = QComboBox()
                unidad.addItems(["°C", "°F"])
                sub_layout.addWidget(entrada)
                sub_layout.addWidget(unidad)
                layout.addLayout(sub_layout)
                self.campos[campo] = (entrada, unidad)
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")

            elif campo == "Potencia (HP,KW)":
                sub_layout = QHBoxLayout()
                entrada = QLineEdit()
                unidad = QComboBox()
                unidad.addItems(["HP", "kW"])
                sub_layout.addWidget(entrada)
                sub_layout.addWidget(unidad)
                layout.addLayout(sub_layout)
                self.campos[campo] = (entrada, unidad)
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")

            elif campo == "Antigüedad":
                sub_layout = QHBoxLayout()
                entrada = QLineEdit()
                unidad = QComboBox()
                unidad.addItems(["días", "meses", "años"])
                sub_layout.addWidget(entrada)
                sub_layout.addWidget(unidad)
                layout.addLayout(sub_layout)
                self.campos[campo] = (entrada, unidad)
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")


            elif campo == "Tipo de motor":
                sub_layout = QHBoxLayout()
                entrada = QLineEdit()
                unidad = QComboBox()
                unidad.addItems(["DC", "AC","servomotor","otro(especificar en observaciones)"])
                sub_layout.addWidget(entrada)
                sub_layout.addWidget(unidad)
                layout.addLayout(sub_layout)
                self.campos[campo] = (entrada, unidad)
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")

            elif campo == "Ciclo mantenimiento":
                sub_layout = QHBoxLayout()
                entrada = QLineEdit()
                unidad = QComboBox()
                unidad.addItems(["horas", "dias", "meses"])
                sub_layout.addWidget(entrada)
                sub_layout.addWidget(unidad)
                layout.addLayout(sub_layout)
                self.campos[campo] = (entrada, unidad)
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")
                  

            else:
                entrada = QLineEdit()
                
                # Limitar campo "Función" a 30 caracteres
                if campo == "Función":
                    entrada.setMaxLength(50)
        
                layout.addWidget(entrada)
                self.campos[campo] = entrada
                entrada.setStyleSheet("font-size: 20px; padding: 10px;")


        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet("font-size: 22px; padding: 12px 24px;")
        self.btn_guardar.clicked.connect(self.guardar_motor)
        layout.addWidget(self.btn_guardar)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def guardar_motor(self):
        # Recolecta datos
        datos = {}
        for campo, widget in self.campos.items():
            if isinstance(widget, tuple):  # Tiene selector de unidad
                valor = widget[0].text().strip() # Obtiene el texto del QLineEdit
                unidad = widget[1].currentText() # Obtiene el texto del QComboBox
                datos[campo] = f"{valor} {unidad}" #guarda el valor y la unidad
            else:
                datos[campo] = widget.text().strip()  # Obtiene el texto del QLineEdit

        campo_nombre = "Nombre persona que registra motor"
        if datos.get(campo_nombre):
            datos[campo_nombre] = datos[campo_nombre].title()  # Capitaliza el nombre completo

        
        if not datos["Código de motor"] or not datos["Código de equipo"] or not datos["Modelo de motor"] or not datos["Nombre persona que registra motor"]:
            QMessageBox.warning(self, "Campos incompletos", "Código del motor, equipo, modelo de motor y nombre de persona que regitra son obligatorios.")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            codigo_motor_nuevo = datos["Código de motor"]
            
            # 1. Chequeo global: Busca el motor en CUALQUIER área y trae la ubicación.
            cursor.execute("""
                SELECT 
                    L.nombre AS linea_nombre,  
                    A.nombre AS area_nombre,
                    M.id_area
                FROM motores AS M
                JOIN areas AS A ON M.id_area = A.id_area
                JOIN lineas AS L ON A.id_linea = L.id_linea
                WHERE M.codigo_motor = ?
            """, (codigo_motor_nuevo,))


            
            duplicados = cursor.fetchall() # Obtiene todas las filas que coinciden con el código de motor
           
            
            existe_en_area_actual = False
            duplicados_externos = []

            for linea_nombre, area_nombre, id_area_encontrada in duplicados:
                if id_area_encontrada == self.id_area:
                    existe_en_area_actual = True
                else:
                    duplicados_externos.append((linea_nombre, area_nombre))

            # 2. Manejo de Duplicados

            # A. Si ya existe en el área actual, detener 
            if existe_en_area_actual:
                QMessageBox.warning(self, "Duplicado", "Ya existe un motor con ese código en esta área/máquina.")
                conn.close()
                return

            # B. Si existe en otras áreas, preguntar al usuario si desea continuar
            if duplicados_externos:
                # Construir el mensaje con las ubicaciones encontradas
                mensaje = f"Ya existe un motor con el código '{codigo_motor_nuevo}' en las siguientes ubicaciones:\n"
                for linea, area in duplicados_externos:
                    mensaje += f"- Línea: {linea}, Área/Máquina: {area}\n"
                
                mensaje += "\n¿Desea crear este motor en el área actual de todas formas?"
                
                # Mostrar el diálogo de confirmación (Sí/No)
                respuesta = QMessageBox.question(
                    self, 
                    "Motor Duplicado Global", 
                    mensaje,
                    QMessageBox.Yes | QMessageBox.No
                )

                if respuesta == QMessageBox.No:
                    conn.close()
                    return # Detener la creación si el usuario elige NO

        # Si no existe, inserta el motor
        
            cursor.execute("""
                    INSERT INTO motores (
                        codigo_motor, codigo_equipo, datos_motor, funcion, marca, tipo_motor,
                        hp_kw, voltaje, voltaje_fuente, amperaje_fabricante, rpm, frecuencia,
                        corriente_trabajo, temperatura_trabajo, ultimo_mantenimiento,
                        proximo_mantenimiento, cojinete_frontal,
                        cojinete_trasero, ciclo_mantenimiento, observaciones, Nombre_persona, Fecha_registro, id_area
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datos["Código de motor"],
                    datos["Código de equipo"],
                    datos["Modelo de motor"],
                    datos["Función"],
                    datos["Marca"],
                    datos["Tipo de motor"],
                    datos["Potencia (HP,KW)"],
                    datos["Voltaje Armadura (V)"],
                    datos["Voltaje fuente/campo (V)"],
                    datos["Amperaje (A)"],
                    datos["Revoluciones por minuto (rpm)"],
                    datos["Frecuencia (Hz)"],
                    datos["Amperaje de excitación (A)"],
                    datos["Temperatura de trabajo"],
                    datos["Antigüedad"],
                    datos["Ubicación o posición de montaje"],
                    datos["Cojinete frontal y Código de repuesto"],
                    datos["Cojinete trasero y Código de repuesto"],
                    datos["Ciclo mantenimiento"],
                    datos["Observaciones"],
                    datos["Nombre persona que registra motor"],
                    pd.Timestamp.now().strftime('%d-%m-%Y %H:%M:%S'),  # Fecha y hora actual
                    self.id_area
                ))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Motor registrado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el motor:\n{e}")




 #****************************************** Clase para mostrar la ventana principal**************************************************

class VentanaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Motores - PAINSA K10")
        
        self.ruta_db = resource_path(os.path.join("Recursos", "Data_base.db"))

        if not os.path.exists(self.ruta_db): # Verifica si la base de datos existe, si no envia mensaje de error
            QMessageBox.critical(self, "Error", "La base de datos no se encuentra en la ruta especificada.")
            sys.exit(1)
            
        self.frame_contenedor = QFrame()
        self.frame_contenedor.setObjectName("ventanaPrincipal")

        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        self.setStyleSheet("""
            #ventanaPrincipal {
                background-color: #f4f6fb;
                border: 6px solid #229954;
                border-radius: 10px;
            }
            QWidget { background-color: #f4f6fb; font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px; }
            
            QPushButton { background-color: #1976d2; color: white; border-radius: 12px; padding: 12px 24px; margin: 8px 0; font-size: 18px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #1565c0; }
            QLabel { color: #222; }
            
            QGroupBox {
            border: 2px solid #229954;
            border-radius: 10px;
            margin-top: 10px;
            background: #eafaf1;
                }
            QGroupBox:title {    
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #229954;
                font-size: 20px;
                font-weight: bold;
            }
            
            QDialog {
                background-color: #f4f6fb;
                border: 4px solid #229954;
                border-radius: 14px;
                
            }
            
             QScrollArea {
                border: none;
                background-color: #f4f6fb;
            }
            QScrollBar:vertical {
                background: #f4f6fb;
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #229954;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            
        """)

        self.layout_grid = QGridLayout() #Se crea un layout de tipo grid
        self.layout_grid.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout_grid)
        self.max_columnas = 4
        
        
        self.frame_contenedor.setLayout(self.layout_grid)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.frame_contenedor)
        self.setLayout(main_layout)

        # Fila 0: Imagen
        imagen_label = QLabel() #QLAbel para la imagen
        # Crea la ruta completa al archivo de imagen
        logo_path = resource_path(os.path.join( "Recursos", "Logo.png"))

        # Verifica si el archivo existe
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(800, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            imagen_label.setPixmap(pixmap)
        else:
            imagen_label.setText("Logo no encontrado.")
        imagen_label.setAlignment(Qt.AlignCenter)
        self.layout_grid.addWidget(imagen_label, 0, 0, 1, self.max_columnas) # Añade la imagen en la fila 0, ocupando todas las columnas


        # Fila 1: Espacio vertical
        self.layout_grid.addItem(QSpacerItem(5, 5, QSizePolicy.Minimum, QSizePolicy.Fixed), 1, 0, 1, self.max_columnas) # Espacio vertical entre la imagen y el título

        # Fila 2: Label
        titulo_label = QLabel("Menú Principal:")
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setStyleSheet("""
            background-color: #229954;
            color: #fff;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 2px 0;
            margin-bottom: 5px;
            letter-spacing: 2px;
        """)
        
        self.layout_grid.addWidget(titulo_label, 2, 0, 1, self.max_columnas) #2, 0, 1, self.max_columnas) # Añade el título en la fila 2, ocupando todas las columnas, 0 significa que empieza en la columna 0, 1 significa que ocupa una fila, y self.max_columnas significa que ocupa todas las columnas disponibles

        # Fila 3: Grupo de gestión
        ancho = 335

        # Botones de líneas
        self.creacion_label = QPushButton("Crear nueva línea")
        self.creacion_label.clicked.connect(self.Nueva_linea)
        self.creacion_label.setFixedWidth(ancho)
        self.eliminar_label = QPushButton("Eliminar línea")
        self.eliminar_label.clicked.connect(self.Eliminar_linea)
        self.eliminar_label.setFixedWidth(ancho)
        self.modificar_label = QPushButton("Modificar línea")
        self.modificar_label.clicked.connect(self.Modificar_linea)
        self.modificar_label.setFixedWidth(ancho)

        # Botones de máquinas
        self.creacion_maquina = QPushButton("Crear nueva Área/Máquina")
        self.creacion_maquina.clicked.connect(lambda: DialogoCrearAreaMaquina(self.obtener_lineas_db()).exec_()) # Abre un diálogo para crear una nueva máquina
        
        self.creacion_maquina.setFixedWidth(ancho)
        self.consultar_maquina = QPushButton("Eliminar Área/Máquina")
        self.consultar_maquina.setFixedWidth(ancho)
        self.consultar_maquina.clicked.connect(lambda: EliminarAreaMaquina(self.obtener_lineas_db(), self.obtener_areas_db()).exec_())
        
        
        # Botones de motores
        self.creacion_motor = QPushButton("Crear nuevo motor")
        self.creacion_motor.setFixedWidth(ancho)
        self.creacion_motor.clicked.connect(lambda: DialogoCrearMotor(self.obtener_lineas_db(), self.obtener_areas_db()).exec_())
        self.consultar_motor = QPushButton("Eliminar motor")
        self.consultar_motor.setFixedWidth(ancho)
        self.consultar_motor.clicked.connect(lambda: EliminarMotor(self.obtener_lineas_db(), self.obtener_areas_db()).exec_())

        # Layout vertical para líneas
        layout_lineas = QVBoxLayout()
        layout_lineas.addWidget(self.creacion_label, alignment=Qt.AlignHCenter)
        layout_lineas.addWidget(self.modificar_label, alignment=Qt.AlignHCenter)
        layout_lineas.addWidget(self.eliminar_label, alignment=Qt.AlignHCenter)

        
        # Layout vertical para máquinas
        layout_maquinas = QVBoxLayout()
        layout_maquinas.addWidget(self.creacion_maquina, alignment=Qt.AlignHCenter)
        layout_maquinas.addWidget(self.consultar_maquina, alignment=Qt.AlignHCenter)
        
        # Layout vertical para motores
        layout_motores = QVBoxLayout()
        layout_motores.addWidget(self.creacion_motor, alignment=Qt.AlignHCenter)
        layout_motores.addWidget(self.consultar_motor, alignment=Qt.AlignHCenter)

        # Layout horizontal para ambos bloques
        layout_gestion = QHBoxLayout()
        layout_gestion.addLayout(layout_lineas)
        layout_gestion.addLayout(layout_maquinas)
        layout_gestion.addLayout(layout_motores)

        # GroupBox de gestión
        grupo_gestion = QGroupBox()
        grupo_gestion.setLayout(layout_gestion)
        self.layout_grid.addWidget(grupo_gestion, 3, 0, 1, self.max_columnas)


        # Fila 4 en adelante: GroupBox para los botones de líneas
        self.layout_grid.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 4, 0, 1, self.max_columnas) # Espacio vertical
      
      
        # Crear el campo de texto
        self.campo_texto = QLineEdit()
        self.campo_texto.setPlaceholderText("Búsqueda rápida")  # Texto de ayuda opcional
        self.campo_texto.setFixedWidth(200)
        
        self.campo_texto.setStyleSheet("""
            QLineEdit {
                background-color: #fff;
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #1976d2;  /* Cambia el color del borde al hacer foco */
            }
        """)
        #Boton para iniciar la búsqueda
        self.boton_buscar = QPushButton("Buscar")
        self.boton_buscar.clicked.connect(self.leer_texto)  # Conectar el botón a un método
        self.boton_buscar.setMaximumWidth(150)
        
        
        #Layout horizontal para el campo de texto y el botón
        layout_busqueda = QHBoxLayout()
        layout_busqueda.addWidget(self.campo_texto)
        layout_busqueda.addWidget(self.boton_buscar)
        # Añadir el layout de búsqueda al grid
        self.layout_grid.addLayout(layout_busqueda, 5, 0, 1, 1)
        

        self.layout_grid.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 6, 0, 1, self.max_columnas) # Espacio vertical
        titulo_label_linea = QLabel("Consulta de  líneas")
        titulo_label_linea.setAlignment(Qt.AlignCenter)
        titulo_label_linea.setStyleSheet("""
            background-color: #229954;
            color: #fff;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 2px 0;
            margin-bottom: 5px;
            letter-spacing: 2px;
        """)
        self.layout_grid.addWidget(titulo_label_linea, 7, 0, 1, self.max_columnas)
        
        
        # GroupBox para las líneas
        self.grupo_lineas = QGroupBox("Selección de líneas")
        self.layout_lineas = QGridLayout()
        self.grupo_lineas.setLayout(self.layout_lineas)
        
        # Widget contenedor para el scroll
        contenedor_scroll = QWidget()
        contenedor_scroll.setLayout(QVBoxLayout())
        contenedor_scroll.layout().addWidget(self.grupo_lineas)
        
        
        # ScrollArea para las lineas
        scroll_linea = QScrollArea()
        scroll_linea.setWidgetResizable(True)
        scroll_linea.setWidget(contenedor_scroll)
        
        
        self.layout_grid.addWidget(scroll_linea, 8, 0, 1, self.max_columnas) # Añade el groupbox de líneas en la fila 8, ocupando todas las columnas

        self.posicion_actual = [0, 0]  # Para el grid de botones dentro del groupbox
        self.lineas = self.obtener_lineas_db()
        for linea in self.lineas:
            self.crear_boton_linea(linea)
        self.ventanas_abiertas = []
        
        

    def obtener_lineas_db(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT nombre FROM lineas")
            lineas = [fila[0] for fila in cursor.fetchall()]
            conn.close()
            return lineas
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron obtener las líneas: {e}")
            return [] 
        
    def obtener_areas_db(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT nombre FROM areas")
            areas = [fila[0] for fila in cursor.fetchall()]
            conn.close()
            return areas
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron obtener las áreas: {e}")
            return []


    def crear_boton_linea(self, nombre_linea):
        boton = QPushButton(f"{nombre_linea}")
        boton.clicked.connect(lambda _, nombre=nombre_linea: self.abrir_ventana(nombre)) # Conecta el botón a la función que abre la ventana
        boton.setMaximumWidth(300)

        fila, col = self.posicion_actual
        self.layout_lineas.addWidget(boton, fila, col)

        # Actualizar posición
        if col + 1 >= self.max_columnas:
            self.posicion_actual = [fila + 1, 0]
        else:
            self.posicion_actual[1] += 1
               

    def abrir_ventana(self, nombre_linea):
        dialog = SeleccionAreaDialog(nombre_linea)
        if dialog.exec_() == QDialog.Accepted:
            area = dialog.get_area_seleccionada()
            if area:
                self.ventana_motores = VentanaLinea(nombre_linea, area)
                self.ventana_motores.show()             
                

    def Nueva_linea(self):
        nombre, ok = QInputDialog.getText(self, "Nueva Línea", "Ingrese el nombre de la nueva línea:")
        if ok and nombre:
            if nombre in self.obtener_lineas_db():
                QMessageBox.critical(self, "Error", "La línea ya esta registrada.")
                return
            respuesta = QMessageBox.question(self, "Confirmar", "¿Está seguro?", QMessageBox.Yes | QMessageBox.No)
            if respuesta == QMessageBox.Yes:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()


                    cursor.execute("INSERT INTO lineas (nombre) VALUES (?)", (nombre,)) #Inserta el nombre de la línea en la base de datos
                    conn.commit() # Confirma los cambios
                    conn.close() # Cierra la conexión a la base de datos
                    self.crear_boton_linea(nombre)
                    self.recargar_botones_lineas() #Recarga los botones de líneas
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo registrar la línea: {e}")

    def Eliminar_linea(self):
        nombre, ok = QInputDialog.getText(self, "Eliminar Línea", "Ingrese el nombre de la línea a eliminar:")
        if ok and nombre:
            if nombre not in self.obtener_lineas_db():
                QMessageBox.critical(self, "Error", "La línea no existe.")
                return
            respuesta = QMessageBox.question(self, "Confirmar", "¿Está seguro?", QMessageBox.Yes | QMessageBox.No)
            if respuesta == QMessageBox.Yes:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                    SELECT codigo_motor
                    FROM motores
                    WHERE id_area IN (
                        SELECT id_area
                        FROM areas
                        WHERE id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
                    )
                    """, (nombre,))
                    motores = cursor.fetchall()


                    for (codigo_motor,) in motores:

                        cursor.execute("""
                        SELECT id_termografia
                        FROM eventos
                        WHERE id_motor = (SELECT id_motor FROM motores WHERE codigo_motor = ?)
                        AND tipo_evento = "Inspección Termográfica"
                        """, (codigo_motor,))
                    
                        eventos = cursor.fetchall()

                        for (id_termo,) in eventos:
                            # Paso 1: Obtener rutas de imágenes asociadas al id_termo
                            if id_termo:
                                cursor.execute("SELECT coj_delantero, coj_trasero, Estator FROM Termografia WHERE id_termo = ?", 
                                            (id_termo,))
                                rutas = cursor.fetchone() # Obtiene las rutas de las imágenes, fetchall() devuelve una tupla y fetchone() un solo registro
                                
                                if rutas:
                                    # Paso 2: Borrar Archivos del Sistema Operativo
                                    for ruta_imagen in rutas:
                                        if ruta_imagen and os.path.exists(ruta_imagen):
                                            try:
                                                # os.remove() borra un archivo. Si fueran carpetas, usaría shutil.rmtree()
                                                os.remove(ruta_imagen)
                                            # print(f"Archivo eliminado: {ruta_imagen}")
                                            except OSError as e:
                                                print(f"Error al eliminar archivo {ruta_imagen}: {e}")

        
                        cursor.execute("""
                            SELECT imagen_motor
                            FROM motores
                            WHERE codigo_motor = ?
                            """, (codigo_motor,))
                        resultado = cursor.fetchone()

                        # 1. Definir la carpeta donde se encuentran las imágenes
                        if getattr(sys, 'frozen', False):
                            base = os.path.dirname(sys.executable)
                        else:
                            base = os.path.dirname(os.path.abspath(__file__))

                        CARPETA_IMAGENES = os.path.join(base, "Fotos")

                    

                        if resultado:
                            nombre_archivo_motor = resultado[0] 
                            
                            if nombre_archivo_motor: # Se asegura de que el campo no sea nulo o vacío
                                
                                # CONSTRUIR LA RUTA COMPLETA 
                                ruta_completa_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo_motor)

                                # Usar la ruta completa para verificar y eliminar
                                if os.path.exists(ruta_completa_imagen):
                                    try:
                                        # USAR RUTA COMPLETA PARA ELIMINAR
                                        os.remove(ruta_completa_imagen)
                                        
                                    # print(f"Imagen del motor eliminada: {ruta_completa_imagen}")

                                    except OSError as e:
                                        # Esto sucede si el archivo existe pero no se tienen permisos para borrarlo
                                        print(f"Error al eliminar la imagen del motor {ruta_completa_imagen}: {e}")
                                
                                else:
                                    print(f"Advertencia: El archivo '{nombre_archivo_motor}' no se encontró en la carpeta '{CARPETA_IMAGENES}'. ")

                    cursor.execute("DELETE FROM lineas WHERE nombre = ?", (nombre,))
                    conn.commit()
                    conn.close()
                    self.recargar_botones_lineas()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar la línea: {e}")
                    
    def Modificar_linea(self):
        nombre, ok = QInputDialog.getText(self, "Modificar Línea", "Ingrese el nombre de la línea a modificar:")
        if ok and nombre:
            if nombre not in self.obtener_lineas_db():
                QMessageBox.critical(self, "Error", "La línea no existe.")
                return
            nuevo_nombre, ok_nuevo = QInputDialog.getText(self, "Nuevo Nombre", "Ingrese el nuevo nombre para la línea:")
            if nuevo_nombre in self.obtener_lineas_db():
                QMessageBox.warning(self, "Duplicado", "Ya existe una línea con ese nombre.")
                return

            if ok_nuevo and nuevo_nombre:
                respuesta = QMessageBox.question(self, "Confirmar", "¿Está seguro?", QMessageBox.Yes | QMessageBox.No)
                if respuesta == QMessageBox.Yes:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        cursor.execute("UPDATE lineas SET nombre = ? WHERE nombre = ?", (nuevo_nombre, nombre))
                        conn.commit()
                        conn.close()
                        self.recargar_botones_lineas()
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"No se pudo modificar la línea: {e}")


    def recargar_botones_lineas(self):
        for i in reversed(range(self.layout_lineas.count())):
            item = self.layout_lineas.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QPushButton):
                self.layout_lineas.removeWidget(widget)
                widget.deleteLater()
        self.posicion_actual = [0, 0]
        self.lineas = self.obtener_lineas_db()
        for linea in self.lineas:
            self.crear_boton_linea(linea)
    
    def leer_texto(self):
        global OFFSET
        texto = self.campo_texto.text().strip() # Elimina espacios al inicio y al final y obtiene el texto ingresado
        if not texto:
            QMessageBox.warning(self, "Advertencia", "No hay texto ingresado.")
            return

        try:

            # Inicializar el contador de desfase si es la primera vez que se llama a la función
            if not hasattr(self, 'offset_count'):  #hasattr verifica si el objeto tiene un atributo con el nombre dado
                self.offset_count = 0 #contador de desfase

            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Ejecución de la consulta 
            cursor.execute("""
                SELECT m.*, a.nombre AS nombre_area, l.nombre AS nombre_linea
                FROM motores m
                JOIN areas a ON m.id_area = a.id_area
                JOIN lineas l ON a.id_linea = l.id_linea
                WHERE m.codigo_motor = ?
            """, (texto,))
            
            # 2.  Usa fetchall() para obtener TODOS los motores
            motores = cursor.fetchall() 
            conn.close()

            # 3. Verifica si se encontró AL MENOS UN motor
            if not motores:
                QMessageBox.information(self, "No encontrado", f"No se encontró un motor con código '{texto}'.")
                return
            
              # Inicializar o crear la lista para guardar las referencias de los diálogos.
             # Esto es vital para que no se cierren al instante.
            if not hasattr(self, 'dialogos_motores_busqueda'):
                self.dialogos_motores_busqueda = []

            # Obtener los nombres de las columnas
            columnas = [desc[0] for desc in cursor.description]
           

            # Traducir nombres para presentación
            nombres_amigables = {
                "nombre_linea": "Línea",
                "nombre_area": "Área/Máquina",
                "codigo_motor": "Código de motor",
                "codigo_equipo": "Código de equipo",
                "datos_motor": "Datos de motor",
                "funcion": "Función",
                "marca": "Marca",
                "tipo_motor": "Tipo de motor",
                "hp_kw": "Potencia (HP,KW)",
                "voltaje": "Voltaje (V)",
                "voltaje_fuente": "Voltaje fuente/campo (V)",
                "amperaje_fabricante": "Amperaje fabricante (A)",
                "rpm": "Revoluciones por minuto (rpm)",
                "frecuencia": "Frecuencia (Hz)",
                "corriente_trabajo": "Corriente de trabajo (A)",
                "temperatura_trabajo": "Temperatura de trabajo",
                "ultimo_mantenimiento": "Antigüedad",
                "proximo_mantenimiento": "Ubicación o posición de montaje",
                "otro": "Otro",
                "observaciones": "Observaciones",
                "cojinete_frontal": "Cojinete frontal y Código de repuesto",
                "cojinete_trasero": "Cojinete trasero y Código de repuesto",
                "ciclo_mantenimiento": "Ciclo mantenimiento",
                "Nombre_persona": "Nombre persona que registró el motor"
            }

            excluir = {"id_motor", "id_area"} 

            # 4. ITERAR sobre la lista de motores y mostrar un diálogo por cada uno
            for motor in motores:
                # Crea el diccionario de datos para el motor actual
                datos = dict(zip(columnas, motor)) 

                # Prepara los datos para la presentación
                datos_presentacion = {
                    nombres_amigables.get(k, k): v for k, v in datos.items() if k not in excluir
                }

                # Crea y muestra el diálogo para ESTE motor
                dialogo = DetalleMotorDialog(datos_presentacion)

                # Obtener la posición actual (generalmente la esquina superior izquierda del diálogo)
                posicion_base = dialogo.pos()

                # Calcular el nuevo desfase
                dx = self.offset_count * OFFSET
                dy = self.offset_count * OFFSET
                
                # Aplicar el desfase
                nueva_posicion = posicion_base.x() + dx, posicion_base.y() + dy
                dialogo.move(*nueva_posicion) 
                
                # Incrementar el contador para el siguiente diálogo
                self.offset_count += 1


                dialogo.show()

                self.dialogos_motores_busqueda.append(dialogo)  # Guarda la referencia del diálogo

        
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo consultar el motor:\n{e}") 


#****************************************** Clase para mostrar el PDF de instrucciones**************************************************
class PDFViewer(QDialog):
    def __init__(self, pdf_path):
        super().__init__()
        self.setWindowTitle("Instrucciones del Sistema")
        self.setFixedSize(1400, 900)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QLabel#titulo { color: #1e8449; font-size: 32px; font-weight: bold; }
            QLabel#descripcion { color: #229954; font-size: 16px; font-weight: normal; }
            QPushButton { background-color: #1976d2; color: white; border-radius: 12px; padding: 12px 24px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #1565c0; }
            
            #CaratulaDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 10px;
            }

        """)

        frame_contenedor = QFrame()
        frame_contenedor.setObjectName("CaratulaDialog")

        self.pdf_path = resource_path(pdf_path)
        self.doc = fitz.open(self.pdf_path)


        layout = QVBoxLayout()

        # --- Barra de búsqueda ---
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar en el PDF...")
        btn_search = QPushButton("Buscar")
        btn_search.clicked.connect(self.buscar_texto)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(btn_search)

        layout.addLayout(search_layout)

        # --- Scroll principal ---
        self.scroll = QScrollArea()
        layout.addWidget(self.scroll)

        # Contenido con las páginas
        self.contenido = QWidget()
        self.vbox = QVBoxLayout()
        self.contenido.setLayout(self.vbox)

        self.cargar_paginas()  # << primera carga sin búsqueda

        self.scroll.setWidget(self.contenido)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar)

        main_layout = QVBoxLayout()
        main_layout.addWidget(frame_contenedor)
        frame_contenedor.setLayout(layout)
        self.setLayout(main_layout)

    # ---------------------------------------------
    # Cargar páginas (sin resaltado)
    # ---------------------------------------------
    def cargar_paginas(self, resultados=None):
        # Limpia páginas anteriores
        for i in reversed(range(self.vbox.count())):
            widget = self.vbox.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for num, page in enumerate(self.doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            # Convertir a QImage
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            # Si hay resultados, resaltar coincidencias en esta página
            if resultados and num in resultados:
                painter = QPainter(img)
                painter.setPen(Qt.red)
                painter.setBrush(Qt.transparent)

                for rect in resultados[num]:
                    # Ajustar coordenadas al zoom (Matrix(2,2))
                    r = QRect(
                        int(rect.x0 * 2),
                        int(rect.y0 * 2),
                        int((rect.x1 - rect.x0) * 2),
                        int((rect.y1 - rect.y0) * 2)
                    )
                    painter.drawRect(r)

                painter.end()

            lbl = QLabel()
            lbl.setPixmap(QPixmap.fromImage(img))
            self.vbox.addWidget(lbl)

    # ---------------------------------------------
    # Buscar y resaltar texto
    # ---------------------------------------------
    def buscar_texto(self):
        texto = self.search_box.text().strip()
        if not texto:
            return
        
        resultados = {}

        for num, page in enumerate(self.doc):
            hallazgos = page.search_for(texto)
            if hallazgos:
                resultados[num] = hallazgos

        # Volver a cargar páginas con resaltado
        self.cargar_paginas(resultados)

        # Ir a la primera coincidencia
        if resultados:
            primera_pag = list(resultados.keys())[0]
            self.scroll.verticalScrollBar().setValue(primera_pag * 800)



#****************************************** Clase de diálogo de información del sistema**************************************************
class InfoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Información del Sistema")
        self.setFixedSize(500, 350)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))

        self.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QLabel#titulo { color: #1e8449; font-size: 32px; font-weight: bold; }
            QLabel#descripcion { color: #229954; font-size: 16px; font-weight: normal; }
            QPushButton { background-color: #1976d2; color: white; border-radius: 12px; padding: 12px 24px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #1565c0; }
            
            #CaratulaDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 10px;
            }

        """)

        frame_contenedor = QFrame()
        frame_contenedor.setObjectName("CaratulaDialog")

        layout = QVBoxLayout()

        # Texto informativo
        texto = QLabel(
            "Este sistema permite guardar los datos y mantenimientos de los motores.\n"
            "Puede registrar, editar y consultar información relevante para la gestión eficiente.\n\n"
            "Acrónimos:\n"
            "RPM: Revoluciones por minuto\n"
            "HP: Caballos de fuerza\n"
            "KW: Kilovatios\n"
            "°C: Grados Celsius\n"
            "°F: Grados Fahrenheit\n"
            "MPM: Metros por minuto\n"
        )
        texto.setWordWrap(True)
        layout.addWidget(texto)

        # Botón para abrir PDF
        btn_pdf = QPushButton("📄 Ver instrucciones del sistema")
        btn_pdf.setStyleSheet("padding: 8px; font-size: 14px;")
        btn_pdf.clicked.connect(self.abrir_pdf)
        layout.addWidget(btn_pdf)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar)

        main_layout = QVBoxLayout()
        main_layout.addWidget(frame_contenedor)
        frame_contenedor.setLayout(layout)
        self.setLayout(main_layout)

    def abrir_pdf(self):
        ruta_pdf = os.path.join("Recursos", "Instrucciones.pdf")

        visor = PDFViewer(ruta_pdf)
        visor.exec_()


    
#****************************************** Clase que aparece al inicio**************************************************   
class CaratulaDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bienvenido")
        self.setFixedSize(800, 500)
        
                
        frame_contenedor = QFrame()
        frame_contenedor.setObjectName("CaratulaDialog")
        
        
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        self.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QLabel#titulo { color: #1e8449; font-size: 32px; font-weight: bold; }
            QLabel#descripcion { color: #229954; font-size: 16px; font-weight: normal; }
            QPushButton { background-color: #1976d2; color: white; border-radius: 12px; padding: 12px 24px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #1565c0; }
            
            #CaratulaDialog {
                background-color: #f4f6fb;
                border: 6px solid #229954;
                border-radius: 10px;
            }
         

        """)

        # Fila 0: Imagen       
        layout = QGridLayout() 
        label = QLabel("Sistema de Gestión de Motores\nPAINSA K10")
        label.setObjectName("titulo")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label,0, 0, 1, 4)  # Añade el título en la fila 0, ocupando todas las columnas
        
        
        #Fila 1, 2, 3:Imagen
        layout.addItem(QSpacerItem(10, 30, QSizePolicy.Minimum, QSizePolicy.Fixed), 1, 0, 1, 4) # Espacio vertical entre la imagen y el título
        imagen_label = QLabel() #QLAbel para la imagen
        # Crea la ruta completa al archivo de imagen
        logo_path = resource_path(os.path.join( "Recursos", "Logo.png"))
        # Verifica si el archivo existe
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            imagen_label.setPixmap(pixmap)
        else:
            imagen_label.setText("Logo no encontrado.")
        imagen_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(imagen_label, 2, 0, 1, 4) # Añade la imagen en la fila 2, ocupando todas las columnas
        layout.addItem(QSpacerItem(10, 30, QSizePolicy.Minimum, QSizePolicy.Fixed), 3, 0, 1, 4)

        btn = QPushButton("Inicio")
        btn.clicked.connect(self.accept)
    
        
        # Botón de info (icono)
        btn_info = QPushButton()
        btn_info.setIcon(QIcon(resource_path(os.path.join("Recursos", "info.png"))))
        btn_info.setIconSize(QSize(40, 40))
        btn_info.setFixedSize(50, 50)
        btn_info.setStyleSheet("background: transparent; border: none;")
        btn_info.setToolTip("Información")

        # Botón de créditos (icono)
        btn_creditos = QPushButton()
        btn_creditos.setIcon(QIcon(resource_path(os.path.join("Recursos", "creditos.png"))))
        btn_creditos.setIconSize(QSize(40, 40))
        btn_creditos.setFixedSize(50, 50)
        btn_creditos.setStyleSheet("background: transparent; border: none;")
        btn_creditos.setToolTip("Créditos")
        
        # Layout horizontal para la fila de botones
        fila_botones = QHBoxLayout()
        fila_botones.addWidget(btn_info)
        fila_botones.addStretch() # Añade espacio flexible entre los botones
        fila_botones.addWidget(btn)
        fila_botones.addStretch()
        fila_botones.addWidget(btn_creditos)
        
        layout.addLayout(fila_botones, 4, 0, 1, 4)
        
        
         # Conexiones para mostrar información y créditos
        def mostrar_info():
            dlg = InfoDialog()
            dlg.exec_()

        def mostrar_creditos():
            msg = QMessageBox(self)
            msg.setWindowTitle("Créditos")
            msg.setText(
                "Desarrollado por: Ingeniero Samuel Tórtola\n"
                "Teléfono: +502 4755 7524\n"
                "Versión: 6.0\n"
                "Año: 2025"
            )
            msg.setIcon(QMessageBox.Information)

            # Aplicar estilo directamente al QMessageBox
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #f4f6fb;
                    border: 3px solid #229954;
                    border-radius: 14px;
                }
                QLabel {
                    color: #1e8449;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    border-radius: 8px;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
                              
                QMessageBox QLabel {
                color: black;  
            }
            """)

            msg.exec_()

        btn_info.clicked.connect(mostrar_info)
        btn_creditos.clicked.connect(mostrar_creditos)

        
        main_layout = QVBoxLayout()
        main_layout.addWidget(frame_contenedor)
        frame_contenedor.setLayout(layout)
        self.setLayout(main_layout)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    inicializar_base_datos()
    caratula = CaratulaDialog()
    if caratula.exec_() == QDialog.Accepted:
        ventana = VentanaPrincipal()
        ventana.showMaximized()  # <-- Esto la muestra maximizada
        ventana.show()
        sys.exit(app.exec_())

















