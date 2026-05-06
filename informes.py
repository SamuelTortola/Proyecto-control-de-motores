from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,  ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line

import os  # Para verificar la existencia de la imagen
 #os sirve para interactuar con el sistema operativo
import datetime

import matplotlib.pyplot as plt
from io import BytesIO

from collections import Counter
from matplotlib.patches import Rectangle

from database_utils import get_db_connection, resource_path

import re  # Para expresiones regulares, re especializado en operaciones con cadenas de texto

import statistics as stats # Para cálculos estadísticos como media, mediana, desviación estándar
import numpy as np  # Para cálculos numéricos avanzados

import sys


# Constantes para el manejo de la página
MARGIN = 25          # Espacio de margen desde el borde de la página (en puntos)
LINE_THICKNESS = 2   # Grosor de la línea del marco
LOGO_WIDTH = 210     # Ancho del logo en el PDF (ajustable)
LOGO_HEIGHT = 60     # Alto del logo en el PDF (ajustable)



RUTA_LOGO = resource_path(os.path.join( "Recursos", "Logo.png"))
# Si el logo está en la misma carpeta: RUTA_LOGO = os.path.join(RUTA_BASE, LOGO_FILENAME)

tipo_evento_display = ""  # Variable global para almacenar el tipo de evento actual


tendencia_frontal = ""
tendencia_trasero = ""
tendencia_estator = ""


