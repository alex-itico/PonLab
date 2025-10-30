# Sistema de Traducciones de PonLab

## 📁 Estructura de Archivos

```
resources/
  translations/
    es_ES.json    # Español (por defecto)
    en_US.json    # Inglés
    
utils/
  translation_manager.py  # Gestor de traducciones
  config_manager.py       # Configuración (incluye idioma)
```

## 🚀 Uso del Sistema

### 1. Importar el sistema de traducción

```python
from utils.translation_manager import translation_manager, tr
```

### 2. Obtener texto traducido

```python
# Método simple
texto = tr('menu.file.open')

# Con parámetros
mensaje = tr('messages.system.language_changed', language='Español')
```

### 3. Estructura de claves

Las traducciones usan una estructura jerárquica con puntos:

```
menu.file.open           → "Abrir archivo..." / "Open file..."
menu.view.components     → "Mostrar/Ocultar Componentes" / "Show/Hide Components"
messages.simulation.started → "🚀 Simulación iniciada" / "🚀 Simulation started"
```

## 📝 Formato de Archivos JSON

```json
{
  "seccion": {
    "subseccion": {
      "clave": "Texto traducido"
    }
  },
  "mensajes": {
    "con_parametros": "El idioma es {language}"
  }
}
```

## 🌍 Idiomas Disponibles

| Código | Idioma | Bandera | Estado |
|--------|--------|---------|--------|
| es_ES  | Español | 🇪🇸 | ✅ Completo |
| en_US  | English | 🇺🇸 | ✅ Completo |

## 🔧 Gestión de Idioma

### Cambiar idioma programáticamente

```python
translation_manager.load_language('en_US')
```

### Obtener idioma actual

```python
current = translation_manager.get_current_language()  # 'es_ES'
```

### Obtener idiomas disponibles

```python
languages = translation_manager.get_available_languages()
# {'es_ES': {...}, 'en_US': {...}}
```

## 🎯 Implementación en Componentes UI

### Patrón recomendado

```python
class MiPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Configurar UI con textos traducidos
        self.button = QPushButton(tr('simulation.start'))
        self.label = QLabel(tr('simulation.title'))
    
    def retranslate_ui(self):
        """Actualizar textos cuando cambia el idioma"""
        self.button.setText(tr('simulation.start'))
        self.label.setText(tr('simulation.title'))
```

## 📋 Secciones Traducidas (Fase 1)

- ✅ Menú Archivo (File)
- ✅ Menú Ver (View)
- ✅ Menú Opciones (Options)
- ✅ Menú Idioma (Language)
- ✅ Panel de Simulación (básico)
- ✅ Panel de Log
- ✅ Mensajes del Sistema
- ✅ Algoritmos DBA
- ✅ Diálogos comunes

## 🔄 Agregar Nuevo Idioma

1. Crear archivo en `resources/translations/`:
   - `pt_BR.json` (Portugués)
   - `fr_FR.json` (Francés)
   - etc.

2. Agregar configuración en `translation_manager.py`:
```python
self.available_languages = {
    ...
    "pt_BR": {
        "name": "Portuguese",
        "native_name": "Português",
        "flag": "🇧🇷",
        "file": "pt_BR.json"
    }
}
```

3. Agregar opción en menú de `main_window.py`:
```python
portuguese_action = QAction('🇧🇷 &Português', self)
portuguese_action.triggered.connect(lambda: self.change_language('pt_BR'))
```

## 🐛 Debugging

### Ver traducciones cargadas
```python
print(translation_manager.translations)
```

### Verificar clave específica
```python
texto = translation_manager.get_text('menu.file.open')
print(texto)  # "Abrir archivo..." o "Open file..."
```

### Si una clave no se encuentra
- Se devuelve la clave misma: `'menu.file.open'`
- Se imprime advertencia: `⚠️ Traducción no encontrada: menu.file.open`

## ⚙️ Configuración Persistente

El idioma seleccionado se guarda automáticamente en `QSettings`:
- Organización: "SimuladorWDM"
- Aplicación: "Simulador de Redes Opticas"
- Clave: "language"

Se restaura automáticamente al iniciar la aplicación.
