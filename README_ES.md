# 🚀 PonLab - Simulador de Redes Ópticas Pasivas

<div align="center">

![PonLab Logo](resources/icons/app_icon_512x512.png)

_Una aplicación de escritorio avanzada para la simulación, diseño y análisis de redes de fibra óptica PON_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![RL](https://img.shields.io/badge/Reinforcement%20Learning-Smart--RL-ff6b6b.svg)](https://github.com/alex-itico/PonLab)
[![SDN](https://img.shields.io/badge/SDN-Controller-4ecdc4.svg)](https://github.com/alex-itico/PonLab)
[![Version](https://img.shields.io/badge/Version-2.1.0-brightgreen.svg)](releases)
[![Languages](https://img.shields.io/badge/Languages-5-blue.svg)](resources/translations)

**🌍 Idiomas Disponibles:** 🇪🇸 Español | 🇺🇸 English | 🇫🇷 Français | 🇧🇷🇵🇹 Português | 🇩🇪 Deutsch

**🎯 Desarrollado por:** Alex Aravena Tapia • Jesús Chaffe González • Eduardo Maldonado Zamora • Jorge Barrios Núñez

</div>

---

## 📑 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características Principales](#-características-principales)
- [Arquitectura de IA y SDN](#-arquitectura-de-ia-y-sdn)
- [Instalación](#-instalación-y-configuración)
- [Guía de Inicio Rápido](#-guía-de-inicio-rápido)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Casos de Uso](#-casos-de-uso-y-aplicaciones)
- [Autores](#-autores)

---

## 📋 Descripción

**PonLab** es una aplicación de escritorio profesional desarrollada en Python que permite simular, diseñar y analizar redes ópticas pasivas (PON - Passive Optical Networks). La herramienta proporciona una interfaz gráfica intuitiva y potente para el diseño de infraestructuras de fibra óptica, con funcionalidades avanzadas de **Inteligencia Artificial (RL)**, **controlador SDN integrado**, visualización en tiempo real y análisis de rendimiento de red con algoritmos de optimización inteligentes.

## ✨ Características Principales

### 🎨 **Interfaz, Temas y Navegación**

- **Canvas Interactivo Avanzado**: Zoom infinito, pan suave, navegación intuitiva con coordenadas en tiempo real
- **Sistema de Coordenadas Profesional**: Cuadrícula configurable con origen visible y medidas precisas
- **Temas Personalizables**: Soporte completo para temas claro/oscuro con integración QSS y configuración persistente
- **Integración de Mapas**: Visualización geográfica para ubicación real de equipos (MapBox)
- **Paneles Adaptativos**: Interfaz redimensionable y configurable con pantalla de carga

### 🔧 **Gestión de Dispositivos y Conexiones**

- **Dispositivos PON Completos**: OLT (Optical Line Terminal) y ONU (Optical Network Unit) con iconos SVG
- **Drag & Drop Intuitivo**: Colocación fluida de dispositivos desde panel lateral al canvas
- **Modo de Conexión Avanzado**: Presiona `L` para conectar dispositivos con cálculo automático de distancias
- **Gestión Visual**: Panel de información en tiempo real con coordenadas, soporte de selección múltiple
- **Validación Inteligente**: Sistema que previene conexiones y configuraciones inválidas

### 🧪 **Sistema de Simulación Inteligente**

- **Simulador PON Integrado**: Motor de simulación avanzado basado en eventos con control de tiempo preciso
- **🤖 Algoritmos DBA**: FCFS, Priority, RL-DBA, SDN, Smart-RL ⭐, Smart-RL-SDN ⭐⭐
- **Escenarios Configurables**: Patrones de tráfico predefinidos con tiempo de simulación personalizable (1-120s)
- **Dashboard en Tiempo Real**: Panel de métricas SDN (Ctrl+D) con monitoreo continuo
- **Análisis de Equidad**: Cálculo automático del índice de Jain y métricas de equidad

### 📊 **Visualización y Análisis**

- **Gráficos Interactivos**: Integración completa con matplotlib con métricas RL en tiempo real
- **Monitoreo de Rendimiento**: Análisis de delay, throughput, ocupación de buffer, utilización de enlaces
- **Auto-Exportación**: Guardado automático de resultados en formatos PNG, PDF, SVG
- **Historial de Simulaciones**: Seguimiento y comparación de múltiples ejecuciones
- **Panel de Log de Eventos**: Sistema de eventos en tiempo real con capacidades de filtrado

### 🌍 **Sistema Multiidioma**

- **5 Idiomas Completos**: Español, Inglés, Francés, Portugués, Alemán
- **660+ Claves de Traducción**: UI completa, diálogos, gráficos matplotlib y mensajes de error
- **Cambio Dinámico**: Cambiar idioma sin reiniciar (Ayuda → Idioma)
- **Configuración Persistente**: Preferencia de idioma guardada automáticamente

### 💾 **Gestión de Proyectos**

- **Formato .pon Nativo**: Sistema de archivos propietario para topologías PON completas
- **Auto-guardado Inteligente**: Respaldo automático en carpeta temporal con detección de cambios
- **Importación/Exportación Completa**: Preservación completa del estado del proyecto con seguimiento de modificaciones

---

## 🤖 Arquitectura de IA y SDN

### **🧠 Sistema Smart-RL (Reinforcement Learning)**

PonLab cuenta con un **agente RL completamente interno** que no requiere dependencias externas:

**Políticas Inteligentes:**
- `prioritize_low_buffer` (0.7) - Prioriza ONUs cerca de saturación de buffer
- `balance_throughput` (0.6) - Balancea distribución de throughput
- `minimize_delay` (0.8) - Optimiza latencia promedio
- `fairness_factor` (0.5) - Garantiza asignación equitativa de recursos

**Mecanismo de Aprendizaje:**
- Tabla-Q interna con espacio de estados discreto
- Observación dinámica de red (niveles de buffer, solicitudes, throughput)
- Mejora adaptativa de políticas con cada ciclo de simulación
- Seguimiento de decisiones en tiempo real y análisis de rendimiento

### **🌐 Controlador SDN (OLT_SDN)**

**Control Centralizado:**
- Gestión unificada con visibilidad del estado global de la red
- Implementación dinámica de políticas y monitoreo continuo
- Métricas en tiempo real: latencia por ONU, throughput agregado, ocupación de buffer, utilización de enlaces, índice de Jain

**Dashboard Interactivo (Ctrl+D):**
- Visualización en vivo de todas las métricas de red
- Cálculos automatizados de equidad
- Seguimiento histórico de rendimiento

### **🚀 Algoritmo Híbrido Smart-RL-SDN**

**Arquitectura Revolucionaria de Dos Capas:**

1. **Capa de Decisión RL**: Smart-RL analiza el estado global y toma decisiones inteligentes de asignación
2. **Capa de Implementación SDN**: OLT_SDN ejecuta decisiones y proporciona retroalimentación de rendimiento
3. **Bucle de Retroalimentación Inteligente**: Optimización continua basada en resultados en tiempo real

**Ventajas:**
- 🎯 Precisión RL + ⚡ Velocidad SDN
- 🔄 Adaptabilidad a cambios en patrones de tráfico
- 📊 Análisis completo de métricas de ambos sistemas
- 🚀 Rendimiento óptimo combinando flexibilidad y control

**Inicio Rápido:**
- Seleccionar algoritmo en panel de simulación (Ctrl+N)
- Configurar políticas en panel RL (Ctrl+T)
- Monitorear en dashboard SDN (Ctrl+D)
- Comparar resultados entre algoritmos

---

## 🛠️ Tecnologías y Arquitectura

**Stack Tecnológico:**
- **Python 3.8+** con PyQt5, PyQtWebEngine, Matplotlib, NumPy
- **IA/ML**: Stable-Baselines3, PyTorch, Gymnasium, Scikit-learn
- **Datos**: Pandas para análisis, JSON para configuración
- **Gráficos**: Iconos SVG vectoriales, temas QSS

**Arquitectura:**
- Diseño modular con separación de responsabilidades (core, ui, utils)
- Simulación basada en eventos con temporización precisa
- Comunicación entre componentes basada en señales
- Renderizado eficiente para miles de dispositivos

---

## 📦 Instalación y Configuración

### **Prerequisitos**

- Python 3.8+ (Recomendado: Python 3.11+)
- Git, gestor de paquetes pip

### **Instalación Rápida**

```bash
# Clonar repositorio
git clone https://github.com/alex-itico/PonLab.git
cd PonLab

# Crear entorno virtual (Recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/MacOS

# Instalar dependencias y ejecutar
pip install -r requirements.txt
python main.py
```

### **Alternativa con Conda**

```bash
conda create -n ponlab python=3.11
conda activate ponlab
conda install -c conda-forge pyqt
git clone https://github.com/alex-itico/PonLab.git
cd PonLab
python main.py
```

---

## 🎮 Guía de Inicio Rápido

### **⚡ Inicio Rápido en 5 Pasos**

1. **Ejecutar**: `python main.py`
2. **Agregar Dispositivos**: Arrastrar OLT/ONU desde panel lateral
3. **Conectar**: Presionar `L`, seleccionar dos dispositivos
4. **Navegar**: `C` (centrar), `R` (resetear), rueda (zoom)
5. **Guardar**: `Ctrl+S`

### **⌨️ Atajos Esenciales**

| Atajo    | Función               | Descripción                          |
| -------- | --------------------- | ------------------------------------ |
| `L`      | Modo Conexión         | Activar/desactivar modo conexión     |
| `C` / `R`| Centrar / Resetear    | Controles de navegación              |
| `Ctrl+N` | Panel Simulación      | Abrir controles de simulación        |
| `Ctrl+D` | Dashboard SDN         | Métricas SDN en tiempo real ⭐       |
| `Ctrl+T` | Panel RL              | Configuración RL ⭐                  |
| `Ctrl+S` | Guardar               | Guardar proyecto actual              |
| `Ctrl+G` | Toggle Cuadrícula     | Mostrar/ocultar cuadrícula           |
| `Delete` | Eliminar              | Quitar elementos seleccionados       |

### **🖱️ Controles del Mouse**

- **Clic Izquierdo**: Seleccionar dispositivos/elementos
- **Clic Derecho**: Menú contextual
- **Medio + Arrastrar**: Mover vista (pan)
- **Rueda**: Zoom in/out
- **Arrastrar y Soltar**: Mover dispositivos

### **🔧 Flujos de Trabajo Comunes**

**Configuración de Simulación:**
1. Configurar topología PON (OLT + ONUs)
2. Abrir panel de simulación (Ctrl+N)
3. Seleccionar algoritmo (Smart-RL-SDN recomendado)
4. Establecer duración y ejecutar
5. Ver resultados en ventana emergente

**Monitoreo RL/SDN:**
1. Iniciar simulación con algoritmo Smart-RL o SDN
2. Abrir dashboard SDN (Ctrl+D) para métricas en vivo
3. Configurar políticas en panel RL (Ctrl+T)
4. Comparar rendimiento de algoritmos

**Cambio de Idioma:**
- Ayuda → Idioma → Seleccionar idioma preferido
- La interfaz se actualiza inmediatamente

---

## 📁 Estructura del Proyecto

```
PonLab/
├── 📄 main.py                    # Punto de entrada principal
├── 📄 requirements.txt           # Dependencias del proyecto
├── 📄 README.md / README_ES.md   # Documentación
│
├── 📁 core/                      # Lógica de negocio
│   ├── 📁 devices/              # Gestión de dispositivos (OLT, ONU)
│   ├── 📁 connections/          # Sistema de conexiones
│   ├── 📁 pon/                  # Componentes específicos PON
│   ├── 📁 algorithms/           # DBA y programación
│   ├── 📁 simulation/           # Motores de simulación
│   ├── 📁 events/               # Sistema basado en eventos
│   ├── 📁 data/                 # Estructuras de datos
│   └── 📁 utilities/            # Funciones auxiliares
│
├── 📁 ui/                        # Componentes de interfaz
│   ├── 📄 main_window.py        # Ventana principal
│   ├── 📄 canvas.py             # Canvas de dibujo
│   ├── 📄 netponpy_sidebar.py   # Panel de simulación
│   ├── 📄 graphics_popup_window.py # Visualización de resultados
│   └── 📄 splash_screen.py      # Pantalla de carga
│
├── 📁 utils/                     # Utilidades
│   ├── 📄 config_manager.py     # Configuración
│   ├── 📄 constants.py          # Constantes de aplicación
│   └── 📄 resource_manager.py   # Manejo de recursos
│
└── 📁 resources/                 # Recursos
    ├── 📁 devices/              # Iconos SVG de dispositivos
    ├── 📁 icons/                # Iconos de aplicación
    ├── 📁 styles/               # Temas QSS (claro/oscuro)
    └── 📁 translations/         # Archivos JSON de idiomas (5 idiomas)
```

---

## 📚 Casos de Uso y Aplicaciones

### **🎓 Investigación Académica**
- Simulación de algoritmos DBA personalizados y análisis comparativo
- Investigación en Reinforcement Learning para redes ópticas
- Desarrollo de nuevas políticas de asignación de ancho de banda

### **🏢 Desarrollo Industrial**
- Prototipado de redes PON antes del despliegue
- Optimización de configuraciones de red existentes
- Análisis de capacidad y planificación de crecimiento

### **📖 Educación y Formación**
- Demostración de conceptos de redes PON
- Enseñanza práctica de algoritmos DBA
- Talleres de IA/SDN aplicados a redes

---

## 🚀 Características Técnicas

### **Rendimiento**
- Renderizado eficiente de canvas para miles de dispositivos
- Gestión automática de memoria y recolección de basura
- Carga progresiva de recursos para inicio rápido

### **Robustez**
- Manejo exhaustivo de errores y validación
- Auto-recuperación desde archivos temporales
- Sistema automático de respaldo de proyectos

### **Extensibilidad**
- Arquitectura modular para fácil adición de características
- API interna con sistema de eventos/señales
- Diseño preparado para plugins

---

## 📄 Licencia

Propósitos académicos y de investigación. Contactar a los autores para información sobre licencias.

---

## 👥 Autores

- **Alex Aravena Tapia** - Desarrollador Principal
- **Jesús Chaffe González** - Algoritmos Centrales
- **Eduardo Maldonado Zamora** - Diseño UI/UX
- **Jorge Barrios Núñez** - Arquitectura de Red

**Repositorio**: [github.com/alex-itico/PonLab](https://github.com/alex-itico/PonLab)

---

## 📝 Historial de Versiones

### **v2.1.0** (Actual)
✨ Soporte multiidioma completo (5 idiomas: ES, EN, FR, PT, DE)
📊 660+ claves de traducción cubriendo toda la aplicación
🎨 Gráficos matplotlib y componentes UI traducidos
📖 README en inglés para visibilidad internacional

### **v2.0.0**
🤖 Implementación del sistema Smart-RL
🌐 Integración del controlador SDN
🚀 Algoritmo híbrido Smart-RL-SDN
📊 Dashboard avanzado de métricas con índice de equidad de Jain

### **v1.0.0**
🎨 Interfaz gráfica inicial
🔧 Gestión básica de dispositivos y conexiones
🧪 Integración de simulación PON

---

<div align="center">

**Hecho con ❤️ para la comunidad de redes PON e IA**

_PonLab - Conectando el futuro de las redes ópticas con tecnología inteligente_

</div>