def generar_informe_pdf(nombre_archivo, titulo, datos_motor_dict, eventos, encabezados_eventos, ruta_imagen=None, filtrado=0, fecha_inicio=None, fecha_fin=None, mantenimiento_dict=None):
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    estilos = getSampleStyleSheet()  # Obtiene estilos predefinidos
     # Lista para almacenar los elementos del PDF
    elementos = []
    global tipo_evento_display

   
    # Crea un estilo centrado basado en Heading3
    estilo_centrado = ParagraphStyle(
        name="Heading3Center",
        parent=estilos["Heading2"],
        alignment=TA_CENTER
    )
    

    # Título
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph(titulo, estilos["Title"]))
    elementos.append(Spacer(1, 10))

    estilo_fecha_centrada = ParagraphStyle(
    name="FechaCentrada",
    parent=estilos["Normal"],
    alignment=TA_CENTER,
    spaceAfter=6
        )

    
    # Fecha y hora actual en formato español
    fecha_hora = datetime.datetime.now().strftime("Informe generado el %d-%m-%Y a las %H:%M:%S")
    elementos.append(Paragraph(fecha_hora, estilo_fecha_centrada)) # Fecha en la parte superior
    elementos.append(Spacer(1, 30))

    # Subtítulo
    elementos.append(Paragraph("Datos del Motor",estilo_centrado))
    elementos.append(Spacer(1, 10))


    # Tabla de datos del motor
    datos_motor = [[k, v] for k, v in datos_motor_dict.items()]
    tabla_motor = Table(datos_motor, colWidths=[195, 320])
    tabla_motor.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))
    elementos.append(tabla_motor)
    

    def obtener_ruta_imagen_motor(nombre_imagen):
        if not nombre_imagen:
            return None

        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base, "Fotos", nombre_imagen)
    
    # Obtener la ruta completa de la imagen del motor
    ruta_imagen = obtener_ruta_imagen_motor(datos_motor_dict.get("Imagen motor"))
    
     # Agrega la imagen si existe
    if ruta_imagen and os.path.exists(ruta_imagen):
        elementos.append(Spacer(1, 10))  # Espacio arriba de la imagen
        elementos.append(Paragraph("Imagen del motor",estilo_centrado))  # Título para la imagen
        elementos.append(Spacer(1, 8)) # Espacio entre el título y la imagen
        # Redimensiona la imagen si es muy grande
        img_reader = ImageReader(ruta_imagen)
        orig_width, orig_height = img_reader.getSize()
        max_width = 400
        # Calcula el alto proporcional
        ratio = max_width / orig_width # Relación de aspecto
        new_height = int(orig_height * ratio) # Nuevo alto proporcional
        img = Image(ruta_imagen, width=max_width, height=new_height) # Ajusta el tamaño de la imagen
      
       

        # Inserta la imagen dentro de una celda de tabla
        tabla = Table([[img]], colWidths=[515])
        tabla.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 2, "#229954"),     # Borde verde
            ("ALIGN", (0,0), (-1,-1), "CENTER"),       # Centrar contenido
            ("LEFTPADDING", (0,0), (-1,-1), 20),       # Espacio a la izquierda
            ("RIGHTPADDING", (0,0), (-1,-1), 20),      # Espacio a la derecha
            ("TOPPADDING", (0,0), (-1,-1), 1),        # Espacio arriba
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),     # Espacio abajo
        ]))
        elementos.append(tabla)
        elementos.append(Spacer(1, 20)) # Espacio debajo de la imagen



    tipos = ["Mantenimiento correctivo", "Mantenimiento preventivo",
         "Mantenimiento predictivo", "Inspección Termográfica"]
    

        # Lista para la tabla: encabezado
    datos_tabla = [["Tipo de evento", "Cantidad"]]

    # Variable para total
    total_eventos = 0

    for tipo in tipos:
        cantidad = mantenimiento_dict.get(tipo, 0)  # Si no existe, devuelve 0
        datos_tabla.append([tipo, cantidad])
        total_eventos += cantidad

    # Añadimos fila de total
    datos_tabla.append(["Total", total_eventos])

    
    elementos.append(Paragraph("Resumen eventos de mantenimiento",estilo_centrado))
    elementos.append(Spacer(1, 10))

    tabla_eventos = Table(datos_tabla, colWidths=[415, 100])
    tabla_eventos.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#229954")), # Encabezado
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke), # filas normales
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e0e0e0")) # fila total
    ]))

    elementos.append(tabla_eventos)
   


    if filtrado:
        # (Esto asume que la lista 'eventos' no está vacía)
        tipo_evento_display = eventos[0][1] if eventos and len(eventos[0]) > 1 else "Tipo Desconocido"
        
        # Inicializa el título base
        titulo_eventos = f"Eventos filtrados de {tipo_evento_display}"
        
        # Solo añade el rango de fecha si las variables de fecha son válidas (no 0, no None, no "")
        if fecha_inicio and fecha_fin and fecha_inicio != 0 and fecha_fin != 0:
             # Si se pasaron fechas válidas (cadenas "dd-MM-yyyy"), agrégalas
             titulo_eventos += f" del: {fecha_inicio} al {fecha_fin}"
             
        # Si las fechas son 0 (caso "Otro") o "", solo se muestra el título base.
        elementos.append(PageBreak())
        elementos.append(Paragraph(titulo_eventos, estilo_centrado))
        
    else:
        if ruta_imagen and os.path.exists(ruta_imagen):
            elementos.append(PageBreak())
        else:
            elementos.append(Spacer(1, 20))

        elementos.append(Paragraph("Eventos registrados",estilo_centrado))
    elementos.append(Spacer(1, 10))

    # Tabla de eventos
    datos_eventos = [encabezados_eventos] 

    if eventos:
        for fila in eventos:
            
            #  Convierte explícitamente todos los elementos de la fila a STRING
            # Esto previene el error 'can only concatenate str (not "int") to str'
            fila_mod = [str(item) for item in fila] 
            
            #  Aplica Paragraph solo al índice de la descripción (columna 2)
            # Esto permite el ajuste de texto en la celda
            if len(fila_mod) > 2:
            
                fila_mod[2] = Paragraph(fila_mod[2], estilos["Normal"]) 
                
            # Añade la fila modificada una sola vez
            datos_eventos.append(fila_mod)

        # Ajusta el ancho de las columnas (ejemplo: 80, 80, 220, 80)
        tabla_eventos = Table(datos_eventos, colWidths=[65, 130, 220, 100])
        tabla_eventos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#229954")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Alinea arriba el texto
        ]))
        elementos.append(tabla_eventos)
        elementos.append(Spacer(1, 20))

    else:
        elementos.append(Paragraph("No se encontraron eventos.", estilos["Normal"]))
        elementos.append(Spacer(1, 20))
    elementos.append(Spacer(1, 20))


    def generar_grafica_mem():

        # Extraer solo las fechas
        fechas = [fila[0] for fila in eventos]

        # Contar cuántas veces aparece cada fecha
        conteo_fechas = Counter(fechas)
         #  ejemplo de resultado esperado: {'16-09-2025': 3, '18-09-2025': 1}

        if len(conteo_fechas) <= 1:
            return None # Devuelve None si no se debe generar gráfica

       # Separar claves y valores
        x = list(conteo_fechas.keys())   # Fechas
        y = list(conteo_fechas.values()) # Cantidad de eventos

        # Crear figura
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(x, y, color="#21BCFF", edgecolor="black", linewidth=2)
        ax.set_title("Eventos por Fecha")
        ax.set_ylabel("Cantidad de eventos por fecha")
        ax.set_xlabel("Fechas"+ " del: " + fecha_inicio + " al " + fecha_fin)
        ax.grid(axis="y", linestyle="--", alpha=0.7) # Líneas de la cuadrícula solo en y, con transparencia, alpha es la transparencia

        # Rotar las etiquetas del eje x si son muchas fechas
        plt.xticks(rotation=45, ha="right")

        # Ajustar márgenes antes de dibujar
        plt.tight_layout()

        # Añadir un rectángulo en coordenadas de figura (0,0) a (1,1)
        rect = Rectangle((0,0), 1, 1, fill=False, color="#229954", linewidth=2, # borde verde 
        transform=fig.transFigure, figure=fig)
        fig.patches.append(rect)


        # Guardar en memoria (BytesIO en vez de archivo)
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight") 
        plt.close(fig)
        buffer.seek(0)  # Regresar al inicio del buffer
        return buffer
    

    if (filtrado == 1  and len(eventos) > 1):  # Solo si hay eventos para graficar
        # Generar gráfica en memoria
        grafica_buffer = generar_grafica_mem()
        if grafica_buffer:
            # Insertar en el PDF sin guardarla en disco
            img = Image(grafica_buffer, width=530, height=305)  # Se inserta directo
            # Mantener el título y la gráfica juntos: si no hay espacio suficiente, van a la siguiente página
            grupo_grafica = KeepTogether([
                Spacer(1, 10),
                Paragraph("Gráfica eventos filtrados", estilo_centrado),
                Spacer(1, 5),
                img,
                
            ])
            elementos.append(grupo_grafica)


    if tipo_evento_display == "Inspección Termográfica" and len(eventos) == 1:
        elementos.append(Spacer(1, 50))
        elementos.append(Paragraph("Imágenes termográficas asociadas", estilo_centrado))
        elementos.append(Spacer(1, 40))

        

        codigo_motor = datos_motor_dict.get("Código de motor", "Desconocido")
        area_trabajo = datos_motor_dict.get("Área", "Desconocido")
        linea = datos_motor_dict.get("Línea", "Desconocido")
        fecha = eventos[0][0]  # Asumiendo que la fecha está en la primera columna


        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute("""
            SELECT e.id_termografia, e.id_motor
            FROM eventos e
            JOIN motores m ON e.id_motor = m.id_motor
            JOIN areas a ON m.id_area = a.id_area
            JOIN lineas l ON a.id_linea = l.id_linea
            WHERE 
                m.codigo_motor = ?
                AND a.nombre = ?
                AND l.nombre = ?
                AND e.fecha = ?
                AND e.tipo_evento = 'Inspección Termográfica'
        """, (codigo_motor, area_trabajo, linea, fecha))

        fila = cursor.fetchone()

        id_termo, id_motor = fila



        # Ahora consultar imágenes
        cursor.execute("""
            SELECT coj_delantero, coj_trasero, Estator
            FROM Termografia
            WHERE id_motor = ? AND id_termo = ?
        """, (id_motor, id_termo))

        resultado = cursor.fetchone()


        cursor.close()
        conn.close()

        if resultado:
    
            nombres_columnas = ["Cojinete frontal","Cojinete trasero", "Estator"]
            
            # Estilo para el título de la imagen dentro del marco
            estilo_titulo_imagen = ParagraphStyle(
                name='ImageTitle', 
                parent=estilos["Heading4"], 
                alignment=TA_CENTER
            )
            
            # Definición del estilo del marco verde
            estilo_marco_verde = TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                # Aplicar el borde verde (ancho 2, color #229954)
                ('GRID', (0, 0), (-1, -1), 2, colors.HexColor("#229954")), 
            ])

            for idx, ruta_imagen in enumerate(resultado):
                nombre_etiqueta = nombres_columnas[idx]
                
                # 1. Crear el contenido a enmarcar (título + imagen)
                contenido_a_enmarcar = []
                
                # Título/Etiqueta
                contenido_a_enmarcar.append(Paragraph(nombre_etiqueta, estilo_titulo_imagen))
                contenido_a_enmarcar.append(Spacer(1, 10))


                if ruta_imagen and os.path.exists(ruta_imagen):
                    # Usamos un tamaño más pequeño para que la tabla quepa en el ancho del PDF
                    img = Image(ruta_imagen, width=300, height=300) 
                    contenido_a_enmarcar.append(img)
                else:
                    contenido_a_enmarcar.append(Paragraph("Imagen no disponible", estilos["Normal"]))
                    
                contenido_a_enmarcar.append(Spacer(1, 10))


                # 2. Agrupar el contenido para que el marco no se rompa entre páginas
                tabla_marco = Table([[contenido_a_enmarcar]], colWidths=[410])


                tabla_marco.setStyle(estilo_marco_verde)
                
                # 4. Añadir la tabla enmarcada a los elementos del PDF
                elementos.append(tabla_marco)
                elementos.append(Spacer(1, 50)) # Espacio entre cada imagen de termografía
            
        else:
            elementos.append(Paragraph("No se encontraron imágenes termográficas para este evento y motor.", estilos["Normal"]))
            elementos.append(Spacer(1, 15))


    def extraer_temperaturas(eventos):
        fechas = []
        frontal = []
        trasero = []
        estator = []

        for fila in eventos:
            fecha = fila[0]
            texto = fila[2]  # Descripción donde vienen las temperaturas

            # Regex para capturar números antes de °C
            f = re.search(r"Cojinete frontal:\s*(\d+)", texto) # Busca "Cojinete frontal: " seguido de números
            e = re.search(r"Estator:\s*(\d+)", texto)
            t = re.search(r"Cojinete trasero:\s*(\d+)", texto)

            if f and e and t:
                fechas.append(fecha)
                frontal.append(int(f.group(1)))
                estator.append(int(e.group(1)))
                trasero.append(int(t.group(1)))

        
        return fechas, frontal, trasero, estator
    

    def grafica_tendencia(labels, fechas, series, titulo, ylabel="Temperatura (°C)"):
        """
        labels: lista de nombres de las series (ej: ["Frontal"])
        fechas: lista de fechas (eje X)
        series: lista de listas. Cada una es una serie de temperaturas.
        titulo: título de la gráfica
        """

        fig, ax = plt.subplots(figsize=(6, 4))

        # Dibujar series
        for label, datos in zip(labels, series):
            ax.plot(fechas, datos, marker="o", linewidth=2, label=label)

        ax.set_title(titulo)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Fecha")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45, ha="right")

        # Borde verde alrededor de la figura
        rect = Rectangle((0, 0), 1, 1, fill=False, color="#229954",
                        linewidth=3, transform=fig.transFigure)
        fig.patches.append(rect)

        plt.tight_layout()

        # Guardar en buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=110)
        plt.close(fig)
        buffer.seek(0)

        return buffer
    


    def interpretar_tendencia(nombre, valores):
        global tendencia_frontal, tendencia_trasero, tendencia_estator
        """
        Recibe un arreglo de temperaturas y devuelve interpretación real.
        """

        if len(valores) < 2:
            return f"• {nombre}: Datos insuficientes para analizar tendencia."

        arr = np.array(valores) # Convertir a array de numpy para cálculos

        # ------ Análisis matemático ------

        # 1. REGRESIÓN LINEAL PARA TENDENCIA
        x = np.arange(len(arr))
        slope, intercept = np.polyfit(x, arr, 1)

        # 2. DESVIACIÓN ESTÁNDAR (volatilidad térmica)
        desv = np.std(arr)

        # 3. PROMEDIO Y ÚLTIMO VALOR
        prom = np.mean(arr)
        ultimo = arr[-1] # Último valor registrado, se hace -1 porque es índice

        # 4. RANGO (picos)
        maxi = np.max(arr)
        mini = np.min(arr)
        rango = maxi - mini

        # ------ Interpretación de tendencia ------
        if slope > 0.5:
            tendencia = "ascendente"

            # Guardar la tendencia global
            if nombre == "Cojinete frontal":
                tendencia_frontal = "Ascendente"
            elif nombre == "Cojinete trasero":
                tendencia_trasero = "Ascendente"
            elif nombre == "Estator":
                tendencia_estator = "Ascendente"  
            
        elif slope > 0.1:
            tendencia = "levemente ascendente"

            # Guardar la tendencia global
            if nombre == "Cojinete frontal":
                tendencia_frontal = "Ascendente"
            elif nombre == "Cojinete trasero":
                tendencia_trasero = "Ascendente"
            elif nombre == "Estator":
                tendencia_estator = "Ascendente"  

        elif slope < -0.5:
            tendencia = "descendente"

            # Guardar la tendencia global
            if nombre == "Cojinete frontal":
                tendencia_frontal = "Descendente"
            elif nombre == "Cojinete trasero":
                tendencia_trasero = "Descendente"
            elif nombre == "Estator":
                tendencia_estator = "Descendente"  
        elif slope < -0.1:
            tendencia = "levemente descendente"

            # Guardar la tendencia global
            if nombre == "Cojinete frontal":
                tendencia_frontal = "Descendente"
            elif nombre == "Cojinete trasero":
                tendencia_trasero = "Descendente"
            elif nombre == "Estator":
                tendencia_estator = "Descendente"  

        else:
            tendencia = "estable"

            # Guardar la tendencia global
            if nombre == "Cojinete frontal":
                tendencia_frontal = "Estable"
            elif nombre == "Cojinete trasero":
                tendencia_trasero = "Estable"
            elif nombre == "Estator":
                tendencia_estator = "Estable" 

        # ------ Interpretación de variación ------
        if desv < 1.0:
            variacion = "muy estable"

        elif desv < 2.5:
            variacion = "estable"
        else:
            variacion = "variable"

        # ------ Picos anómalos ------
        if rango > 8:
            pico = "Se detectan picos significativos."
        elif rango > 4:
            pico = "Variaciones moderadas presentes."
        else:
            pico = "Sin variaciones relevantes."

        # ------ Riesgo térmico según desviación porcentual respecto a la media ------
        if prom != 0:
            desviacion_pct = ((ultimo - prom) / prom) * 100 # Desviación porcentual, ejemplo: 12.5%
            desviacion_pct =abs(desviacion_pct)  # Solo valor absoluto
        else:
            desviacion_pct = 0

        

        # Clasificación de riesgo
        if desviacion_pct > 25.0:
            riesgo = "CRÍTICO — muy por encima del comportamiento normal."
        elif desviacion_pct > 15.0:
            riesgo = " ALTO — incremento térmico significativo."
        elif desviacion_pct > 5.0:
            riesgo = "MEDIO — incremento moderado, requiere seguimiento."
        else:
            riesgo = "BAJO — dentro del rango normal."


        # ------ Construcción final ------
        texto = (
            f"<b>• {nombre}:</b><br/>"
            f"Tendencia: <i>{tendencia}</i>, comportamiento: <i>{variacion}</i>.<br/>"
            f"{pico}<br/>"
            f"Riesgo: <b>{riesgo}</b> ( +{desviacion_pct:.1f}% sobre la media ).<br/>"
            f"Temperaturas — mín: <b>{mini}°C</b>, máx: <b>{maxi}°C</b>, "
            f"promedio: <b>{prom:.2f}°C</b>, última registrada: <b>{ultimo}°C</b>."
        )


        return texto
    

    def calcular_estadisticas(fechas, frontal, trasero, estator):

        global tendencia_frontal, tendencia_trasero, tendencia_estator
        datos = {
            "Cojinete frontal": frontal,
            "Cojinete trasero": trasero,
            "Estator": estator
        }

        tabla = []

        for nombre, valores in datos.items():
            if not valores:
                continue
            
            minimo = min(valores)
            maximo = max(valores)
            promedio = round(stats.mean(valores), 2)
            try:
                desviacion = round(stats.stdev(valores), 2) if len(valores) > 1 else 0
            except:
                desviacion = 0
            
            rango = maximo - minimo
            ultimo = valores[-1]

            # Tendencia
            if nombre == "Cojinete frontal":
                tendencia = tendencia_frontal
            elif nombre == "Cojinete trasero":
                tendencia = tendencia_trasero
            elif nombre == "Estator":
                tendencia = tendencia_estator

            tabla.append([
                nombre,
                f"{minimo}°C",
                f"{maximo}°C",
                f"{promedio}°C",
                f"{desviacion}°C",
                f"{rango}°C",
                f"{ultimo}°C",
                tendencia
            ])

        return tabla
    

    def tabla_estadistica_pdf(estilos, estilo_centrado, stats_table):

        encabezados_estadisticos = [
            "Componente",
            "Mín",
            "Máx",
            "Promedio",
            "Desv. Est.",
            "Rango",
            "Último",
            "Tendencia"
        ]

        datos = [encabezados_estadisticos] + stats_table

        tabla = Table(datos, colWidths=[120, 45, 45, 65, 65, 65, 45, 75])
        
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#229954")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE")
        ]))

        return tabla

    

    def grafica_gauss(valores, titulo):
        fig, ax = plt.subplots(figsize=(4, 2.5))

        # Histograma
        ax.hist(valores, bins=6, density=True, alpha=0.5, edgecolor="black")

        # --- Curva de Gauss ---
        mu = np.mean(valores)
        sigma = np.std(valores)

        # Generar puntos para la curva suave
        x = np.linspace(min(valores), max(valores), 200)
        y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(- (x - mu)**2 / (2 * sigma**2))

        ax.plot(x, y, linewidth=2)

        # Títulos
        ax.set_title(titulo)
        ax.set_xlabel("°C")
        ax.set_ylabel("Densidad")

        # Borde verde
        rect = Rectangle((0,0), 1, 1, fill=False, color="#229954", linewidth=3,
                        transform=fig.transFigure)
        fig.patches.append(rect)

        # A guardar
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=120)
        plt.close(fig)
        buffer.seek(0)
        return buffer


    if tipo_evento_display == "Inspección Termográfica" and len(eventos) > 1 and filtrado:
        elementos.append(PageBreak())  # Nueva página para las gráficas
        elementos.append(Paragraph("Gráficas de tendencias", estilo_centrado))
        

        fechas, frontal, trasero, estator = extraer_temperaturas(eventos)
        

        """"
        print("Fechas extraídas:", fechas)
        print("Cojinete frontal:", frontal)
        print("Cojinete trasero:", trasero)
        print("Estator:", estator)
        """


        graf_frontal  = grafica_tendencia(["Cojinete frontal"], fechas, [frontal],
                                   "Tendencia — Cojinete frontal")

        graf_trasero  = grafica_tendencia(["Cojinete trasero"], fechas, [trasero],
                                        "Tendencia — Cojinete trasero")

        graf_estator  = grafica_tendencia(["Estator"], fechas, [estator],
                                        "Tendencia — Estator")
        

        graf_combinada = grafica_tendencia(
            ["Frontal", "Trasero", "Estator"],
            fechas,
            [frontal, trasero, estator],
            "Tendencias Termográficas — Comparación"
          )

        

        for titulo, graf in [
            ("Tendencia — Cojinete frontal", graf_frontal),
            ("Tendencia — Cojinete trasero", graf_trasero),
            ("Tendencia — Estator", graf_estator),
            ("Comparación de temperaturas", graf_combinada),
        ]:
            img = Image(graf, width=510, height=310)

            grupo = KeepTogether([
                Spacer(1, 5),
                Paragraph(titulo, estilo_centrado),
                Spacer(1, 5),
                img,
                
                
            ])

            elementos.append(grupo)
            
             # ---- Interpretación AUTOMÁTICA debajo de cada gráfica ----

            estilo_interpretacion = ParagraphStyle(
                name="Interpretacion",
                parent=estilos["Normal"],
                alignment=TA_JUSTIFY,
                leading=14,
                spaceAfter=12
            )


            if "frontal" in titulo.lower():
                texto = interpretar_tendencia("Cojinete frontal", frontal)
                GAUSS = grafica_gauss(frontal, "Distribución Cojinete frontal")
                img_gauss = Image(GAUSS, width=250, height=160)
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto, estilo_interpretacion))
                elementos.append(Spacer(1, 5))
                elementos.append(img_gauss)
                

            elif "trasero" in titulo.lower():
                texto = interpretar_tendencia("Cojinete trasero", trasero)
                GAUSS = grafica_gauss(trasero, "Distribución Cojinete trasero")
                img_gauss = Image(GAUSS, width=250, height=160)
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto, estilo_interpretacion))

                elementos.append(Spacer(1,5))
                elementos.append(img_gauss)
               

            elif "estator" in titulo.lower():
                texto = interpretar_tendencia("Estator", estator)
                GAUSS = grafica_gauss(estator, "Distribución Estator")
                img_gauss = Image(GAUSS, width=250, height=160)
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(texto, estilo_interpretacion))


                elementos.append(Spacer(1, 5))
                elementos.append(img_gauss)
              


        
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(" Resumen análisis estadístico de temperaturas", estilo_centrado))
        elementos.append(Spacer(1, 10))
        stats_table = calcular_estadisticas(fechas, frontal, trasero, estator)
        elementos.append(tabla_estadistica_pdf(estilos, estilo_centrado, stats_table))
        


        explicacion = ListFlowable(
            [
                ListItem(Paragraph("<b>Mín:</b> Temperatura más baja registrada.", estilos["Normal"])),
                ListItem(Paragraph("<b>Máx:</b> Temperatura más alta registrada.", estilos["Normal"])),
                ListItem(Paragraph("<b>Promedio:</b> Valor medio del componente.", estilos["Normal"])),
                ListItem(Paragraph("<b>Desv. Est:</b> Qué tan estables han sido las temperaturas.", estilos["Normal"])),
                ListItem(Paragraph("<b>Tendencia:</b> Indica si la temperatura va subiendo, bajando o estable.", estilos["Normal"])),
            ],
            bulletType='bullet',
            bulletColor=colors.HexColor("#229954"),
            leftIndent=25,
        )

        elementos.append(Spacer(1, 10))
        elementos.append(explicacion)
        elementos.append(Spacer(1, 2))
    
    
    elementos.append(Spacer(1, 10))

    firma_texto = """
    <br/><br/><br/>
    ______________________________________<br/>
    Revisado por
    """

    estilo_firma = ParagraphStyle(
        name="Firma",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        leading=14
    )

    elementos.append(Paragraph(firma_texto, estilo_firma))


    



    def manejar_pagina(canvas, doc):
        canvas.saveState()
        ancho, alto = letter 
        
        # 1. DIBUJAR MARGEN VERDE (Todas las páginas)

        # Define el radio de las esquinas 
        RADIO_ESQUINA = 10
        # Se usa el color #229954
        canvas.setStrokeColor(colors.HexColor("#229954")) 
        canvas.setLineWidth(LINE_THICKNESS)
        
        # Dibuja el rectángulo: (X_inicio, Y_inicio, Ancho, Alto)
        canvas.roundRect(
            MARGIN, 
            MARGIN, 
            ancho - 2 * MARGIN, 
            alto - 2 * MARGIN,
            RADIO_ESQUINA 
        )

        # 2. DIBUJAR LOGO (Solo Primera Página)
        if canvas.getPageNumber() == 1:
            # Posición: superior derecha, ajustado al margen.
            # Se añade un pequeño buffer (5) para separarlo del marco
            x_pos = MARGIN + 10  
            y_pos = alto - MARGIN - LOGO_HEIGHT - 10
            
            if os.path.exists(RUTA_LOGO):
                canvas.drawImage(RUTA_LOGO, x_pos, y_pos, width=LOGO_WIDTH, height=LOGO_HEIGHT, mask='auto')
            # Opcional: Si el logo no existe, se puede dibujar un texto de advertencia
            # else:
            #     canvas.setFont("Helvetica-Bold", 10)
            #     canvas.drawString(x_pos, y_pos + LOGO_HEIGHT/2, "LOGO AQUÍ")


        # 3. NÚMERO DE PÁGINA (Todas las páginas)
        canvas.setFont("Helvetica", 9)
        numero = canvas.getPageNumber()
        texto = f"Página {numero}"
        # Se dibuja justo debajo del margen inferior (MARGIN / 2)
        canvas.drawCentredString(ancho/2.0, MARGIN / 2, texto) 

        canvas.restoreState()

    doc.build(elementos, onFirstPage=manejar_pagina, onLaterPages=manejar_pagina)  #Genera el PDF
