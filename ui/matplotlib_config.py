"""
Configuración de matplotlib para resolver errores de fuentes en Windows
"""

import os
import sys

def configure_matplotlib_for_windows():
    """Configurar matplotlib para evitar errores de fuentes en Windows"""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        
        # Configurar backend antes de importar pyplot
        matplotlib.use('Qt5Agg')
        
        # Configuración básica y segura para Windows
        safe_rcparams = {
            # Fuentes seguras
            'font.family': 'sans-serif',
            'font.size': 10,
            
            # Evitar problemas de encoding
            'axes.unicode_minus': False,
            
            # Configuración de figura
            'figure.facecolor': 'white',
            'figure.dpi': 100,
            
            # Configuración de guardado
            'savefig.facecolor': 'white',
            'savefig.dpi': 300,
            'savefig.format': 'png',
            
            # Configuración de ejes
            'axes.facecolor': 'white',
            'axes.edgecolor': 'black',
            'axes.linewidth': 0.8,
            
            # Grid
            'grid.color': 'gray',
            'grid.linewidth': 0.5,
            
            # Líneas
            'lines.linewidth': 2.0,
        }
        
        # Aplicar solo los parámetros válidos
        for key, value in safe_rcparams.items():
            try:
                plt.rcParams[key] = value
            except KeyError:
                print(f"WARNING parametro {key} no valido, saltando")
        
        # Configuración específica para evitar problemas de rendering
        if sys.platform.startswith('win'):
            # En Windows, forzar uso de fuentes del sistema
            try:
                from matplotlib import font_manager
                # Limpiar caché de fuentes si existe
                font_cache_path = font_manager.get_cachedir()
                if os.path.exists(font_cache_path):
                    import shutil
                    cache_files = [f for f in os.listdir(font_cache_path) if f.endswith('.cache')]
                    for cache_file in cache_files[:2]:  # Solo limpiar algunos archivos
                        try:
                            os.remove(os.path.join(font_cache_path, cache_file))
                        except:
                            pass
            except Exception as e:
                print(f"WARNING limpiando cache de fuentes: {e}")
        
        print("OK Matplotlib configurado para Windows")
        return True
        
    except Exception as e:
        print(f"ERROR configurando matplotlib: {e}")
        return False

def safe_matplotlib_backend():
    """Configurar un backend de matplotlib seguro"""
    try:
        import matplotlib
        
        # Probar diferentes backends seguros
        backends_to_try = ['Qt5Agg', 'TkAgg', 'Agg']
        
        for backend in backends_to_try:
            try:
                matplotlib.use(backend, force=True)
                import matplotlib.pyplot as plt
                # Probar crear una figura simple
                fig = plt.figure(figsize=(1, 1))
                plt.close(fig)
                print(f"OK Backend {backend} funcionando correctamente")
                return backend
            except Exception as e:
                print(f"WARNING Backend {backend} fallo: {e}")
                continue
        
        print("ERROR No se pudo configurar ningun backend de matplotlib")
        return None
        
    except Exception as e:
        print(f"ERROR configurando backend: {e}")
        return None

# Aplicar configuración automáticamente al importar
if __name__ != "__main__":
    configure_matplotlib_for_windows()