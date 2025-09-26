# 🚀 PonLab - Simulador de Redes Ópticas Pasivas

<div align="center">

![PonLab Logo](resources/icons/app_icon_1080_1080.png)

_Una aplicación de escritorio avanzada para la simulación, diseño y análisis de redes de fibra óptica PON_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![Version](https://img.shields.io/badge/Version-2.0.0-brightgreen.svg)](releases)

**🎯 Desarrollado por:** Alex Aravena Tapia • Jesús Chaffe González • Eduardo Maldonado Zamora • Jorge Barrios Núñez

</div>

---

## 📋 Descripción

**PonLab** es una aplicación de escritorio profesional desarrollada en Python que permite simular, diseñar y analizar redes ópticas pasivas (PON - Passive Optical Networks). La herramienta proporciona una interfaz gráfica intuitiva y potente para el diseño de infraestructuras de fibra óptica, con funcionalidades avanzadas de visualización, gestión de dispositivos, análisis de topologías y simulación en tiempo real con gráficos interactivos.

## ✨ Características Principales

### 🎨 **Interfaz y Visualización**

- **Canvas Interactivo Avanzado**: Área de trabajo con zoom infinito, pan suave y navegación intuitiva
- **Sistema de Coordenadas Profesional**: Cuadrícula configurable con origen visible y medidas precisas
- **Visualización de Mapas**: Integración con mapas geográficos para ubicación real de equipos
- **Temas Personalizables**: Soporte completo para temas claro y oscuro con estilos profesionales
- **Pantalla de Carga**: Splash screen con progreso de inicialización
- **Interfaz Adaptativa**: Paneles redimensionables y configurables

### 🔧 **Gestión de Dispositivos**

- **Dispositivos PON Completos**: Soporte para OLT (Optical Line Terminal) y ONU (Optical Network Unit)
- **Drag & Drop Intuitivo**: Arrastra dispositivos desde el panel lateral al canvas
- **Gestión Visual**: Iconos SVG profesionales y representación gráfica detallada
- **Información en Tiempo Real**: Panel de información con coordenadas y datos de dispositivos
- **Selección y Manipulación**: Selección múltiple, movimiento y configuración de dispositivos
- **Propiedades Configurables**: Configuración detallada de cada dispositivo

### 🔗 **Sistema de Conexiones**

- **Modo Conexión Avanzado**: Activación con tecla `L` para conectar dispositivos
- **Conexiones Visuales**: Líneas de fibra óptica con etiquetas de distancia automáticas
- **Gestión Inteligente**: Creación, eliminación y modificación de conexiones
- **Cálculo de Distancias**: Medición automática de distancias entre dispositivos
- **Validación de Conexiones**: Sistema que previene conexiones inválidas

### 🧪 **Sistema de Simulación NetPONPy**

- **Simulador PON Integrado**: Motor de simulación avanzado para redes PON
- **Algoritmos DBA**: Soporte para múltiples algoritmos de asignación dinámica de ancho de banda (FCFS, Round-Robin, Weighted, Priority-Based)
- **Escenarios Predefinidos**: Configuración automática para diferentes escenarios de tráfico
- **Simulación en Tiempo Real**: Ejecución de simulaciones con tiempo configurable (1-120 segundos)
- **Arquitectura Híbrida**: Sistema de simulación event-driven con control temporal preciso
- **Métricas Avanzadas**: Análisis de delay, throughput, utilización, pérdida de paquetes

### 📊 **Visualización y Análisis**

- **Gráficos Interactivos**: Sistema completo de visualización con matplotlib
- **Métricas en Tiempo Real**: Monitoreo de rendimiento durante la simulación
- **Ventana de Resultados**: Popup automático con gráficos al finalizar simulación
- **Exportación de Gráficos**: Guardado automático en formatos PNG, PDF, SVG
- **Análisis de Performance**: Gráficos de delay, throughput, buffer occupancy
- **Historial de Simulaciones**: Seguimiento y comparación de resultados
- **Panel de Log**: Sistema de eventos en tiempo real con filtros

### 💾 **Gestión de Proyectos**

- **Formato .pon Nativo**: Sistema de archivos propio para topologías PON
- **Auto-guardado Inteligente**: Guardado automático en carpeta temporal
- **Carga y Guardado**: Importación y exportación completa de proyectos
- **Historial de Cambios**: Seguimiento de modificaciones y estados del proyecto
- **Detección de Cambios**: Notificación de trabajo sin guardar
- **Exportación de Resultados**: Guardado de métricas y gráficos de simulación

### ⌨️ **Controles y Navegación**

- **Atajos de Teclado Completos**: Más de 15 atajos para navegación rápida
- **Controles de Mouse**: Pan con botón central, zoom con rueda, selección con clic
- **Navegación Inteligente**: Centrado automático, reseteo de vista y enfoque en dispositivos
- **Panel Simulación**: Acceso rápido con Ctrl+N al sistema de simulación

## 🛠️ Tecnologías y Arquitectura

### **Stack Tecnológico**

- **Python 3.8+**: Lenguaje principal con soporte moderno
- **PyQt5**: Framework de interfaz gráfica profesional
- **PyQtWebEngine**: Motor web para mapas interactivos (opcional)
- **Matplotlib**: Biblioteca para gráficos científicos y visualización
- **NumPy**: Computación numérica para análisis de datos
- **JSON**: Formato de almacenamiento de configuraciones
- **SVG**: Gráficos vectoriales para iconos de dispositivos

### **Arquitectura del Sistema**

```
📦 PonLab Architecture
├── 🚀 Application Layer (main.py)
├── 🎨 UI Layer (ui/)
│   ├── MainWindow (Ventana principal)
│   ├── Canvas (Área de trabajo)
│   ├── SidebarPanel (Panel de dispositivos)
│   ├── NetPONPySidebar (Panel de simulación)
│   ├── IntegratedPONTestPanel (Simulador integrado)
│   ├── PONMetricsChartsPanel (Visualización gráficos)
│   ├── PONResultsPanel (Panel de resultados)
│   └── GraphicsPopupWindow (Ventana emergente)
├── ⚙️ Core Logic (core/)
│   ├── 📱 devices/ (Gestión de dispositivos)
│   │   ├── DeviceManager (Gestor principal)
│   │   ├── DeviceGraphicsItem (Representación gráfica)
│   │   └── DeviceTypes (Creación de dispositivos)
│   ├── 🔗 connections/ (Gestión de conexiones)
│   │   ├── ConnectionManager (Gestor de conexiones)
│   │   ├── ConnectionPoints (Puntos de conexión)
│   │   └── PONConnection (Conexiones PON)
│   ├── 🌐 pon/ (Componentes PON específicos)
│   │   ├── PONAdapter (Interfaz principal)
│   │   ├── PON_OLT (Terminal óptico)
│   │   └── PON_ONU (Unidad de red óptica)
│   ├── 🧮 algorithms/ (Algoritmos DBA y scheduling)
│   │   ├── UpstreamScheduler (Planificador upstream)
│   │   ├── PON_DBA (Algoritmos de asignación)
│   │   └── DBA_Cycle (Gestión de ciclos)
│   ├── 🎯 simulation/ (Motores de simulación)
│   │   ├── SimulationManager (Gestor principal)
│   │   ├── PONOrchestrator (Orquestador)
│   │   └── EventSimulator (Simulador de eventos)
│   ├── ⚡ events/ (Sistema de eventos discretos)
│   │   ├── EventQueue (Cola de eventos)
│   │   ├── PONEvent (Eventos PON)
│   │   └── HybridOLT/ONU (Componentes híbridos)
│   ├── 📊 data/ (Estructuras de datos)
│   │   ├── PONQueue (Colas PON)
│   │   ├── PONRequest (Peticiones)
│   │   └── TrafficGeneration (Generación de tráfico)
│   └── 🛠️ utilities/ (Funciones de utilidad)
│       ├── PONTraffic (Escenarios de tráfico)
│       ├── PONRandom (Generadores aleatorios)
│       └── Helpers (Funciones auxiliares)
└── 🛠️ Utils Layer (utils/)
    ├── ConfigManager (Configuraciones)
    ├── ResourceManager (Recursos)
    └── Constants (Constantes y configuración)
```

## 📦 Instalación y Configuración

### **Prerrequisitos**

- Python 3.8+ (Recomendado: Python 3.11+)
- Git para clonar el repositorio
- pip (gestor de paquetes de Python)

### **Instalación Rápida**

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/alex-itico/PonLab.git
   cd PonLab
   ```

2. **Crear entorno virtual (Recomendado):**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

### **Instalación con Conda (Alternativa)**

```bash
# Crear entorno conda
conda create -n ponlab python=3.11
conda activate ponlab

# Instalar PyQt5
conda install -c conda-forge pyqt

# Clonar y ejecutar
git clone https://github.com/alex-itico/PonLab.git
cd PonLab
python main.py
```

## 🎮 Manual de Usuario

### **🚀 Inicio Rápido**

1. **Ejecuta la aplicación** con `python main.py`
2. **Arrastra dispositivos** desde el panel lateral al canvas
3. **Conecta dispositivos** presionando `L` y seleccionando dos dispositivos
4. **Navega** usando `C` (centrar), `R` (resetear), mouse wheel (zoom)
5. **Guarda tu proyecto** con `Ctrl+S`

### **⌨️ Atajos de Teclado Completos**

| Atajo    | Función               | Descripción                                         |
| -------- | --------------------- | --------------------------------------------------- |
| `L`      | **Modo Conexión**     | Activa/desactiva el modo para conectar dispositivos |
| `C`      | **Centrar Vista**     | Centra la vista en el origen (0, 0)                 |
| `R`      | **Resetear Vista**    | Restaura zoom y centra la vista                     |
| `Escape` | **Cancelar**          | Cancela operaciones en curso                        |
| `Ctrl+P` | **Panel Componentes** | Muestra/oculta el panel de dispositivos             |
| `Ctrl+G` | **Cuadrícula**        | Muestra/oculta la cuadrícula y origen               |
| `Ctrl+I` | **Panel Info**        | Muestra/oculta el panel de información              |
| `Ctrl+N` | **Panel Simulación**  | Muestra/oculta el panel de simulación               |
| `Ctrl+S` | **Guardar**           | Guarda el proyecto actual                           |
| `Ctrl+O` | **Abrir**             | Abre un proyecto existente                          |
| `Delete` | **Eliminar**          | Elimina dispositivos/conexiones seleccionados       |

### **🖱️ Controles de Mouse**

| Acción                   | Función                                   |
| ------------------------ | ----------------------------------------- |
| **Clic Izquierdo**       | Seleccionar dispositivos/elementos        |
| **Clic Derecho**         | Menú contextual con opciones              |
| **Botón Central + Drag** | Pan (mover vista)                         |
| **Rueda del Mouse**      | Zoom in/out                               |
| **Drag & Drop**          | Mover dispositivos, arrastrar desde panel |

### **🔧 Funcionalidades Avanzadas**

#### **Sistema de Simulación NetPONPy**

- **Simulación Integrada**: Panel de simulación PON con controles completos
- **Configuración Temporal**: Control de duración de simulación personalizable
- **Ejecución Automática**: Sistema de simulación con parámetros optimizados
- **Resultados en Tiempo Real**: Visualización inmediata de resultados

#### **Visualización de Métricas PON**

- **Gráficos Interactivos**: Gráficos matplotlib integrados en la interfaz
- **Métricas en Tiempo Real**: Monitoreo continuo de parámetros de red
- **Ventana Emergente**: Visualización ampliada de gráficos y resultados
- **Análisis Detallado**: Métricas de rendimiento y estadísticas avanzadas

#### **Gestión de Dispositivos**

- **Agregar Dispositivos**: Arrastra OLT/ONU desde el panel lateral
- **Mover Dispositivos**: Selecciona y arrastra dispositivos en el canvas
- **Información Detallada**: Panel de información muestra coordenadas y datos
- **Selección Múltiple**: Mantén Ctrl para seleccionar múltiples dispositivos

#### **Sistema de Conexiones**

- **Crear Conexiones**: Presiona `L`, luego selecciona dos dispositivos
- **Etiquetas de Distancia**: Las conexiones muestran distancia automáticamente
- **Validación**: El sistema previene conexiones inválidas
- **Gestión Visual**: Conexiones con colores y estilos diferenciados

#### **Navegación y Vista**

- **Zoom Infinito**: Acércate tanto como necesites sin límites
- **Navegación Suave**: Pan fluido con inercia natural
- **Centrado Inteligente**: `C` centra en origen, `R` resetea completamente
- **Coordenadas en Tiempo Real**: Ve las coordenadas del mouse en tiempo real

#### **Sistema de Temas**

- **Temas Intercambiables**: Soporte completo para temas claro y oscuro
- **Integración QSS**: Todos los componentes respetan el tema seleccionado
- **Persistencia**: El tema seleccionado se mantiene entre sesiones
- **Compatibilidad Universal**: Todos los paneles y ventanas soportan temas

## 📁 Estructura del Proyecto Detallada

```
PonLab/
├── 📄 main.py                    # 🚀 Punto de entrada principal
├── 📄 requirements.txt           # 📦 Dependencias del proyecto
├── 📄 SHORTCUTS.md              # ⌨️ Guía completa de atajos
├── 📄 README.md                 # 📖 Documentación principal
├── 📄 .gitignore               # 🚫 Archivos ignorados por Git
│
├── 📁 core/                     # ⚙️ Lógica principal del negocio (REORGANIZADO)
│   ├── 📄 __init__.py
│   ├── � devices/             # 📱 Gestión de dispositivos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 device.py        # 🔧 Clase base de dispositivos
│   │   ├── 📄 device_manager.py # 📱 Gestor de dispositivos
│   │   └── 📄 device_types.py  # 🏭 Factory de dispositivos
│   ├── � connections/         # 🔗 Sistema de conexiones
│   │   ├── 📄 __init__.py
│   │   ├── 📄 connection.py    # 🔗 Clase de conexión base
│   │   ├── 📄 connection_manager.py # 🔗 Gestor de conexiones
│   │   ├── 📄 connection_points.py # 📍 Puntos de conexión
│   │   ├── 📄 pon_connection.py # 🌐 Conexiones PON específicas
│   │   └── 📄 pon_link.py      # 🔌 Enlaces PON
│   ├── 📁 pon/                 # 🌐 Componentes PON específicos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pon_adapter.py   # 🔄 Adaptador principal PON
│   │   ├── 📄 pon_olt.py       # 🔴 Terminal de línea óptica
│   │   ├── 📄 pon_onu.py       # 🔵 Unidad de red óptica
│   │   └── 📄 pon_types.py     # 📋 Tipos y constantes PON
│   ├── 📁 algorithms/          # 🧮 Algoritmos DBA y scheduling
│   │   ├── 📄 __init__.py
│   │   ├── 📄 upstream_scheduler.py # ⬆️ Planificador upstream
│   │   ├── 📄 pon_dba.py       # 🎯 Algoritmos DBA principales
│   │   └── 📄 pon_dba_cycle.py # 🔄 Gestión de ciclos DBA
│   ├── 📁 simulation/          # 🎯 Motores de simulación
│   │   ├── 📄 __init__.py
│   │   ├── 📄 simulation_manager.py # 🎮 Gestor principal
│   │   ├── 📄 pon_orchestrator.py # 🎼 Orquestador PON
│   │   ├── 📄 pon_simulator.py    # 🔬 Simulador principal
│   │   ├── � pon_event_simulator.py # ⚡ Simulador de eventos
│   │   ├── 📄 pon_cycle_simulator.py # 🔄 Simulador por ciclos
│   │   └── 📄 pon_netsim.py       # 🌐 Simulador de red
│   ├── �📁 events/              # ⚡ Sistema de eventos discretos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 event_queue.py   # 📋 Cola de eventos
│   │   ├── 📄 pon_event.py     # ⚡ Eventos PON base
│   │   ├── 📄 pon_event_olt.py # 🔴 Eventos OLT híbridos
│   │   └── 📄 pon_event_onu.py # 🔵 Eventos ONU híbridos
│   ├── 📁 data/                # 📊 Estructuras de datos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pon_queue.py     # 📋 Colas PON
│   │   ├── 📄 pon_request.py   # 📤 Peticiones PON
│   │   └── 📄 project_manager.py # 📁 Gestor de proyectos
│   └── 📁 utilities/           # 🛠️ Funciones de utilidad
│       ├── 📄 __init__.py
│       ├── 📄 pon_traffic.py   # 🚦 Generación de tráfico
│       ├── 📄 pon_random.py    # 🎲 Variables aleatorias
│       └── 📄 helpers.py       # 🔧 Funciones auxiliares
│
├── 📁 ui/                       # 🎨 Componentes de interfaz
│   ├── 📄 __init__.py
│   ├── 📄 main_window.py       # 🏢 Ventana principal
│   ├── 📄 canvas.py            # 🎨 Canvas principal de dibujo
│   ├── 📄 sidebar_panel.py     # 📋 Panel lateral de dispositivos
│   ├── 📄 netponpy_sidebar.py  # 🧪 Panel de simulación NetPONPy
│   ├── 📄 integrated_pon_test_panel.py # 🔬 Panel simulador integrado
│   ├── 📄 pon_simulation_results_panel.py # 📊 Panel de resultados
│   ├── 📄 graphics_popup_window.py # 🖼️ Ventana emergente gráficos
│   ├── 📄 log_panel.py         # 📋 Panel de log de eventos
│   ├── 📄 map_view.py          # 🗺️ Vista de mapas (MapBox)
│   ├── 📄 map_overlay_toggle.py # 🔘 Botón toggle para mapas
│   └── 📄 splash_screen.py     # 🎬 Pantalla de carga
│
├── 📁 utils/                    # 🛠️ Utilidades y helpers
│   ├── 📄 __init__.py
│   ├── 📄 config_manager.py    # ⚙️ Gestor de configuración
│   ├── 📄 constants.py         # 📊 Constantes de la aplicación
│   ├── 📄 helpers.py           # 🔧 Funciones auxiliares
│   ├── 📄 resource_manager.py  # 📦 Gestor de recursos
│   └── 📄 validators.py        # ✅ Validadores
│
├── 📁 resources/               # 🎨 Recursos gráficos y assets
│   ├── 📁 devices/            # 📱 Iconos de dispositivos
│   │   ├── 🔴 olt_icon.svg    # Icono OLT (Terminal Óptico)
│   │   └── 🔵 onu_icon.svg    # Icono ONU (Unidad Red Óptica)
│   ├── 📁 icons/              # 🖼️ Iconos de la aplicación
│   │   ├── 📄 app_icon.ico    # Icono principal Windows
│   │   ├── 📄 app_icon.png    # Icono PNG
│   │   ├── 📄 app_icon.svg    # Icono vectorial
│   │   ├── 📄 app_icon_16x16.png
│   │   ├── 📄 app_icon_32x32.png
│   │   ├── 📄 app_icon_64x64.png
│   │   └── 📄 app_icon_128x128.png
│   ├── 📁 images/             # 🖼️ Imágenes adicionales
│   └── 📁 styles/             # 🎨 Archivos de estilo CSS
│       ├── 📄 dark_theme.qss  # Tema oscuro
│       └── 📄 light_theme.qss # Tema claro
│
└── 📁 temp/                    # 🗂️ Archivos temporales (auto-generado)
    └── 📄 autosave_*.pon      # 💾 Auto-guardado de proyectos
```

## 🚀 Características Técnicas Avanzadas

### **🎯 Rendimiento y Optimización**

- **Renderizado Eficiente**: Canvas optimizado para miles de dispositivos
- **Gestión de Memoria**: Limpieza automática de recursos y garbage collection
- **Carga Diferida**: Carga progresiva de recursos para inicio rápido
- **Auto-guardado Inteligente**: Guardado automático sin interrupciones

### **🔒 Robustez y Confiabilidad**

- **Manejo de Errores**: Sistema robusto de captura y manejo de excepciones
- **Validación de Datos**: Validación completa de entradas y formatos
- **Recuperación de Fallos**: Auto-recuperación de archivos temporales
- **Backup Automático**: Sistema de respaldo automático de proyectos

### **🎨 Personalización y Extensibilidad**

- **Sistema de Temas**: Temas completamente personalizables (claro/oscuro)
- **Configuración Persistente**: Todas las preferencias se guardan automáticamente
- **Arquitectura Modular**: Fácil extensión y adición de nuevas funcionalidades
- **API Interna**: Sistema de events y signals para comunicación entre componentes
