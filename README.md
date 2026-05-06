# 🚀 Proyecto Control de Motores

Aplicación de escritorio con arquitectura **Frontend + Backend** para la gestión integral de motores industriales, incluyendo:

* Registro de motores
* Gestión de mantenimientos y eventos
* Almacenamiento de imágenes (motor y termografía)
* Generación de informes en PDF

---

## 📌 Descripción

Este sistema permite organizar y controlar información de motores dentro de diferentes **líneas** y **áreas/máquinas**, facilitando el seguimiento de:

* Datos técnicos del motor
* Historial de mantenimientos
* Inspecciones termográficas
* Evidencia visual (imágenes)

El objetivo principal es centralizar toda la información en una sola herramienta para mejorar la trazabilidad y gestión del mantenimiento.

📄 Basado en el flujo descrito en el manual de uso 

---

## 🧩 Tecnologías utilizadas

* **Python 3**
* **PyQt5** → Interfaz gráfica (Frontend)
* **SQLite** → Base de datos local
* **ReportLab** → Generación de PDFs
* **Matplotlib** → Gráficas en informes
* **NumPy / Statistics** → Cálculos y análisis

---

## 🏗️ Arquitectura del proyecto

El proyecto está dividido en módulos principales:

### 🔹 Backend

* `database_utils.py`

  * Manejo de base de datos SQLite
  * Inicialización automática de la BD
  * Gestión de rutas del sistema 

* `informes.py`

  * Generación de informes PDF
  * Inclusión de tablas, imágenes y gráficas
  * Análisis de eventos 

---

### 🔹 Frontend

* `main.py`

  * Punto de entrada del sistema
  * Navegación principal

* `motores.py`

  * Gestión de motores
  * Visualización de datos
  * Manejo de eventos e imágenes
  * Generación de informes

---

## ⚙️ Funcionalidades principales

### 🏭 Gestión estructurada

* Crear, modificar y eliminar:

  * Líneas
  * Áreas / máquinas
  * Motores

---

### ⚡ Gestión de motores

* Registro completo de datos técnicos
* Asociación a línea y área
* Búsqueda rápida por código
* Edición de información

---

### 🛠️ Gestión de eventos

* Registro de:

  * Mantenimiento correctivo
  * Mantenimiento preventivo
  * Mantenimiento predictivo
  * Inspección termográfica

* Filtrado por tipo y fechas

* Historial completo por motor

---

### 🖼️ Manejo de imágenes

* Imagen del motor
* Imágenes termográficas:

  * Cojinete delantero
  * Cojinete trasero
  * Estator

Las imágenes se almacenan localmente en carpetas del proyecto.

---

### 📊 Generación de informes

* Exportación en PDF con:

  * Datos del motor
  * Imagen del motor
  * Tabla de eventos
  * Resumen de mantenimientos
  * Gráficas de eventos por fecha

---

## 📁 Estructura del proyecto

```
Proyecto-control-de-motores/
│
├── main.py
├── motores.py
├── database_utils.py
├── informes.py
│
├── data/
│   └── Data_base.db
│
├── Fotos/
├── Recursos/
│   ├── Logo.png
│   └── Data_base.db
│
└── README.md
```

---

## ▶️ Ejecución del proyecto

1. Clonar el repositorio:

```bash
git clone https://github.com/SamuelTortola/Proyecto-control-de-motores.git
cd Proyecto-control-de-motores
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:

```bash
python main.py
```

---

## 🧠 Consideraciones importantes

* Cada motor debe tener un **código único**
* Al eliminar:

  * Líneas, áreas o motores → se eliminan **todos sus datos asociados**
  * Incluye imágenes y eventos
* La base de datos se inicializa automáticamente si no existe

---

## 📌 Estado del proyecto

🚧 Finalizado

Funcionalidades implementadas:

* CRUD completo de motores, líneas y áreas
* Gestión de eventos
* Generación de informes
* Interfaz gráfica funcional

Pendiente (posibles mejoras):

* Autenticación de usuarios
* Backup automático
* Versión web
* Dashboard con métricas

---

## 👨‍💻 Autor

Desarrollado por: *Samuel *

---

## 📄 Licencia

Este proyecto se encuentra bajo la licencia MIT.

---
