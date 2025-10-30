"""
Translation Manager
Sistema de gestión de traducciones multilenguaje para PonLab
"""

import json
import os
from typing import Dict, Any, Optional


class TranslationManager:
    """Gestor de traducciones para la aplicación"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern para asegurar una sola instancia"""
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializar el gestor de traducciones"""
        if self._initialized:
            return
            
        self.translations_dir = os.path.join("resources", "translations")
        self.current_language = "es_ES"  # Idioma por defecto
        self.translations = {}
        self.available_languages = {}
        
        # Crear directorio de traducciones si no existe
        self._ensure_translations_directory()
        
        # Cargar idiomas disponibles
        self._load_available_languages()
        
        # Cargar idioma por defecto
        self.load_language(self.current_language)
        
        self._initialized = True
    
    def _ensure_translations_directory(self):
        """Asegurar que existe el directorio de traducciones"""
        if not os.path.exists(self.translations_dir):
            os.makedirs(self.translations_dir)
            print(f"📁 Directorio de traducciones creado: {self.translations_dir}")
    
    def _load_available_languages(self):
        """Cargar información de idiomas disponibles"""
        self.available_languages = {
            "es_ES": {
                "name": "Español",
                "native_name": "Español",
                "flag": "🇪🇸",
                "file": "es_ES.json"
            },
            "en_US": {
                "name": "English",
                "native_name": "English",
                "flag": "🇺🇸",
                "file": "en_US.json"
            }
        }
    
    def load_language(self, language_code: str) -> bool:
        """
        Cargar un idioma específico
        
        Args:
            language_code: Código del idioma (ej: 'es_ES', 'en_US')
            
        Returns:
            bool: True si se cargó correctamente, False en caso contrario
        """
        if language_code not in self.available_languages:
            print(f"⚠️ Idioma no disponible: {language_code}")
            return False
        
        language_file = os.path.join(
            self.translations_dir, 
            self.available_languages[language_code]["file"]
        )
        
        try:
            if not os.path.exists(language_file):
                print(f"⚠️ Archivo de traducción no encontrado: {language_file}")
                # Si no existe el archivo, usar traducciones vacías
                self.translations = {}
                return False
            
            with open(language_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            self.current_language = language_code
            print(f"✅ Idioma cargado: {self.available_languages[language_code]['native_name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando idioma {language_code}: {e}")
            self.translations = {}
            return False
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Obtener texto traducido usando una clave
        
        Args:
            key: Clave de traducción en formato 'section.subsection.key'
            **kwargs: Parámetros para formatear el texto
            
        Returns:
            str: Texto traducido o la clave si no se encuentra
        """
        # Dividir la clave por puntos para navegación jerárquica
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            # Si hay parámetros, formatear el texto
            if kwargs:
                return value.format(**kwargs)
            
            return value
            
        except (KeyError, TypeError):
            # Si no se encuentra la traducción, devolver la clave
            print(f"⚠️ Traducción no encontrada: {key}")
            return key
    
    def get_current_language(self) -> str:
        """Obtener el código del idioma actual"""
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, Dict[str, str]]:
        """Obtener diccionario de idiomas disponibles"""
        return self.available_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Obtener nombre nativo del idioma"""
        if language_code in self.available_languages:
            return self.available_languages[language_code]['native_name']
        return language_code
    
    def get_language_flag(self, language_code: str) -> str:
        """Obtener emoji de bandera del idioma"""
        if language_code in self.available_languages:
            return self.available_languages[language_code]['flag']
        return "🌐"


# Instancia global del gestor de traducciones
translation_manager = TranslationManager()


def tr(key: str, **kwargs) -> str:
    """
    Función helper para obtener traducciones
    
    Args:
        key: Clave de traducción
        **kwargs: Parámetros para formatear
        
    Returns:
        str: Texto traducido
    """
    return translation_manager.get_text(key, **kwargs)
