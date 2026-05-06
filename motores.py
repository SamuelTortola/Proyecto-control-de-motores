import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QApplication, QTextEdit,QCheckBox,QScrollArea,QLineEdit,QFileDialog,QFrame,QDateEdit,QListWidgetItem,QHeaderView,QComboBox, QWidget, QPushButton, QLabel, QInputDialog, QGridLayout, QGroupBox, QVBoxLayout, QSpacerItem, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QVBoxLayout, QListWidget
from PyQt5.QtGui import QPixmap, QDoubleValidator, QIntValidator, QIcon
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QMessageBox
import sqlite3
import shutil
from PIL import Image

from database_utils import get_db_connection, resource_path
from informes import generar_informe_pdf

from datetime import datetime

global filtrado
filtrado = 0
imagenes_cargadas = 0

global fecha_1
global fecha_2
fecha_1 = ""
fecha_2 = ""

# Diccionario temporal para almacenar las imágenes seleccionadas
imagenes_temporales = {}


#********************Clase que permite crear una ventana para gestionar los motores de una línea específica*********************************

class VentanaLinea(QWidget):
    def __init__(self, nombre_linea, area):
        super().__init__()
        self.nombre_linea = nombre_linea
        self.area = area
        self.setWindowTitle(f"Motores - Línea {nombre_linea}")
        self.setGeometry(100, 50, 900, 800)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
         # Frame contenedor para aplicar estilo
        self.frame_contenedor = QFrame()
        self.frame_contenedor.setObjectName("contenedorLinea")

        # Layout interno (dentro del frame)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        self.frame_contenedor.setLayout(layout)

        # Aplica el layout principal a la ventana
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.frame_contenedor)
        self.setLayout(main_layout)

        # Estilo
        self.setStyleSheet("""
            QWidget { background-color: #f4f6fb; font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px; }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 12px;
                padding: 12px 24px;
                margin: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
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
                padding: 0 3px;
                color: #229954;
                font-size: 20px;
                font-weight: bold;
            }
            QDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            #contenedorLinea {
                border: 3px solid #229954;
                border-radius: 14px;
                background-color: #f4f6fb;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #eafaf1;
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
        
        # Agrega el label de selección de motores
        self.titulo_label1 = QLabel("Selección de motores")
        self.titulo_label1.setAlignment(Qt.AlignCenter)
        self.titulo_label1.setStyleSheet("""
            background-color: #229954;
            color: #fff;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            padding: 6px 0;
            margin-bottom: 10px;
            letter-spacing: 2px;
        """)
        layout.addWidget(self.titulo_label1, 1, 0, 1, 4)  # Ocupa toda la fila superior
        self.titulo_label1.setMaximumWidth(500)
        self.titulo_label1.setMaximumHeight(60)
        
        layout.addItem(QSpacerItem(200, 50, QSizePolicy.Minimum, QSizePolicy.Fixed), 0, 0, 1, 4) # Añade un espacio en la parte superior para separar el título del resto del contenido
        
        #colocar un espacio vertical entre el título y los botones
        layout.addItem(QSpacerItem(200, 50, QSizePolicy.Minimum, QSizePolicy.Fixed), 2, 0, 1, 4) #1,0,1,4 significa que ocupa la fila 1, columna 0, 1 fila de alto y 4 columnas de ancho
       
       
        # GroupBox para los motores
        self.grupo_motores = QGroupBox("Motores disponibles")
        self.layout_motores = QGridLayout()
        self.grupo_motores.setLayout(self.layout_motores)
        
        # Widget contenedor para el scroll
        contenedor_scroll = QWidget()
        contenedor_scroll.setLayout(QVBoxLayout())
        contenedor_scroll.layout().addWidget(self.grupo_motores)
        
        # ScrollArea para los motores
        scroll_motores = QScrollArea()
        scroll_motores.setWidgetResizable(True)
        scroll_motores.setWidget(contenedor_scroll)
        
        # Agregar el scroll al layout principal
        layout.addWidget(scroll_motores, 3, 0, 1, 4)

        
        self.nombre_linea = nombre_linea
        self.area = area
        self.layout_grid = layout
        self.max_columnas = 4
     
        self.posicion_actual = [0, 0]  # Para el grid de motores
        self.cargar_motores()

    def cargar_motores(self):  # Método para cargar los motores de la base de datos
        # Conectar a la base de datos y obtener los motores
        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute("""
            SELECT codigo_motor, funcion FROM motores
            WHERE id_area = (
                SELECT id_area FROM areas WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
            )
        """, (self.area, self.nombre_linea))
        motores = cursor.fetchall() # Esto obtiene todos los motores de la base de datos para el área y línea especificadas
        conn.close()

        for (nombre_motor,funcion) in motores:
            self.crear_boton_motor(nombre_motor, funcion)
    
    
    def recargar_motores(self):
        # Limpia los botones actuales
        for i in reversed(range(self.layout_motores.count())):
            widget = self.layout_motores.itemAt(i).widget()
            if widget:
                self.layout_motores.removeWidget(widget)
                widget.deleteLater()
        self.posicion_actual = [0, 0]
        self.cargar_motores()

    def crear_boton_motor(self, nombre_motor, funcion):
        texto_boton = f"{nombre_motor} - {funcion}" if funcion else str(nombre_motor)
        boton = QPushButton(texto_boton) 
        boton.setMaximumWidth(600)
        boton.clicked.connect(lambda _, nombre=nombre_motor: self.mostrar_detalles_motor(nombre))

        fila, col = self.posicion_actual # Obtiene la fila y columna actuales
        self.layout_motores.addWidget(boton, fila, col) #añade el botón a la cuadrícula en la posición actual

        if col + 1 >= 1:
            self.posicion_actual = [fila + 1, 0]
        else:
            self.posicion_actual[1] += 1


    def mostrar_detalles_motor(self, nombre_motor):
        dialog = None
        conn = get_db_connection()
        cursor = conn.cursor()


        # Obtener nombres de columnas dinámicamente
        cursor.execute("PRAGMA table_info(motores)") #PRAGMA table_info(motores) obtiene información sobre las columnas de la tabla motores
        columnas = [info[1] for info in cursor.fetchall()] #  obtiene los nombres de las columnas de la tabla motores
        
        

        if "id_motor" not in columnas:
            QMessageBox.warning(self, "Error", "La tabla 'motores' no contiene la columna 'id_motor'.")
            conn.close()
            return
        else:
            # Buscar el motor en la base de datos
            columnas_sql = ", ".join(columnas) #crea una cadena con los nombres de las columnas separadas por comas

            cursor.execute(f"""
                    SELECT {columnas_sql} FROM motores
                    WHERE codigo_motor = ? AND id_area = (
                        SELECT id_area FROM areas WHERE nombre = ? AND id_linea = (
                            SELECT id_linea FROM lineas WHERE nombre = ?
                        )
                    )
                """, (nombre_motor, self.area, self.nombre_linea))

            fila = cursor.fetchone()
            if not fila:
                QMessageBox.warning(self, "Motor no encontrado", "No se encontraron datos para este motor.")
                conn.close()
                return
            datos = list(fila)
            dialog = DetalleMotorDialog(datos, columnas, self)
        conn.close()
        if dialog is not None:
            dialog.exec_()
            self.recargar_motores()


#********************Clase que permite seleccionar un área o máquina específica para editar o eliminar*********************************

class SeleccionAreaDialog(QDialog):
    def __init__(self, nombre_linea, parent=None):  #Se pasa el nombre de la línea como parámetro
        super().__init__(parent)
        self.setObjectName("customDialogStyled")
        self.setWindowTitle("Seleccionar Área/Máquina")
        self.setFixedSize(800, 800)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        self.nombre_linea = nombre_linea

        frame_contenedor = QFrame()
        frame_contenedor.setObjectName("SeleccionAreaDialog")

        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6fb;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 18px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 12px;
                padding: 12px 24px;
                margin: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
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
                padding: 0 3px;
                color: #229954;
                font-size: 20px;
                font-weight: bold;
            }

            QDialog#dialogConBorde {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }

            #SeleccionAreaDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 10px;
            }
            
            QInputDialog {
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
            
             QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #eafaf1;
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

        
        # Layout principal

        layout_principal = QVBoxLayout(frame_contenedor)
        
        # Título central
        titulo_label = QLabel("Selección de Área/Máquina")
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setStyleSheet("""
            background-color: #229954;
            color: #fff;
            font-size: 20px;
            font-weight: bold;
            border-radius: 10px;
            padding: 12px;
        """)
        titulo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        titulo_label.setMaximumHeight(45)
        layout_principal.addWidget(titulo_label)

        # QGroupBox contenedor
        grupo = QGroupBox("Gestión de áreas/máquinas")
        layout_grupo = QVBoxLayout()
        grupo.setLayout(layout_grupo)
        
       
        # Botones de gestión
        botones_layout = QHBoxLayout()
        self.btn_agregar = QPushButton("Editar área/máquina")
        self.btn_agregar.setFixedHeight(60)
        botones_layout.addWidget(self.btn_agregar)
        layout_principal.addLayout(botones_layout)

        # Conexiones
        self.btn_agregar.clicked.connect(self.editar_area)  #Editar área/máquina

        # Layout de botones de áreas/máquinas
        self.grid_areas = QGridLayout()
        self.grid_areas.setAlignment(Qt.AlignTop)
        layout_grupo.addLayout(self.grid_areas)
        

        # Parámetros de disposición
        self.max_columnas = 2
        self.fila = 0
        self.col = 0
        
        
        # Widget contenedor para el scroll
        contenedor_scroll = QWidget()
        contenedor_scroll.setLayout(QVBoxLayout())
        contenedor_scroll.layout().addWidget(grupo)
        
        
         #ScrollArea para las lineas
        scroll_linea = QScrollArea()
        scroll_linea.setWidgetResizable(True)
        scroll_linea.setWidget(contenedor_scroll)
        
        
        layout_principal.addWidget(scroll_linea)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(frame_contenedor)
        self.setLayout(main_layout)
        self.cargar_areas()

    def cargar_areas(self):
        self.fila = 0
        self.col = 0

        # Eliminar botones antiguos
        while self.grid_areas.count():
            item = self.grid_areas.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Cargar desde SQLite
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre FROM areas
            WHERE id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
        """, (self.nombre_linea,))
        areas = cursor.fetchall()
        conn.close()

        for (nombre_area,) in areas:
            btn = QPushButton(nombre_area)
            btn.setFixedHeight(60)
            btn.clicked.connect(lambda _, area=nombre_area: self.seleccionar_area(area))
            self.grid_areas.addWidget(btn, self.fila, self.col)
            self.col += 1
            if self.col >= self.max_columnas:
                self.col = 0
                self.fila += 1


    def editar_area(self):
        # Seleccionar el área a editar
        nombre_area, ok = QInputDialog.getText(self, "Editar Área/máquina", "Nombre del área/máquina a editar:")
        if not (ok and nombre_area):
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_area, nombre, id_linea FROM areas
            WHERE nombre = ? AND id_linea = (SELECT id_linea FROM lineas WHERE nombre = ?)
        """, (nombre_area.strip(), self.nombre_linea))
        area_existente = cursor.fetchone()

        if not area_existente:
            QMessageBox.warning(self, "Error", "El área/máquina no existe.")
            conn.close()
            return

        id_area, nombre_actual, id_linea_actual = area_existente

        # Obtener todas las líneas para el combo
        cursor.execute("SELECT nombre FROM lineas")
        lineas = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Crear diálogo personalizado
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Área/Máquina")
        layout = QVBoxLayout(dialog)
        dialog.setObjectName("dialogConBorde")  # Este SÍ debe tener borde


        label_nombre = QLabel("Nuevo nombre del área/máquina:")
        edit_nombre = QLineEdit(nombre_actual)
        layout.addWidget(label_nombre)
        layout.addWidget(edit_nombre)

        label_linea = QLabel("Nueva línea:")
        combo_lineas = QComboBox()
        combo_lineas.addItems(lineas)
        # Selecciona la línea actual
        idx_actual = lineas.index(self.nombre_linea) if self.nombre_linea in lineas else 0
        combo_lineas.setCurrentIndex(idx_actual)
        layout.addWidget(label_linea)
        layout.addWidget(combo_lineas)

        btn_guardar = QPushButton("Guardar cambios")
        layout.addWidget(btn_guardar)

        def guardar():
            nuevo_nombre = edit_nombre.text().strip()
            nueva_linea = combo_lineas.currentText()
            if not nuevo_nombre or not nueva_linea:
                QMessageBox.warning(dialog, "Advertencia", "Debe ingresar un nombre y seleccionar una línea.")
                return
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nueva_linea,))
            id_linea_nueva = cursor2.fetchone()
            if not id_linea_nueva:
                QMessageBox.critical(dialog, "Error", "No se encontró la línea seleccionada.")
                conn2.close()
                return
            try:
                cursor2.execute("""
                    UPDATE areas
                    SET nombre = ?, id_linea = ?
                    WHERE id_area = ?
                """, (nuevo_nombre, id_linea_nueva[0], id_area))
                conn2.commit()
                QMessageBox.information(dialog, "Éxito", "Área/máquina actualizada correctamente.")
                dialog.accept()
                self.cargar_areas()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"No se pudo actualizar el área/máquina:\n{e}")
            finally:
                conn2.close()

        btn_guardar.clicked.connect(guardar)
        dialog.exec_()

    def seleccionar_area(self, area): # Método para seleccionar un área
        self.area_seleccionada = area # asigna el área seleccionada a un atributo de la clase
        self.accept() # Cierra el diálogo y devuelve el área seleccionada

    def get_area_seleccionada(self):  # Método para obtener el área seleccionada, fuera de la clase
        return getattr(self, "area_seleccionada", None)
    

#********************Clase que permite mostrar los detalles de un motor específico y editar sus datos*********************************
    
class DetalleMotorDialog(QDialog):
    def __init__(self, datos_motor, columnas, parent=None, nuevo=False): # Constructor que recibe los datos del motor y las columnas
        super().__init__(parent)
        self.nuevo = nuevo
        self.setWindowTitle("Detalles del Motor")
        self.setWindowState(Qt.WindowMaximized)
        self.nombre_imagen = None


         # Frame contenedor para aplicar estilo
        self.frame_contenedor2 = QFrame()
        self.frame_contenedor2.setObjectName("contenedorLinea2")

        # Layout interno (dentro del frame)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        self.frame_contenedor2.setLayout(layout)

        # Aplica el layout principal a la ventana
       # Layout general de la ventana
        layout_general = QVBoxLayout()
       # layout_general.setContentsMargins(0, 0, 0, 0)
        layout_general.addWidget(self.frame_contenedor2)
       
        self.setLayout(layout_general)


      

        self.setStyleSheet("""
            QDialog { 
                background-color: #f4f6fb;
                border: 3px solid #229954;
                border-radius: 14px;
            }
                           
            QWidget { background-color: #f4f6fb; font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px; }
            #marcoVerde {
                border: 3px solid #229954;
                border-radius: 14px;
                background-color:  #d4efdf;
                padding: 24px;
                           
            }
           
           
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 12px;
                padding: 12px 24px;
                margin: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
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
                padding: 0 3px;
                color: #229954;
                font-size: 20px;
                font-weight: bold;
            }
            
            QCalendarWidget QAbstractItemView {
                color: black; /* Texto de los días */
                selection-background-color: #1976d2;
                selection-color: white;
                background-color: white;
            }

            QCalendarWidget QToolButton {
                color: black; /* Mes y año */
                background-color: #cfcfcf;
                font-weight: bold;
            }

            QCalendarWidget QWidget {
                color: black; /* En general */
                background-color: white;
            }

            QCalendarWidget QSpinBox {
                color: black;
            }
            #contenedorLinea2 {
                border: 3px solid #229954;
                border-radius: 14px;
                background-color: #f4f6fb;
            }
        
            DetalleMotorDialog { 
                border: none; 
            }
        """)


        self.NOMBRES_AMIGABLES = {
            "codigo_motor": "Código de motor",
            "codigo_equipo": "Código de equipo",
            "datos_motor": "Modelo de motor",
            "funcion": "Función",
            "marca": "Marca",
            "tipo_motor": "Tipo de motor",
            "hp_kw": "Potencia (HP,KW)",
            "voltaje": "Voltaje Armadura (V)",
            "voltaje_fuente": "Voltaje fuente/campo (V)",
            "amperaje_fabricante": "Amperaje fabricante (A)",
            "rpm": "Revoluciones por minuto (rpm)",
            "frecuencia": "Frecuencia (Hz)",
            "corriente_trabajo": "Amperaje de excitación (A)",
            "temperatura_trabajo": "Temperatura de trabajo",
            "ultimo_mantenimiento": "Antigüedad",
            "proximo_mantenimiento": "Ubicación o posición de montaje",
            "cojinete_frontal": "Cojinete frontal y código de repuesto",
            "cojinete_trasero": "Cojinete trasero y código de repuesto",
            "ciclo_mantenimiento": "Ciclo mantenimiento",
            "observaciones": "Observaciones",
            "imagen_motor": "Imagen motor",
            "Nombre_persona": "Nombre persona que registró el motor",
            "Fecha_registro": " Fecha y hora de registro",
        }
        
        
        contenedor = QFrame()
        contenedor.setObjectName("marcoVerde")
        contenedor_layout = QVBoxLayout(contenedor)
        contenedor_layout.setContentsMargins(40, 40, 40, 40)

        self.reverso_nombres = {v: k for k, v in self.NOMBRES_AMIGABLES.items()} # Crea un diccionario inverso para buscar por nombre amigable

        
        ORDEN_DESEADO = [
            "codigo_motor", "codigo_equipo", "datos_motor", "funcion", "marca", "tipo_motor",
            "hp_kw", "voltaje", "voltaje_fuente", "amperaje_fabricante", "rpm", "frecuencia",
            "corriente_trabajo", "temperatura_trabajo", "ultimo_mantenimiento", "proximo_mantenimiento",
            "cojinete_frontal","imagen_motor", "ciclo_mantenimiento",  "cojinete_trasero","observaciones","Nombre_persona", "Fecha_registro"
        ]
        ocultas = {"id_motor", "id_area"}
        self.columnas_visibles = [c for c in ORDEN_DESEADO if c in columnas and c not in ocultas]



        # Imagen
        self.imagen_label = QLabel("Sin imagen")
        self.imagen_label.setAlignment(Qt.AlignCenter)
        self.imagen_label.setFixedSize(300, 300)
        self.imagen_label.setStyleSheet("border: 2px dashed #888; color: #888; background: #f4f6fb;")
        
        # 1. Crea el QGroupBox para la imagen
        self.grupo_imagen = QGroupBox("Imagen del motor")
        self.grupo_imagen.setMinimumHeight(370)
        self.grupo_imagen.setLayout(QVBoxLayout())
        self.grupo_imagen.layout().addWidget(self.imagen_label)

        if "imagen_motor" in columnas:
            idx = columnas.index("imagen_motor")
            nombre_img = datos_motor[idx]
            if nombre_img:
                if getattr(sys, 'frozen', False):
                    base = os.path.dirname(sys.executable)
                else:
                    base = os.path.dirname(os.path.abspath(__file__))

                ruta = os.path.join(base, "Fotos", nombre_img)

                if os.path.exists(ruta):
                    pixmap = QPixmap(ruta).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.imagen_label.setPixmap(pixmap)
                    self.imagen_label.setText("")  # Quita el texto
                    self.imagen_label.setStyleSheet("""
                       
                        border-radius: 10px;
                        background: #eafaf1;
                    """)
                else:
                    self.imagen_label.setPixmap(QPixmap())
                    self.imagen_label.setText("Sin imagen")
                    self.imagen_label.setStyleSheet("border: 2px dashed #888; color: #888; background: #f4f6fb;")

        # Tabla eventos y botón
        self.tabla_eventos = QTableWidget(5, 4)
        self.tabla_eventos.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción","Realizado por"])
        self.tabla_eventos.setMinimumHeight(200)  # Ajusta el ancho mínimo
        self.tabla_eventos.setColumnWidth(1, 250)
        self.tabla_eventos.setColumnWidth(2, 800)
        self.tabla_eventos.horizontalHeader().setStretchLastSection(True)


        # Layouts de campos
        col1_widget = QWidget()
        col2_widget = QWidget()
        col3_widget = QWidget()
        self.col1_layout = QVBoxLayout(col1_widget)
        self.col2_layout = QVBoxLayout(col2_widget)
        self.col3_layout = QVBoxLayout(col3_widget)


        for i, col in enumerate(self.columnas_visibles):
            nombre_amigable = self.NOMBRES_AMIGABLES.get(col, col)
            valor = datos_motor[columnas.index(col)]
            label = QLabel(nombre_amigable + ":")
            edit = QLineEdit(str(valor))
            edit.setObjectName(col)
            edit.setReadOnly(True)
            edit.setStyleSheet("background-color: #d7dbdd;")  # Fondo gris claro por defecto

            if i % 3 == 0: # Distribuye los campos en 3 columnas, i % 3 determina la columna
                self.col1_layout.addWidget(label)
                self.col1_layout.addWidget(edit)
            elif i % 3 == 1:
                self.col2_layout.addWidget(label)
                self.col2_layout.addWidget(edit)
            else:
                self.col3_layout.addWidget(label)
                self.col3_layout.addWidget(edit)


        campos_layout = QHBoxLayout()
        campos_layout.addWidget(col1_widget, stretch=1)
        campos_layout.addWidget(col2_widget, stretch=1)
        campos_layout.addWidget(col3_widget, stretch=1)
        
        self.grupo_datos = QGroupBox("Datos del motor")
        self.grupo_datos.setLayout(QVBoxLayout())
        self.grupo_datos.layout().addLayout(campos_layout)  
        
        self.grupo_eventos = QGroupBox("Eventos del motor")
        self.grupo_eventos.setLayout(QVBoxLayout())
        self.grupo_eventos.layout().addWidget(self.tabla_eventos)


        layout_derecha = QVBoxLayout()
        layout_derecha.addWidget(self.grupo_datos)
        layout_derecha.addWidget(self.grupo_eventos)

        layout_izquierda = QVBoxLayout()
        self.btn_imagen = QPushButton("Agregar imagen del motor")
        layout_izquierda.addWidget(self.grupo_imagen)
        layout_izquierda.addWidget(self.btn_imagen)
        layout_izquierda.addStretch()
        # Espacio extra para separar de los demás botones
        layout_izquierda.addSpacing(20)

        layout_principal = QHBoxLayout()
        layout_principal.addLayout(layout_izquierda)
        layout_principal.addLayout(layout_derecha)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_editar = QPushButton("Editar campos")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_informes = QPushButton("Generar informe")
        self.btn_guardar.setEnabled(False)
        self.btn_imagen.setEnabled(False)
        self.btn_imagen.clicked.connect(self.seleccionar_imagen)
        self.boton_evento = QPushButton("Funciones eventos")
        
        
        
        layout_izquierda.addWidget(self.boton_evento)
        layout_izquierda.addWidget(self.btn_editar)
        layout_izquierda.addWidget(self.btn_guardar)
        layout_izquierda.addWidget(self.btn_informes)
        
        

        if "codigo_motor" in columnas:
            idx_codigo = columnas.index("codigo_motor")
            codigo_motor = datos_motor[idx_codigo]
        else:
            codigo_motor = "desconocido"

        titulo_label_linea = QLabel("Línea: " + self.parent().nombre_linea +", "+ "Motor: "+ codigo_motor )
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

        # Contenedor con borde verde y márgenes
        contenedor = QFrame()
        contenedor_layout = QVBoxLayout(contenedor)
        contenedor_layout.setContentsMargins(40, 40, 40, 40)  # Espacio interno dentro del borde verde  


        contenedor_layout.addWidget(titulo_label_linea)
        contenedor_layout.addLayout(layout_principal)
        contenedor_layout.addLayout(btn_layout)

        
        #layout_general.setContentsMargins(20, 20, 20, 20)  # Espacio contra los bordes de pantalla

        layout.addWidget(contenedor)
      


        self.btn_editar.clicked.connect(self.habilitar_edicion)
        self.btn_guardar.clicked.connect(self.guardar_cambios)
        self.boton_evento.clicked.connect(self.eventos)
        self.btn_informes.clicked.connect(self.informes)
        
       
        self.cargar_eventos()

    def habilitar_edicion(self):
        self.btn_guardar.setEnabled(True)
        self.btn_editar.setEnabled(False)
        self.btn_imagen.setEnabled(True)

        for layout in [self.col1_layout, self.col2_layout, self.col3_layout]:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QLineEdit):
                    widget.setReadOnly(False)
                    widget.setStyleSheet("background-color: #ffffff;")  # Fondo blanco



    def guardar_cambios(self):
        global filtrado
        filtrado = 0
        self.btn_guardar.setEnabled(False)
        self.btn_editar.setEnabled(True)

        nuevos_valores = []
        columnas = []

        for layout in [self.col1_layout, self.col2_layout, self.col3_layout]:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QLineEdit):
                    nuevos_valores.append(widget.text())
                    columnas.append(widget.objectName())
                    widget.setStyleSheet("background-color: #d7dbdd;")  # Fondo gris claro

        if len(nuevos_valores) != len(columnas):
            QMessageBox.critical(self, "Error", "El número de datos no coincide con el número de columnas.")
            return
                
                
        datos_dict = dict(zip(columnas, nuevos_valores))  # Crea un diccionario con los nombres de las columnas como claves y los nuevos valores como valores
        

        conn = get_db_connection()
        cursor = conn.cursor()


        try:
            nombre_linea = self.parent().nombre_linea  #Se obtiene la línea desde el diálogo padre
            area = self.parent().area
            cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
            id_linea = cursor.fetchone()
            cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
            id_area = cursor.fetchone()
            if not id_linea or not id_area:
                QMessageBox.critical(self, "Error", "No se encontró la línea o el área seleccionada.")
                conn.close()
                return

            if self.nuevo:
                    # Agrega el nombre de la imagen si se seleccionó
                if self.nombre_imagen:
                    datos_dict["imagen_motor"] = self.nombre_imagen
                
                datos_dict["id_area"] = id_area[0]
                if "id_motor" in datos_dict:
                    datos_dict.pop("id_motor")
                campos = ", ".join(datos_dict.keys())
                placeholders = ", ".join(["?"] * len(datos_dict)) #placeholders para los valores, estos son los signos de interrogación que se usan en la consulta SQL para evitar inyecciones SQL
                valores = list(datos_dict.values())
                cursor.execute(f"INSERT INTO motores ({campos}) VALUES ({placeholders})", valores)
            
            else:
                nombre_motor = datos_dict["codigo_motor"]  

                if self.nombre_imagen:
                    datos_dict["imagen_motor"] = self.nombre_imagen

                if "id_motor" in datos_dict:
                    datos_dict.pop("id_motor")
                if "id_area" in datos_dict:
                    datos_dict.pop("id_area")  #pop elimina la clave del diccionario si existe

                set_clause = ", ".join([f"{col}=?" for col in datos_dict.keys()])
                valores = list(datos_dict.values())
                valores += [nombre_motor, id_area[0]]

                cursor.execute(
                    f"""UPDATE motores SET {set_clause}
                        WHERE codigo_motor=? AND id_area=?""",
                    valores
                )


            conn.commit()
            QMessageBox.information(self, "Guardado", "Los cambios se han guardado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar en la base de datos:\n{str(e)}")
        finally:
            conn.close()
        
        
    def seleccionar_imagen(self):
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Archivos de imagen (*.png *.jpg *.bmp)", options=opciones
        )

        if archivo:
            # --- 1. Preparar nombre único del archivo ---
            codigo_motor = self.obtener_codigo_motor()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"MOTOR_{codigo_motor}_{timestamp}.png"

            # --- 2. Determinar carpeta base donde sí se puede guardar ---
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)   # exe
            else:
                base = os.path.dirname(os.path.abspath(__file__))  # desarrollo

            # --- 3. Carpeta "Fotos" persistente junto al programa ---
            carpeta_fotos = os.path.join(base, "Fotos")
            os.makedirs(carpeta_fotos, exist_ok=True)

            # --- 4. Ruta FINAL del archivo ---
            ruta_final = os.path.join(carpeta_fotos, nombre_archivo)

            # --- 5. Guardar la imagen ---
            try:
                img = Image.open(archivo)
                img.save(ruta_final, format="PNG")

                self.nombre_imagen = nombre_archivo
                self.guardar_cambios()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo copiar la imagen:\n{str(e)}")

    def limpiar_imagenes_temporales(self):
        global imagenes_temporales
        global imagenes_cargadas

        for motor, imgs in imagenes_temporales.items():
            for tipo, ruta in imgs.items():
                if ruta and os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except Exception:
                        pass

        imagenes_temporales.clear()
        imagenes_cargadas = 0

    def agregar_evento(self):

        dialog = QDialog(self)
        dialog.finished.connect(lambda _: self.limpiar_imagenes_temporales())
        dialog.setWindowTitle("Agregar Evento")
        dialog.resize(500, 320) 
        dialog.fecha_bloqueada = False
        

        layout = QVBoxLayout(dialog)

        label_fecha = QLabel("Fecha:")
        edit_fecha = QDateEdit()
        edit_fecha.setCalendarPopup(True)
        edit_fecha.setDate(QDate.currentDate())
        edit_fecha.setDisplayFormat("dd-MM-yyyy")
        layout.addWidget(label_fecha)
        layout.addWidget(edit_fecha)

        # Tipo de evento - ComboBox
        label_tipo = QLabel("Tipo de evento:")
        layout.addWidget(label_tipo)
        
        combo_tipo = QComboBox()
        combo_tipo.addItems([
            "Mantenimiento correctivo", "Mantenimiento preventivo", "Mantenimiento predictivo",
            "Inspección Termográfica", "Sustitución de piezas", "Reparación", "Inspección de vibraciones",
            "Inspección de alineación", "Otro"
        ])
        layout.addWidget(combo_tipo)
        
        
        # --- Checklist para mantenimientos ---
        checklist_rubros = [
            "Limpieza", "Pintura", "Cambio de rodamientos", "Barnizado bobinado",
            "Reparación eje", "Cambio cuña", "Reparación tapaderas",
            "Reparación caja conexiones", "Cambio de conector", "Otro"
        ]
        
        
        grupo_checklist = QGroupBox("Rubros realizados")
        checklist_layout = QVBoxLayout(grupo_checklist)
        checkboxes = []
        for rubro in checklist_rubros:
            chk = QCheckBox(rubro)
            checklist_layout.addWidget(chk)
            checkboxes.append(chk)
        grupo_checklist.hide()
        layout.addWidget(grupo_checklist)
        
        # --- Campos para termografía ---
        grupo_termografico = QGroupBox("Datos termográficos")
        termografico_layout = QVBoxLayout(grupo_termografico)
        label_bobinas = QLabel("Temperatura de Cojinete frontal (°C):")
        edit_bobinas = QLineEdit()
        label_ambiente = QLabel("Temperatura de Estator (°C):")
        edit_ambiente = QLineEdit()
        label_cojinetes = QLabel("Temperatura de Cojinete trasero (°C):")
        edit_cojinetes = QLineEdit()
        label_velocidad = QLabel("Velocidad de máquina en metros por minuto (MPM):")
        edit_velocidad = QLineEdit()


        # Validador para temperaturas (0 a 800 °C, 2 decimal)
        validador_temp = QDoubleValidator(0.00, 800.00, 2)  # Permitir hasta 2 decimales, rango 0-800, 0.0 es el mínimo
        validador_temp.setNotation(QDoubleValidator.StandardNotation)

        edit_bobinas.setValidator(validador_temp)
        edit_ambiente.setValidator(validador_temp)
        edit_cojinetes.setValidator(validador_temp)

        # Validador SOLO enteros para velocidad
        validador_velocidad = QIntValidator(0, 1000000) # Rango de 0 a 100000 MPM
        edit_velocidad.setValidator(validador_velocidad)


        img_coji_frontal = QPushButton("Imagen")
        img_coji_trasero = QPushButton("Imagen")
        img_estator = QPushButton("Imagen")


        # Conectar los botones para seleccionar imágenes, pasando la fecha seleccionada
        img_coji_frontal.clicked.connect(lambda: seleccionar_y_guardar_imagen(self.obtener_codigo_motor(), "delantero", edit_fecha.date().toString("dd-MM-yyyy")))
        img_coji_trasero.clicked.connect(lambda: seleccionar_y_guardar_imagen(self.obtener_codigo_motor(), "trasero", edit_fecha.date().toString("dd-MM-yyyy")))
        img_estator.clicked.connect(lambda: seleccionar_y_guardar_imagen(self.obtener_codigo_motor(), "estator", edit_fecha.date().toString("dd-MM-yyyy")))

        # Ajustar diseño para alinear botones con etiquetas
        layout_bobinas = QHBoxLayout()
        layout_bobinas.addWidget(label_bobinas)
        layout_bobinas.addWidget(img_coji_frontal)
        img_coji_frontal.setFixedSize(150,63)  # Reducir tamaño del botón
        termografico_layout.addLayout(layout_bobinas)
        #espacio entre botón y campo de texto
        termografico_layout.addSpacing(30)  # Espacio vertical de 30 píxeles
        termografico_layout.addWidget(edit_bobinas)

        layout_ambiente = QHBoxLayout()
        layout_ambiente.addWidget(label_ambiente)
        layout_ambiente.addWidget(img_estator)
        img_estator.setFixedSize(150, 63)  # Reducir tamaño del botón
        termografico_layout.addLayout(layout_ambiente)
         #espacio entre botón y campo de texto
        termografico_layout.addSpacing(30)  # Espacio vertical 
        termografico_layout.addWidget(edit_ambiente)

        layout_cojinetes = QHBoxLayout()
        layout_cojinetes.addWidget(label_cojinetes)
        layout_cojinetes.addWidget(img_coji_trasero)
        img_coji_trasero.setFixedSize(150, 63)  # Reducir tamaño del botón
        termografico_layout.addLayout(layout_cojinetes)
         #espacio entre botón y campo de texto
        termografico_layout.addSpacing(30)  # Espacio vertical 
        termografico_layout.addWidget(edit_cojinetes)

        termografico_layout.addSpacing(30)  # Espacio vertical 
        termografico_layout.addWidget(label_velocidad)
        
        termografico_layout.addWidget(edit_velocidad)
        grupo_termografico.hide()  # Oculto por defecto

        # --- Campo de descripción normal ---
        label_descripcion = QLabel("Descripción:")
        edit_descripcion = QLineEdit()
        layout.addWidget(label_descripcion)
        layout.addWidget(edit_descripcion)
        
        
        # --- Campo para "Otro" ---
        label_otro_tipo = QLabel("Especificar otro tipo:")
        edit_otro_tipo = QLineEdit()
        label_otro_tipo.hide()
        edit_otro_tipo.hide()
        layout.addWidget(label_otro_tipo)
        layout.addWidget(edit_otro_tipo)

        # --- Agrega el grupo termográfico al layout, pero oculto ---
        layout.addWidget(grupo_termografico)






        def seleccionar_y_guardar_imagen(codigo_motor, tipo, fecha_seleccionada):
            global imagenes_temporales
            global imagenes_cargadas

            opciones = QFileDialog.Options()
            archivo, _ = QFileDialog.getOpenFileName(None, "Seleccionar imagen de termografía", "", "Archivos de imagen (*.png *.jpg *.bmp)", options=opciones)
            if archivo:

                # Crear carpeta de destino si no existe
                if getattr(sys, 'frozen', False):
                    base = os.path.dirname(sys.executable)
                else:
                    base = os.path.dirname(os.path.abspath(__file__))

                carpeta_termografia = os.path.join(base, "Imagenes_termografia")
                os.makedirs(carpeta_termografia, exist_ok=True)

                # Generar el nombre del archivo basado en el código del motor y el tipo
                if imagenes_cargadas >=3:
                    None
                
                else:
                    #Generar una marca de tiempo para asegurar que el nombre es único
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_imagen = f"{codigo_motor}-{tipo}-{fecha_seleccionada}_{timestamp}.png"
                    ruta_destino = os.path.join(carpeta_termografia, nombre_imagen)

                # Copiar la imagen seleccionada a la carpeta de destino
                try:

                    if imagenes_cargadas >=3:
                        None
                    else:
                        shutil.copyfile(archivo, ruta_destino)
                        if not dialog.fecha_bloqueada:
                            edit_fecha.setReadOnly(True)      # Bloquea la edición manual
                            edit_fecha.setButtonSymbols(0)    # Oculta el botón del calendario
                            edit_fecha.setStyleSheet("background-color: #e0e0e0;") # Estilo visual para indicar bloqueo
                            dialog.fecha_bloqueada = True     # Marca el estado como bloqueado

                    # Almacenar temporalmente la imagen seleccionada
                    
                    if codigo_motor not in imagenes_temporales:
                        imagenes_temporales[codigo_motor] = {"delantero": None, "trasero": None, "estator": None}

                    if imagenes_cargadas >=3:
                        None
                    else:
                        imagenes_temporales[codigo_motor][tipo] = ruta_destino
                    

                    # Verificar si ya se seleccionaron las tres imágenes
                    if all(imagenes_temporales[codigo_motor].values()) and imagenes_cargadas < 3:
                        # Guardar en la base de datos
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        nombre_linea = self.parent().nombre_linea  #Se obtiene la línea desde el diálogo padre
                        area = self.parent().area
                        cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
                        id_linea = cursor.fetchone()
                        cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
                        id_area = cursor.fetchone()
                        if not id_linea or not id_area:
                            QMessageBox.critical(self, "Error", "No se encontró la línea o el área seleccionada.")
                            conn.close()
                            return
                        
                        cursor.execute(
                                """
                                INSERT INTO Termografia (id_motor, coj_delantero, coj_trasero, Estator)
                                VALUES (
                                    (
                                        SELECT id_motor FROM motores 
                                        WHERE codigo_motor = ? 
                                        AND id_area = (
                                            SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?
                                        )
                                    ),
                                    ?, ?, ?
                                )
                                """,
                                (
                                    codigo_motor,                 # Para el SELECT de id_motor
                                    area,                         # Para el SELECT de id_area en subconsulta
                                    id_linea[0],                  # Para el SELECT de id_area en subconsulta
                                    imagenes_temporales[codigo_motor]["delantero"],
                                    imagenes_temporales[codigo_motor]["trasero"],
                                    imagenes_temporales[codigo_motor]["estator"],
                                )
                            )

                        conn.commit()
                        conn.close()

                        # Limpiar el almacenamiento temporal para este motor
                        del imagenes_temporales[codigo_motor]

                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Información")
                        msg_box.setText("Las imágenes se guardaron correctamente en la base de datos.")
                        msg_box.setIcon(QMessageBox.Information)
                        imagenes_cargadas=3
                         # Personalizar el estilo del cuadro de mensaje
                        msg_box.setStyleSheet("""
                            QMessageBox {
                                background-color: #f4f6fb;  /* Fondo del cuadro */
                                border: 3px solid #229954; /* Borde verde */
                                border-radius: 10px;       /* Bordes redondeados */
                            }
                            QLabel {
                                color: #222;              /* Color del texto */
                                font-size: 18px;          /* Tamaño de fuente */
                            }
                            QPushButton {
                                background-color: #1976d2; /* Botón azul */
                                color: white;              /* Texto blanco */
                                border-radius: 8px;        /* Bordes redondeados */
                                padding: 6px 12px;         /* Espaciado interno */
                                font-size: 18px;           /* Tamaño de fuente */
                                font-weight: bold;         /* Negrita */
                                border: none;              /* Sin borde */
                            }
                            QPushButton:hover {
                                background-color: #1565c0; /* Azul más oscuro al pasar el mouse */
                            }
                        """)

                        # Mostrar el cuadro de mensaje
                        msg_box.exec_()

                    elif imagenes_cargadas == 3:
                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Información")
                        msg_box.setText("Todas las imágenes ya han sido cargadas.")
                        msg_box.setIcon(QMessageBox.Information)
                         # Personalizar el estilo del cuadro de mensaje
                        msg_box.setStyleSheet("""
                            QMessageBox {
                                background-color: #f4f6fb;  /* Fondo del cuadro */
                                border: 3px solid #229954; /* Borde verde */
                                border-radius: 10px;       /* Bordes redondeados */
                            }
                            QLabel {
                                color: #222;              /* Color del texto */
                                font-size: 18px;          /* Tamaño de fuente */
                            }
                            QPushButton {
                                background-color: #1976d2; /* Botón azul */
                                color: white;              /* Texto blanco */
                                border-radius: 8px;        /* Bordes redondeados */
                                padding: 6px 12px;         /* Espaciado interno */
                                font-size: 14px;           /* Tamaño de fuente */
                                font-weight: bold;         /* Negrita */
                                border: none;              /* Sin borde */
                            }
                            QPushButton:hover {
                                background-color: #1565c0; /* Azul más oscuro al pasar el mouse */
                            }
                        """)
                        # Mostrar el cuadro de mensaje
                        msg_box.exec_()

                                              
                    else:
                        #QMessageBox.information(None, "Información", f"Imagen guardada temporalmente, Selecciona las imágenes restantes.")
                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Información")
                        msg_box.setText("Imagen guardada temporalmente, Selecciona las imágenes restantes.")
                        imagenes_cargadas = imagenes_cargadas+1
                        msg_box.setIcon(QMessageBox.Information)
                       

                        # Personalizar el estilo del cuadro de mensaje
                        msg_box.setStyleSheet("""
                            QMessageBox {
                                background-color: #f4f6fb;  /* Fondo del cuadro */
                                border: 3px solid #229954; /* Borde verde */
                                border-radius: 10px;       /* Bordes redondeados */
                            }
                            QLabel {
                                color: #222;              /* Color del texto */
                                font-size: 18px;          /* Tamaño de fuente */
                            }
                            QPushButton {
                                background-color: #1976d2; /* Botón azul */
                                color: white;              /* Texto blanco */
                                border-radius: 8px;        /* Bordes redondeados */
                                padding: 6px 12px;         /* Espaciado interno */
                                font-size: 14px;           /* Tamaño de fuente */
                                font-weight: bold;         /* Negrita */
                                border: none;              /* Sin borde */
                            }
                            QPushButton:hover {
                                background-color: #1565c0; /* Azul más oscuro al pasar el mouse */
                            }
                        """)

                        # Mostrar el cuadro de mensaje
                        msg_box.exec_()
                except Exception as e:
                    QMessageBox.critical(None, "Error", f"No se pudo guardar la imagen: {str(e)}")


        # --- Mostrar/ocultar campos según selección ---
        def actualizar_campos(index):
            tipo = combo_tipo.currentText()
            if tipo == "Inspección Termográfica":
                grupo_termografico.show()
                label_descripcion.hide()
                edit_descripcion.hide()
                label_otro_tipo.hide()
                edit_otro_tipo.hide()
                grupo_checklist.hide()
                dialog.setFixedSize(500,600)
                
                dialog.updateGeometry()
                
            elif tipo == "Otro":
                grupo_termografico.hide()
                label_descripcion.show()
                edit_descripcion.show()
                label_otro_tipo.show()
                edit_otro_tipo.show()
                grupo_checklist.hide()
                
                dialog.setFixedSize(500, 400)
              #  dialog.resize(500, 400)  # Tamaño intermedio
                
               
                
            elif tipo in ("Mantenimiento correctivo", "Mantenimiento preventivo", "Mantenimiento predictivo"):
                grupo_checklist.show()
                grupo_termografico.hide()
                label_descripcion.hide()
                edit_descripcion.hide()
                label_otro_tipo.hide()
                edit_otro_tipo.hide()
                dialog.setFixedSize(500,600)
               
                dialog.updateGeometry()
            
            else:
                grupo_termografico.hide()
                label_descripcion.show()
                edit_descripcion.show()
                label_otro_tipo.hide()
                edit_otro_tipo.hide()
                grupo_checklist.hide()
                dialog.setFixedSize(500, 320)
              
                dialog.updateGeometry()

        combo_tipo.currentIndexChanged.connect(actualizar_campos)
        actualizar_campos(0)  # Inicializa la visibilidad

        btn_guardar_evento = QPushButton("Guardar evento")
        layout.addWidget(btn_guardar_evento)

        def guardar_evento():
            global filtrado
            global imagenes_cargadas
            rubros_seleccionados = [chk.text() for chk in checkboxes if chk.isChecked()]
            
            fecha = edit_fecha.date().toString("dd-MM-yyyy")
            tipo = combo_tipo.currentText()
            if tipo == "Inspección Termográfica":
                if not edit_bobinas.hasAcceptableInput() \
                    or not edit_ambiente.hasAcceptableInput() \
                    or not edit_cojinetes.hasAcceptableInput():
                        QMessageBox.warning(
                            dialog,
                            "Datos inválidos",
                            "Las temperaturas deben ser valores numéricos válidos."
                        )
                        return
                descripcion = f"Cojinete frontal: {edit_bobinas.text().strip()}°C, Estator: {edit_ambiente.text().strip()}°C, Cojinete trasero: {edit_cojinetes.text().strip()}°C, Velocidad: {edit_cojinetes.text().strip()}MPM"
            elif tipo == "Otro":
                tipo = edit_otro_tipo.text().strip()
                descripcion = edit_descripcion.text().strip()
                
            elif tipo  in ("Mantenimiento correctivo", "Mantenimiento preventivo", "Mantenimiento predictivo") and rubros_seleccionados:
                descripcion = "Rubros: " + ", ".join(rubros_seleccionados)
            
            
            else:
                descripcion = edit_descripcion.text().strip()

            if not fecha or not tipo or not descripcion:
                QMessageBox.warning(dialog, "Advertencia", "Todos los campos son obligatorios.")
                return
            
             # Pide el nombre de la persona que modifica
            nombre_persona, ok = QInputDialog.getText(dialog, "Nombre", "Ingrese su nombre:")
            nombre_persona = nombre_persona.strip().title()
            if not ok or not nombre_persona.strip():
                QMessageBox.warning(dialog, "Advertencia", "Debe ingresar su nombre.")
                return

            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (self.parent().nombre_linea,))
                id_linea = cursor.fetchone()
                if not id_linea:
                    raise Exception("No se encontró la línea")

                cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (self.parent().area, id_linea[0]))
                id_area = cursor.fetchone()
                if not id_area:
                    raise Exception("No se encontró el área")

                codigo_motor = self.obtener_codigo_motor().strip()
                cursor.execute("SELECT id_motor FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
        
                id_motor = cursor.fetchone()
                if not id_motor:
                    filtrado = 0
                    raise Exception("No se encontró el motor")
            

                if tipo == "Inspección Termográfica":

                    if imagenes_cargadas <3:
                        QMessageBox.warning(dialog, "Advertencia", "Debe cargar las tres imágenes de termografía antes de guardar el evento.")
                        return
                    else:
                        
                        cursor.execute("""
                            INSERT INTO eventos (fecha, tipo_evento, descripcion, id_motor, Persona_modifico, id_termografia)
                            VALUES (?, ?, ?, ?, ?,(SELECT  MAX(id_termo) FROM Termografia WHERE id_motor = ?))
                        """, (fecha, tipo, descripcion, id_motor[0], nombre_persona.strip(), id_motor[0]))
                        imagenes_cargadas = 0  # Reinicia el contador para la próxima vez
                else:
                    cursor.execute("""
                        INSERT INTO eventos (fecha, tipo_evento, descripcion, id_motor, Persona_modifico)
                        VALUES (?, ?, ?, ?, ?)
                    """, (fecha, tipo, descripcion, id_motor[0], nombre_persona.strip()))

                conn.commit() # Guarda los cambios
                QMessageBox.information(dialog, "Éxito", "Evento agregado correctamente.")
                imagenes_cargadas = 0
                filtrado = 0
                dialog.accept()
                self.cargar_eventos()


            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"No se pudo agregar el evento:\n{str(e)}")
                imagenes_cargadas = 0


        btn_guardar_evento.clicked.connect(guardar_evento)  # Conecta el botón al método guardar_evento
        dialog.exec_()        
        
        
    def obtener_codigo_motor(self):
        for layout in [self.col1_layout, self.col2_layout, self.col3_layout]:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QLineEdit) and widget.objectName() == "codigo_motor":
                    return widget.text().strip()  # Retorna el código del motor, strip elimina espacios en blanco
                
        return None

    def filtrar_eventos(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Filtrar Eventos")
        dialog.setFixedSize(400, 350) #Tamaño alto x ancho

        layout = QVBoxLayout(dialog)
        
        combo_tipo = QComboBox()
        combo_tipo.addItems([
            "Mantenimiento correctivo", "Mantenimiento preventivo", "Mantenimiento predictivo",
            "Inspección Termográfica", "Sustitución de piezas", "Reparación", "Inspección de vibraciones",
            "Inspección de alineación", "Otro", "Por fecha"
        ])
        layout.addWidget(combo_tipo)

        # Desplegable de tipo de evento
        layout.addWidget(combo_tipo)

        # Campo adicional para "Otro"
        label_otro_tipo = QLabel("Especificar otro tipo:")
        edit_otro_tipo = QLineEdit()
        label_otro_tipo.hide()
        edit_otro_tipo.hide()
        layout.addWidget(label_otro_tipo)
        layout.addWidget(edit_otro_tipo)

        # Campos de fecha SIEMPRE presentes pero ocultos por defecto
        label_fecha_inicio = QLabel("Fecha inicio:")
        edit_fecha_inicio = QDateEdit()
        edit_fecha_inicio.setCalendarPopup(True)
        edit_fecha_inicio.setDisplayFormat("dd-MM-yyyy")
        edit_fecha_inicio.setDate(QDate.currentDate().addMonths(-1)) 

        label_fecha_fin = QLabel("Fecha fin:")
        edit_fecha_fin = QDateEdit()
        edit_fecha_fin.setCalendarPopup(True)
        edit_fecha_fin.setDisplayFormat("dd-MM-yyyy")
        edit_fecha_fin.setDate(QDate.currentDate())


        label_fecha_inicio.hide()
        edit_fecha_inicio.hide()
        label_fecha_fin.hide()
        edit_fecha_fin.hide()


        layout.addWidget(label_fecha_inicio)
        layout.addWidget(edit_fecha_inicio)
        layout.addWidget(label_fecha_fin)
        layout.addWidget(edit_fecha_fin)


        #Labels para fechas de cada campo
        label_fecha_inicio1 = QLabel("Fecha inicio:")
        edit_fecha_inicio1 = QDateEdit()
        edit_fecha_inicio1.setCalendarPopup(True)
        edit_fecha_inicio1.setDisplayFormat("dd-MM-yyyy")
        edit_fecha_inicio1.setDate(QDate.currentDate().addMonths(-1)) 

        label_fecha_fin1 = QLabel("Fecha fin:")
        edit_fecha_fin1 = QDateEdit()
        edit_fecha_fin1.setCalendarPopup(True)
        edit_fecha_fin1.setDisplayFormat("dd-MM-yyyy")
        edit_fecha_fin1.setDate(QDate.currentDate())

        layout.addWidget(label_fecha_inicio1)
        layout.addWidget(edit_fecha_inicio1)
        layout.addWidget(label_fecha_fin1)
        layout.addWidget(edit_fecha_fin1)



        # Mostrar/ocultar campo adicional si selecciona "Otro"
        def actualizar_campos(index):
            if combo_tipo.currentText() == "Otro":

                label_otro_tipo.show()
                edit_otro_tipo.show()
                label_fecha_inicio.hide()
                edit_fecha_inicio.hide()
                label_fecha_fin.hide()
                edit_fecha_fin.hide()

            elif combo_tipo.currentText() == "Por fecha":
                
                label_otro_tipo.hide()
                edit_otro_tipo.hide()
                label_fecha_inicio.show()
                edit_fecha_inicio.show()
                label_fecha_fin.show()
                edit_fecha_fin.show()
                label_fecha_inicio1.hide()
                edit_fecha_inicio1.hide()
                label_fecha_fin1.hide()
                edit_fecha_fin1.hide()

            else:

                label_otro_tipo.hide()
                edit_otro_tipo.hide()
                label_fecha_inicio.hide()
                edit_fecha_inicio.hide()
                label_fecha_fin.hide()
                edit_fecha_fin.hide()
                label_fecha_inicio1.show()
                edit_fecha_inicio1.show()
                label_fecha_fin1.show()
                edit_fecha_fin1.show()


        combo_tipo.currentIndexChanged.connect(actualizar_campos)
        #actualizar_campos(0) # Inicializa la visibilidad

        btn_filtrar = QPushButton("Filtrar eventos")
        layout.addWidget(btn_filtrar)

        def aplicar_filtro():
            global filtrado
            global fecha_1  
            global fecha_2
            tipo_filtro = combo_tipo.currentText()
            if tipo_filtro == "Otro":
                tipo_filtro = edit_otro_tipo.text().strip()
                if not tipo_filtro:
                    QMessageBox.warning(dialog, "Advertencia", "Debe ingresar un tipo de evento válido.")
                    return
                
        
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                codigo_motor = self.obtener_codigo_motor().strip()
                nombre_linea = self.parent().nombre_linea
                area = self.parent().area

                fecha_inicio_sqlite1 = edit_fecha_inicio1.date().toString("yyyy-MM-dd")
                fecha_fin_sqlite1 = edit_fecha_fin1.date().toString("yyyy-MM-dd")

                # Obtener ID del motor
                cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
                id_linea = cursor.fetchone()
                cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
                id_area = cursor.fetchone()
                cursor.execute("SELECT id_motor FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
        
                id_motor = cursor.fetchone()
                if not id_motor:
                    QMessageBox.warning(dialog, "Advertencia", "No se encontró el motor.")
                    filtrado = 0
                    conn.close()
                    return


                # Filtrar eventos

                if tipo_filtro == "Otro":
                    tipo_filtro = edit_otro_tipo.text().strip()  #Si es "Otro", toma el texto ingresado,strip elimina espacios en blanco
                    if not tipo_filtro:
                        QMessageBox.warning(dialog, "Advertencia", "Debe ingresar un tipo de evento válido.")
                        conn.close()
                        return
                    # Parámetros para la consulta (ID Motor, Tipo, Fecha Inicio, Fecha Fin)
                    params = (id_motor[0], tipo_filtro, fecha_inicio_sqlite1, fecha_fin_sqlite1)
                    
                    cursor.execute(
                        """
                        SELECT fecha, tipo_evento, descripcion, Persona_modifico 
                        FROM eventos 
                        WHERE id_motor = ? AND tipo_evento = ?
                        
                        -- AÑADIDA CLÁUSULA DE FECHA
                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) >= date(?) 
                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) <= date(?) 
                        ORDER BY date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) ASC
                        """,
                        params
                    )

                elif tipo_filtro == "Inspección Termográfica":
                
                # Parámetros a pasar al execute: ID Motor, Tipo, Fecha Inicio, Fecha Fin
                    params = (
                        id_motor[0], 
                        tipo_filtro, 
                        fecha_inicio_sqlite1, 
                        fecha_fin_sqlite1
                    )
                    
                    cursor.execute("""
                        SELECT e.fecha, e.tipo_evento, e.descripcion, e.Persona_modifico, t.coj_delantero, t.coj_trasero, t.Estator
                        FROM eventos e
                        LEFT JOIN Termografia t ON e.id_termografia = t.id_termo
                        WHERE e.id_motor = ? AND e.tipo_evento = ?
                        
                    
                        AND date(substr(e.fecha, 7, 4) || '-' || substr(e.fecha, 4, 2) || '-' || substr(e.fecha, 1, 2)) >= date(?) 
                        AND date(substr(e.fecha, 7, 4) || '-' || substr(e.fecha, 4, 2) || '-' || substr(e.fecha, 1, 2)) <= date(?)
                        
                        ORDER BY date(substr(e.fecha, 7, 4) || '-' || substr(e.fecha, 4, 2) || '-' || substr(e.fecha, 1, 2)) ASC
                    """, params)


                elif tipo_filtro == "Por fecha":
        

                    fecha_inicio_sqlite = edit_fecha_inicio.date().toString("yyyy-MM-dd") # Convierte la fecha a cadena en formato yyyy-MM-dd
                    fecha_fin_sqlite = edit_fecha_fin.date().toString("yyyy-MM-dd")  # Convierte la fecha a cadena en formato yyyy-MM-dd
                    #.toDate() convierte a objeto de fecha

                    #.date hace que tome solo la parte de la fecha, sin hora
                    #.toString("dd-MM-yyyy") convierte la fecha a cadena en formato dd-MM-yyyy
                    #toString se usa para convertir objetos de fecha a cadenas de texto en un formato específico

                    cursor.execute(
                        """
                        SELECT e.fecha, e.tipo_evento, e.descripcion, e.Persona_modifico, t.coj_delantero, t.coj_trasero, t.Estator
                        FROM eventos e
                        LEFT JOIN Termografia t ON e.id_termografia = t.id_termo
                        WHERE e.id_motor = ?

                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) >= date(?) 
                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) <= date(?)
                        ORDER BY date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) ASC
                        """,
                        (id_motor[0], fecha_inicio_sqlite, fecha_fin_sqlite)
                    )

                     # Obtener eventos del motor con datos de termografía si están disponibles
         
                else:


                    cursor.execute(
                        """
                        SELECT fecha, tipo_evento, descripcion, Persona_modifico
                        FROM eventos
                        WHERE id_motor = ? AND tipo_evento = ?
                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) >= date(?) 
                        AND date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) <= date(?) 
                        ORDER BY date(substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) ASC
                        """,
                        (id_motor[0], tipo_filtro, fecha_inicio_sqlite1, fecha_fin_sqlite1)
                    )

                     #Como funciona esto es: fecha:
               # 23-04-2025

                #substr(fecha, 7, 4) → toma los 4 caracteres desde la posición 7: "2025"
                #substr(fecha, 4, 2) → toma 2 caracteres desde la posición 4: "04"
                #substr(fecha, 1, 2) → toma 2 caracteres desde la posición 1: "23"
                #Luego, los une con guiones:
                #"2025" || '-' || "04" || '-' || "23" → "2025-04-23"

                #esto porque SQl no entiende español, solo ingles


                
                eventos = cursor.fetchall() #fetchall obtiene todos los resultados de la consulta, se usa cuando se esperan múltiples filas

                self.tabla_eventos.clearContents()
                self.tabla_eventos.setRowCount(len(eventos))
              
              
                # Función para manejar eventos termográficos
                def manejar_evento_termografico(i, evento):
                    fecha, tipo, descripcion, persona, coj_delantero, coj_trasero, estator = evento

                    # Resaltar temperaturas en la descripción
                    import re
                    def negrita_temperaturas(texto):
                        return re.sub(r'(\d+\s*°[CF]|\d+\s*RPM|\d+\s*MPM)', r'<b>\1</b>', texto)

                    html = negrita_temperaturas(descripcion)

                    # Crear contenedor para texto y botón
                    contenedor = QWidget()
                    layout_contenedor = QHBoxLayout(contenedor)
                    layout_contenedor.setContentsMargins(0, 0, 0, 0)

                    label_html = QLabel()
                    label_html.setTextFormat(Qt.RichText)
                    label_html.setText(html)

                    btn_ver_imagen = QPushButton("Imágenes")
                    btn_ver_imagen.setFixedSize(150, 40)
                    btn_ver_imagen.clicked.connect(lambda _, c=coj_delantero, t=coj_trasero, e=estator, f=fecha: abrir_ventana_imagenes(c, t, e,f))
                    btn_ver_imagen.setStyleSheet("""
                        QPushButton {
                            background-color: #1976d2; 
                            color: white;
                            border-radius: 8px;
                            padding: 1px;
                            font-size: 14px;
                            font-weight: normal;
                            border: 1px solid #1976d2;
                        }
                        QPushButton:hover { background-color: #1565c0; }
                    """)

                    layout_contenedor.addWidget(label_html)
                    layout_contenedor.addWidget(btn_ver_imagen)
                    self.tabla_eventos.setCellWidget(i, 2, contenedor)

                    # Agregar los demás datos
                    self.tabla_eventos.setItem(i, 0, QTableWidgetItem(fecha))
                    self.tabla_eventos.setItem(i, 1, QTableWidgetItem(tipo))
                    self.tabla_eventos.setItem(i, 3, QTableWidgetItem(persona))

                # Función para manejar eventos generales
                def manejar_evento_general(i, evento):
                    fecha, tipo, descripcion, persona = evento[:4]
                    self.tabla_eventos.setItem(i, 0, QTableWidgetItem(fecha))
                    self.tabla_eventos.setItem(i, 1, QTableWidgetItem(tipo))
                    self.tabla_eventos.setItem(i, 2, QTableWidgetItem(descripcion))
                    self.tabla_eventos.setItem(i, 3, QTableWidgetItem(persona))

                # Función para abrir ventana de imágenes
                def abrir_ventana_imagenes(coj_delantero, coj_trasero, estator, fecha):
                    dialog = MostrarImagenesDialog(self, fecha)
                    dialog.mostrar_imagen(coj_delantero, coj_trasero, estator)
                    dialog.exec_()

                # Procesar eventos
                for i, evento in enumerate(eventos):
                    tipo = evento[1]  # Asegurarse de que tipo esté definido
                    if tipo.lower() == "inspección termográfica":
                        manejar_evento_termografico(i, evento)
                    else:
                        manejar_evento_general(i, evento)

                dialog.accept()
                filtrado = 1
                # Determinar qué campos de fecha se usaron según la selección
                seleccionado = combo_tipo.currentText()
                if seleccionado == "Por fecha":
                    fecha_1 = edit_fecha_inicio.date().toString("dd-MM-yyyy")
                    fecha_2 = edit_fecha_fin.date().toString("dd-MM-yyyy")
                elif seleccionado == "Otro":
                    fecha_1 = edit_fecha_inicio1.date().toString("dd-MM-yyyy")
                    fecha_2 = edit_fecha_fin1.date().toString("dd-MM-yyyy")
                else:
                    # Para filtros por tipo que usan los campos 1 (edit_fecha_inicio1 / edit_fecha_fin1)
                    fecha_1 = edit_fecha_inicio1.date().toString("dd-MM-yyyy")
                    fecha_2 = edit_fecha_fin1.date().toString("dd-MM-yyyy")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo filtrar:\n{str(e)}")
                filtrado = 0
                fecha_1 = ""
                fecha_2 = ""
            finally:
                conn.close()

        btn_filtrar.clicked.connect(aplicar_filtro)
        dialog.exec_()

        
        
    def cargar_eventos(self):
        global filtrado
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            codigo_motor = self.obtener_codigo_motor().strip()
            nombre_linea = self.parent().nombre_linea
            area = self.parent().area

            # Obtener ID del área
            cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
            id_linea = cursor.fetchone()
            cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
            id_area = cursor.fetchone()

            # Obtener ID del motor
            cursor.execute("SELECT id_motor FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
            id_motor = cursor.fetchone()

            if not id_motor:
                print("No se encontró el motor para cargar eventos.")
                filtrado = 0
                return

            # Obtener eventos del motor con datos de termografía si están disponibles
            cursor.execute(
                """
                SELECT e.fecha, e.tipo_evento, e.descripcion, e.Persona_modifico, t.coj_delantero, t.coj_trasero, t.Estator
                FROM eventos e
                LEFT JOIN Termografia t ON e.id_termografia = t.id_termo
                WHERE e.id_motor = ?
                ORDER BY date(substr(e.fecha, 7, 4) || '-' || substr(e.fecha, 4, 2) || '-' || substr(e.fecha, 1, 2)) ASC
                """,
                (id_motor[0],)
            )

            eventos = cursor.fetchall()
        

            self.tabla_eventos.clearContents()
            self.tabla_eventos.setRowCount(len(eventos))

            # Función para manejar eventos termográficos
            def manejar_evento_termografico(i, evento):
                fecha, tipo, descripcion, persona, coj_delantero, coj_trasero, estator = evento

                # Resaltar temperaturas en la descripción
                import re
                def negrita_temperaturas(texto):
                    return re.sub(r'(\d+\s*°[CF]|\d+\s*RPM|\d+\s*MPM)', r'<b>\1</b>', texto)

                html = negrita_temperaturas(descripcion)

                # Crear contenedor para texto y botón
                contenedor = QWidget()
                layout_contenedor = QHBoxLayout(contenedor)
                layout_contenedor.setContentsMargins(0, 0, 0, 0)

                label_html = QLabel()
                label_html.setTextFormat(Qt.RichText)
                label_html.setText(html)

                btn_ver_imagen = QPushButton("Imágenes")
                btn_ver_imagen.setFixedSize(150, 40)
                btn_ver_imagen.clicked.connect(lambda _, c=coj_delantero, t=coj_trasero, e=estator, f=fecha: abrir_ventana_imagenes(c, t, e,f))
                btn_ver_imagen.setStyleSheet("""
                    QPushButton {
                        background-color: #1976d2; 
                        color: white;
                        border-radius: 8px;
                        padding: 1px;
                        font-size: 14px;
                        font-weight: normal;
                        border: 1px solid #1976d2;
                    }
                    QPushButton:hover { background-color: #1565c0; }
                """)

                layout_contenedor.addWidget(label_html)
                layout_contenedor.addWidget(btn_ver_imagen)
                self.tabla_eventos.setCellWidget(i, 2, contenedor)

                # Agregar los demás datos
                self.tabla_eventos.setItem(i, 0, QTableWidgetItem(fecha))
                self.tabla_eventos.setItem(i, 1, QTableWidgetItem(tipo))
                self.tabla_eventos.setItem(i, 3, QTableWidgetItem(persona))

            # Función para manejar eventos generales
            def manejar_evento_general(i, evento):
                fecha, tipo, descripcion, persona = evento[:4]
                self.tabla_eventos.setItem(i, 0, QTableWidgetItem(fecha))
                self.tabla_eventos.setItem(i, 1, QTableWidgetItem(tipo))
                self.tabla_eventos.setItem(i, 2, QTableWidgetItem(descripcion))
                self.tabla_eventos.setItem(i, 3, QTableWidgetItem(persona))

            # Función para abrir ventana de imágenes
            def abrir_ventana_imagenes(coj_delantero, coj_trasero, estator, fecha):
                dialog = MostrarImagenesDialog(self, fecha)
                dialog.mostrar_imagen(coj_delantero, coj_trasero, estator)
                dialog.exec_()

            # Procesar eventos
            for i, evento in enumerate(eventos):
                tipo = evento[1]  # Asegurarse de que tipo esté definido
                if tipo.lower() == "inspección termográfica":
                    manejar_evento_termografico(i, evento)
                else:
                    manejar_evento_general(i, evento)

            filtrado = 0

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los eventos:\n{str(e)}")
            filtrado = 0
        finally:
            if 'conn' in locals():
                conn.close()
                
            

    def quitar_filtro(self):
        self.tabla_eventos.clearContents()
        self.cargar_eventos()


    def abrir_ventana_imagenes(self):
        dialog = MostrarImagenesDialog(self)
        dialog.exec_()         
            
    def eliminar_eventos(self):
        global filtrado
        dialog = QDialog(self)
        dialog.setWindowTitle("Eliminar evento")
        dialog.setFixedSize(1500, 400)
        layout = QVBoxLayout(dialog)

        # 1. Obtener eventos del motor
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            codigo_motor = self.obtener_codigo_motor().strip()
            nombre_linea = self.parent().nombre_linea
            area = self.parent().area

            cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
            id_linea = cursor.fetchone()
            cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
            id_area = cursor.fetchone()
            cursor.execute("SELECT id_motor FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
            id_motor = cursor.fetchone()

            if not id_motor:
                QMessageBox.warning(dialog, "Advertencia", "No se encontró el motor.")
                return

            cursor.execute("""
                SELECT id_evento, fecha, tipo_evento, descripcion, Persona_modifico
                FROM eventos
                WHERE id_motor = ?
                ORDER BY fecha ASC
            """, (id_motor[0],))
            
            eventos = cursor.fetchall()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"No se pudieron cargar los eventos:\n{str(e)}")
            return
        finally:
            conn.close()
            filtrado = 0

        # 2. Mostrar eventos en una lista
        lista = QListWidget()
        for id_evento, fecha, tipo, descripcion, persona in eventos:
            texto = f"{fecha} | {tipo} | {descripcion[:500]}..."  # Solo muestra datos amigables
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, id_evento)  # Guarda el id_evento de forma interna
            lista.addItem(item)
        layout.addWidget(lista)

        btn_eliminar = QPushButton("Eliminar seleccionado")
        layout.addWidget(btn_eliminar)

        def eliminar_seleccionado():
            global filtrado
            item = lista.currentItem()
            if not item:
                QMessageBox.warning(dialog, "Advertencia", "Seleccione un evento para eliminar.")
                return
            id_evento = item.data(Qt.UserRole)  # Recupera el id interno
            confirm = QMessageBox.question(dialog, "Confirmar", "¿Está seguro de eliminar este evento?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    #Obtener el id_termografia del evento

                    cursor.execute("SELECT id_termografia FROM eventos WHERE id_evento = ?", 
                                (id_evento,))
                    resultado_evento = cursor.fetchone()
                    id_termo = resultado_evento[0]

                    cursor.execute("DELETE FROM eventos WHERE id_evento = ?", (id_evento,))
                    conn.commit()

                    # Paso 1: Obtener rutas de imágenes asociadas al id_termo
                    if id_termo:
                        cursor.execute("SELECT coj_delantero, coj_trasero, Estator FROM Termografia WHERE id_termo = ?", 
                                    (id_termo,))
                        rutas = cursor.fetchone()
                        
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

                    cursor.execute("DELETE FROM Termografia WHERE id_termo = ?", (id_termo,))
                    conn.commit()

                

                    QMessageBox.information(dialog, "Éxito", "Evento eliminado correctamente.")
                    dialog.accept()
                 
                    filtrado = 0
                    self.cargar_eventos()
                except Exception as e:
                    QMessageBox.critical(dialog, "Error", f"No se pudo eliminar el evento:\n{str(e)}")
                
                    filtrado = 0
                finally:
                    conn.close()

        btn_eliminar.clicked.connect(eliminar_seleccionado)
        dialog.exec_()


        #Si se desea editar un evento, se puede eliminar y volver a crear con los datos correctos.

    def editar_eventos(self):
        pass
        
            
    def eventos(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Funciones de eventos")
        dialog.setFixedSize(500, 400)
        layout = QVBoxLayout(dialog)

        btn_nuevo = QPushButton("Agregar evento")
    
        btn_eliminar = QPushButton("Eliminar evento")
        boton_filtro = QPushButton("Filtrar eventos")
        eliminar_filtro = QPushButton("Eliminar filtro")

        btn_layout = QVBoxLayout()
        btn_layout.addWidget(btn_nuevo)
       
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addWidget(boton_filtro)
        btn_layout.addWidget(eliminar_filtro)
        layout.addLayout(btn_layout)

        btn_nuevo.clicked.connect(dialog.accept)
        btn_nuevo.clicked.connect(self.agregar_evento)
        
        btn_eliminar.clicked.connect(dialog.accept)
        btn_eliminar.clicked.connect(self.eliminar_eventos)
        
        boton_filtro.clicked.connect(dialog.accept)
        boton_filtro.clicked.connect(self.filtrar_eventos)
        
        eliminar_filtro.clicked.connect(dialog.accept)
        eliminar_filtro.clicked.connect(self.quitar_filtro)

        dialog.exec_()
        
    
    def generar_nombre_carpeta_unico(self, base_path, nombre_base):
        """
        Si 'nombre_base' existe, genera nombre_base_2, nombre_base_3, etc.
        """
        carpeta = os.path.join(base_path, nombre_base)


        if not os.path.exists(carpeta):
            return nombre_base  # No existe → usar este nombre

        contador = 2
        while True:
            nuevo_nombre = f"{nombre_base}_{contador}" #f "" para formateo de cadenas
            nueva_carpeta = os.path.join(base_path, nuevo_nombre)

            if not os.path.exists(nueva_carpeta):
                return nuevo_nombre

            contador += 1

        
    def informes(self):
        global filtrado
        global fecha_1
        global fecha_2
        try:
            # 1. Extraer datos del motor desde los campos
            datos_motor_dict = {}
            for layout in [self.col1_layout, self.col2_layout, self.col3_layout]:
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if isinstance(widget, QLineEdit):
                        nombre = widget.objectName()
                        valor = widget.text() # Obtiene el texto del QLineEdit
                        nombre_amigable = self.NOMBRES_AMIGABLES.get(nombre, nombre)
                        datos_motor_dict[nombre_amigable] = valor
                        

            # Agregar línea y área
            if self.parent():
                datos_motor_dict["Línea"] = self.parent().nombre_linea
                datos_motor_dict["Área"] = self.parent().area
                
           

            # 2. Extraer eventos desde la tabla
            eventos = []
            for fila in range(self.tabla_eventos.rowCount()):
                fila_evento = []
                for col in range(self.tabla_eventos.columnCount()):
                    item = self.tabla_eventos.item(fila, col)
                    texto_extraido = ""

                    if item:
                        # Caso 1: Hay QTableWidgetItem (para Fecha, Tipo, Realizado por, etc.)
                        texto_extraido = item.text()
                    else:
                        # Caso 2: Hay un widget personalizado (Descripción)
                        widget = self.tabla_eventos.cellWidget(fila, col)
                        
                        # Lista de widgets a revisar: el propio widget y sus posibles hijos
                        widgets_a_revisar = []
                        if widget:
                            widgets_a_revisar.append(widget)
                            
                            # Si tiene un layout, buscamos dentro del contenedor (el caso del QWidget genérico)
                            if widget.layout():
                                for i in range(widget.layout().count()):
                                    child = widget.layout().itemAt(i).widget()
                                    if child:
                                        widgets_a_revisar.append(child)

                        # Iterar sobre el widget(es) para encontrar el texto real
                        for w in widgets_a_revisar:
                            if isinstance(w, QTextEdit):
                                texto_extraido = w.toPlainText()
                                break
                            elif isinstance(w, QLabel):
                                # Lógica para obtener texto plano de HTML de un QLabel
                                from PyQt5.QtGui import QTextDocument
                                doc = QTextDocument()
                                doc.setHtml(w.text())
                                texto_extraido = doc.toPlainText()
                                break
                            elif isinstance(w, QLineEdit):
                                texto_extraido = w.text()
                                break
                    
                    fila_evento.append(texto_extraido)
                            
                eventos.append(fila_evento)

    
            encabezados_eventos = ["Fecha", "Tipo", "Descripción","Realizado por"]  # Agrega encabezado para la persona que modificó el evento
            
            # 3. Datos generales

           # Obtener el código del motor desde el diccionario
            codigo_motor = datos_motor_dict.get("Código de motor", "desconocido").replace(" ", "_")

            nombre_img = datos_motor_dict.get("Imagen motor", None)
            ruta_imagen = None
            if nombre_img:
                
                ruta_imagen = resource_path(os.path.join("Fotos", nombre_img))
                if not os.path.exists(ruta_imagen):
                    ruta_imagen = None  # Si no existe la imagen, se pone None

            # --- Crear carpeta única para el motor ---
            # Carpeta raíz donde van todos los informes
            # 1. Determinar la ruta base de la aplicación
            if getattr(sys, 'frozen', False):
                # Si el programa está empaquetado (PyInstaller), usamos el directorio donde se encuentra el .exe
                CARPETA_GUARDADO_BASE = os.path.dirname(sys.executable)
            else:
                # Si se está ejecutando como un script normal (desarrollo), usamos el directorio del script actual
                CARPETA_GUARDADO_BASE = os.path.dirname(os.path.abspath(__file__))

            # 2. Definir la ruta final de la carpeta de Informes
            # Esta ruta será persistente, y el código ya existente creará la carpeta si no existe.
            carpeta_informes = os.path.join(CARPETA_GUARDADO_BASE, "Informes")
           
            os.makedirs(carpeta_informes, exist_ok=True) # Crear carpeta si no existe

            # Comprobar si la BD ya tiene carpeta registrada
            conn = get_db_connection()
            cursor = conn.cursor()

            nombre_linea = self.parent().nombre_linea  #Se obtiene la línea desde el diálogo padre
            area = self.parent().area
            cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (nombre_linea,))
            id_linea = cursor.fetchone()
            cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (area, id_linea[0]))
            id_area = cursor.fetchone()
            if not id_linea or not id_area:
                QMessageBox.critical(self, "Error", "No se encontró la línea o el área seleccionada.")
                conn.close()
                return

            cursor.execute("SELECT Carpeta FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
            resultado = cursor.fetchone()

            if resultado and resultado[0]:  #si resultado no es None y la carpeta no es cadena vacía
                # Ya tiene carpeta asignada → usarla
                nombre_carpeta = resultado[0]
            else:
                # No tiene carpeta → generar una carpeta única
                nombre_carpeta = self.generar_nombre_carpeta_unico(carpeta_informes, codigo_motor)

                # Guardar carpeta en la BD
                cursor.execute("UPDATE motores SET carpeta = ? WHERE codigo_motor = ? AND id_area = ?", (nombre_carpeta, codigo_motor, id_area[0]))
                conn.commit()

            conn.close()

            # Crear carpeta final
            carpeta_motor = os.path.join(carpeta_informes, nombre_carpeta)
            os.makedirs(carpeta_motor, exist_ok=True)


            # 3. Ruta final del PDF
            base_nombre_pdf = os.path.join(carpeta_motor, f"Informe_motor_{codigo_motor}")

            # Busca el siguiente número disponible
            contador = 1
            nombre_pdf = f"{base_nombre_pdf}.pdf"
            while os.path.exists(nombre_pdf):
                nombre_pdf = f"{base_nombre_pdf}_{contador}.pdf"
                contador += 1

            # 4. Crear diccionario de mantenimiento generales
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id_linea FROM lineas WHERE nombre = ?", (self.parent().nombre_linea,))
            id_linea = cursor.fetchone()
            cursor.execute("SELECT id_area FROM areas WHERE nombre = ? AND id_linea = ?", (self.parent().area, id_linea[0]))
            id_area = cursor.fetchone()
            cursor.execute("SELECT id_motor FROM motores WHERE codigo_motor = ? AND id_area = ?", (codigo_motor, id_area[0]))
            id_motor = cursor.fetchone()

            cursor.execute("""
                SELECT tipo_evento, COUNT(*) as cantidad
                FROM eventos
                WHERE id_motor = ?
                GROUP BY tipo_evento
            """, (id_motor[0],))
           
            eventos_tipo = cursor.fetchall()
            conn.close()
            mantenimiento_dict = {tipo: cantidad for tipo, cantidad in eventos_tipo}

        

            # 5. Generar el informe

            if fecha_1 and fecha_2 and filtrado:
                # Generar el informe
    
                generar_informe_pdf(nombre_pdf, "Informe del Motor: "+ datos_motor_dict.get("Código de motor"), datos_motor_dict, eventos, encabezados_eventos, ruta_imagen, filtrado, fecha_1, fecha_2, mantenimiento_dict)

            else:
                generar_informe_pdf(nombre_pdf, "Informe del Motor: " + datos_motor_dict.get("Código de motor"), datos_motor_dict, eventos, encabezados_eventos, ruta_imagen, filtrado,0,0,mantenimiento_dict)
              
            QMessageBox.information(self, "Éxito", f"Se ha generado el informe:\n{nombre_pdf}")


        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el informe:\n{str(e)}")



#**************************Clase para mostrar imágenes de eventos de termografia en un diálogo separado****************************


class MostrarImagenesDialog(QDialog):
    def __init__(self, parent=None, fecha=""):
        super().__init__(parent)
        self.setWindowTitle("Imágenes termográficas")
        self.setGeometry(100, 50, 1600, 800)
        self.setWindowIcon(QIcon(resource_path(os.path.join("Recursos", "Motor.ico"))))
        
        # Frame contenedor para aplicar estilo
        self.frame_contenedor = QFrame()
        self.frame_contenedor.setObjectName("contenedorLinea1")

        # Layout interno (dentro del frame)
        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.frame_contenedor.setLayout(self.layout)

        # Aplica el layout principal a la ventana
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.frame_contenedor)
        self.setLayout(main_layout)


        # Ajustar el estilo de la clase MostrarImagenesDialog para eliminar el borde del QDialog y mantener el del QFrame
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6fb;
                padding: 0px; /* Mantener margen interno */
                border: none;
            }
            QLabel {
                color: #222;
                font-size: 16px;
            }
            #contenedorLinea1 {
                border: 3px solid #229954;
                border-radius: 14px;
                background-color: #f4f6fb;
                margin: 5px; /* Agregar margen externo */
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 12px;
                padding: 12px 24px;
                margin: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)

        # Título
        titulo_label = QLabel(f"Imágenes de termografía - Fecha: {fecha}")
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setStyleSheet("""
            background-color: #229954;
            color: #fff;
            font-size: 20px;
            font-weight: bold;
            border-radius: 10px;
            padding: 12px;
        """)
        self.layout.addWidget(titulo_label, 0, 0, 1, -1)

    
        self.contenedor_dinamico = QWidget()
        self.layout.addWidget(self.contenedor_dinamico, 1, 0, 1, -1) # Fila 1 para las imágenes

        # Botón para cerrar (estático, Fila 2)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        self.layout.addWidget(btn_cerrar, 2, 0, 1, -1) # Fila 2

    def mostrar_imagen(self, coj_delantero, coj_trasero, estator):
        """
        Método para mostrar las imágenes en un diseño horizontal con etiquetas.
        """
        # Si el contenedor dinámico ya tiene un layout, lo limpiamos
        current_dynamic_layout = self.contenedor_dinamico.layout()
        if current_dynamic_layout:
             while current_dynamic_layout.count():
                item = current_dynamic_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
             # Eliminar el layout anterior del QWidget para poner uno nuevo
             self.contenedor_dinamico.setLayout(None)

        # Crear un layout horizontal para las imágenes
        imagenes_layout = QHBoxLayout(self.contenedor_dinamico) # Establecerlo directamente en el contenedor dinámico

        # Lista de imágenes y etiquetas
        imagenes = [
            (coj_delantero, "Cojinete frontal"),
            (coj_trasero, "Cojinete trasero"),
            (estator, "Estator")
        ]

        for imagen, etiqueta in imagenes:
            if imagen:
                # Crear un QLabel para la imagen
                pixmap = QPixmap(imagen)
                imagen_label = QLabel()
                imagen_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                imagen_label.setAlignment(Qt.AlignCenter)
                imagen_label.setStyleSheet("border: 2px dashed #888; background: #f4f6fb;")

                # Crear un QLabel para la etiqueta
                etiqueta_label = QLabel(etiqueta)
                etiqueta_label.setAlignment(Qt.AlignCenter)
                etiqueta_label.setStyleSheet("color: #222; font-size: 14px; font-weight: bold;")

                # Crear un contenedor vertical para la imagen y su etiqueta
                contenedor = QVBoxLayout()
                contenedor.addWidget(imagen_label)
                contenedor.addWidget(etiqueta_label)

                # Crear un widget para el contenedor y agregarlo al layout horizontal
                widget_contenedor = QFrame()
                widget_contenedor.setLayout(contenedor)
                imagenes_layout.addWidget(widget_contenedor)

   

