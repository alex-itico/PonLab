# PonLab - Simulador de Redes Ópticas Pasivas

<div align="center">

![PonLab Logo](resources/icons/app_icon_128x128.png)

*Una aplicación de escritorio para la simulación y visualización de redes de fibra óptica PON*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
</div>

## 📋 Descripción

**PonLab** es una aplicación de escritorio desarrollada en Python que permite simular y visualizar redes ópticas pasivas (PON - Passive Optical Networks). La herramienta proporciona una interfaz gráfica intuitiva para el diseño, análisis y gestión de infraestructuras de fibra óptica.

## ✨ Características Principales

- 🎨 **Interfaz Gráfica Intuitiva**: Canvas interactivo con soporte para zoom y navegación
- 🌐 **Visualización de Mapas**: Integración con mapas para ubicación geográfica de equipos
- 🔧 **Gestión de Dispositivos**: Soporte para OLT (Optical Line Terminal) y ONU (Optical Network Unit)
- 📐 **Sistema de Cuadrícula**: Cuadrícula ajustable para precisión en el diseño
- 🎯 **Panel de Información**: Visualización de coordenadas y datos en tiempo real
- 🌙 **Temas Personalizables**: Soporte para temas claro y oscuro
- ⌨️ **Atajos de Teclado**: Navegación rápida y eficiente

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**: Lenguaje principal
- **PyQt5**: Framework de interfaz gráfica
- **PyQtWebEngine**: Motor web para mapas interactivos

## 📦 Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/alex-itico/PonLab.git
   cd PonLab
   ```

2. **Crear un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En Linux/macOS
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

## 🎮 Uso

### Navegación Básica

- **Pan**: Mantén presionado el botón central del mouse y arrastra
- **Zoom**: Usa la rueda del mouse para acercar/alejar
- **Centrar vista**: Presiona `C` para centrar en el origen
- **Resetear vista**: Presiona `R` para restaurar la vista por defecto

### Atajos de Teclado

| Atajo | Función |
|-------|---------|
| `C` | Centrar vista en el origen (0, 0) |
| `R` | Resetear vista (centrar y restaurar zoom) |
| `Ctrl+I` | Mostrar/Ocultar panel de información |
| `Ctrl+G` | Mostrar/Ocultar cuadrícula |

### Menú Contextual

Haz clic derecho en el canvas para acceder a:
- Opciones de navegación
- Configuración de cuadrícula
- Controles de zoom
- Información de coordenadas

Para más detalles sobre atajos y funcionalidades, consulta [SHORTCUTS.md](SHORTCUTS.md).

## 📁 Estructura del Proyecto

```
PonLab/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias del proyecto
├── SHORTCUTS.md           # Guía de atajos de teclado
├── core/                  # Módulos principales
├── resources/             # Recursos gráficos
│   ├── devices/          # Iconos de dispositivos (OLT, ONU)
│   ├── icons/            # Iconos de la aplicación
│   ├── images/           # Imágenes adicionales
│   └── styles/           # Archivos de estilo (temas)
├── ui/                   # Componentes de interfaz
│   ├── canvas.py         # Canvas principal de dibujo
│   ├── main_window.py    # Ventana principal
│   ├── map_view.py       # Vista de mapas
│   ├── sidebar_panel.py  # Panel lateral
│   └── splash_screen.py  # Pantalla de carga
└── utils/                # Utilidades y helpers
    ├── config_manager.py # Gestor de configuración
    ├── constants.py      # Constantes de la aplicación
    ├── helpers.py        # Funciones auxiliares
    ├── resource_manager.py # Gestor de recursos
    └── validators.py     # Validadores
```
