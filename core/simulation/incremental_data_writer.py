"""
Incremental Data Writer
Sistema de escritura incremental de datos durante la simulación
Escribe datos en tiempo real con compresión gzip
"""

import os
import json
import gzip
import time
from typing import Dict, Any, Optional
from datetime import datetime


class IncrementalDataWriter:
    """
    Escritor de datos incremental para simulaciones PON.
    Escribe datos durante la simulación en lugar de al final.
    """

    def __init__(self, session_dir: str, use_compression: bool = True):
        """
        Inicializar escritor incremental

        Args:
            session_dir: Directorio donde guardar los datos
            use_compression: Usar compresión gzip (recomendado)
        """
        self.session_dir = session_dir
        self.use_compression = use_compression
        self.active = False

        # Archivos
        if use_compression:
            self.temp_file = os.path.join(session_dir, "datos_simulacion.json.gz.tmp")
        else:
            self.temp_file = os.path.join(session_dir, "datos_simulacion.json.tmp")

        self.file_handle = None

        # Estadísticas de escritura
        self.start_time = None
        self.chunks_written = 0
        self.bytes_written = 0
        self.last_flush_time = 0

        # Control de estructura JSON
        self.sections_started = set()
        self.first_item_in_section = {}

        print(f"📝 IncrementalDataWriter creado: {os.path.basename(self.temp_file)}")

    def start_writing(self) -> bool:
        """
        Iniciar escritura incremental

        Returns:
            True si se inició correctamente
        """
        try:
            # Abrir archivo
            if self.use_compression:
                self.file_handle = gzip.open(self.temp_file, 'wt', encoding='utf-8', compresslevel=6)
            else:
                self.file_handle = open(self.temp_file, 'w', encoding='utf-8')

            # Escribir inicio de JSON
            self.file_handle.write('{\n')

            self.active = True
            self.start_time = time.time()
            self.last_flush_time = self.start_time

            print(f"✅ Escritura incremental iniciada")
            return True

        except Exception as e:
            print(f"❌ Error iniciando escritura incremental: {e}")
            return False

    def start_section(self, section_name: str):
        """
        Iniciar una nueva sección del JSON

        Args:
            section_name: Nombre de la sección (ej: "buffer_snapshots")
        """
        if not self.active or section_name in self.sections_started:
            return

        # Si no es la primera sección, cerrar la anterior con coma
        if self.sections_started:
            self.file_handle.write(',\n')

        # Escribir inicio de sección
        self.file_handle.write(f'  "{section_name}": [\n')
        self.sections_started.add(section_name)
        self.first_item_in_section[section_name] = True

        print(f"📂 Sección '{section_name}' iniciada")

    def write_item(self, section_name: str, item: Dict[str, Any]):
        """
        Escribir un item a una sección

        Args:
            section_name: Nombre de la sección
            item: Diccionario con el item a escribir
        """
        if not self.active:
            return

        # Asegurar que la sección está iniciada
        if section_name not in self.sections_started:
            self.start_section(section_name)

        # Agregar coma si no es el primer item
        if not self.first_item_in_section.get(section_name, False):
            self.file_handle.write(',\n')
        else:
            self.first_item_in_section[section_name] = False

        # Escribir item (indentado 4 espacios)
        self.file_handle.write('    ')
        json.dump(item, self.file_handle, ensure_ascii=False, default=str)

        self.chunks_written += 1

        # Flush periódico (cada 1000 items o cada 5 segundos)
        current_time = time.time()
        if self.chunks_written % 1000 == 0 or (current_time - self.last_flush_time) >= 5.0:
            self.file_handle.flush()
            self.last_flush_time = current_time

            # Obtener tamaño del archivo
            if os.path.exists(self.temp_file):
                self.bytes_written = os.path.getsize(self.temp_file)

    def close_section(self, section_name: str):
        """
        Cerrar una sección del JSON

        Args:
            section_name: Nombre de la sección a cerrar
        """
        if not self.active or section_name not in self.sections_started:
            return

        # Cerrar array de la sección
        self.file_handle.write('\n  ]')

        # Marcar como cerrada para no cerrar dos veces
        self.sections_started.add(f"{section_name}_closed")

        print(f"📁 Sección '{section_name}' cerrada ({self.chunks_written} items)")

    def write_metadata(self, metadata: Dict[str, Any]):
        """
        Escribir metadata y otras secciones finales

        Args:
            metadata: Diccionario con metadata y secciones adicionales
        """
        if not self.active:
            print("⚠️ Writer no está activo, no se puede escribir metadata")
            return

        try:
            # Escribir cada sección de metadata
            for key, value in metadata.items():
                print(f"  📝 Escribiendo sección: {key}")
                self.file_handle.write(',\n')
                self.file_handle.write(f'  "{key}": ')

                # Serializar con indentación para legibilidad
                # Pero ajustar indentación para que se alinee correctamente
                json_str = json.dumps(value, ensure_ascii=False, default=str, indent=2)

                # Reemplazar saltos de línea para mantener indentación correcta
                json_str_indented = json_str.replace('\n', '\n  ')
                self.file_handle.write(json_str_indented)

                print(f"    ✅ Sección '{key}' escrita")

            # Flush después de escribir metadata
            self.file_handle.flush()

            print(f"📋 Metadata escrita ({len(metadata)} secciones)")

        except Exception as e:
            print(f"❌ Error escribiendo metadata: {e}")
            import traceback
            traceback.print_exc()

    def finalize(self) -> Optional[str]:
        """
        Finalizar escritura y renombrar archivo temporal

        Returns:
            Ruta del archivo final, o None si hubo error
        """
        if not self.active:
            return None

        try:
            # Hacer flush final antes de cerrar
            self.file_handle.flush()

            # Cerrar JSON
            self.file_handle.write('\n}\n')
            self.file_handle.flush()
            self.file_handle.close()

            # Calcular estadísticas finales
            elapsed_time = time.time() - self.start_time
            final_size_mb = os.path.getsize(self.temp_file) / (1024 * 1024)

            # Renombrar archivo temporal a final
            final_file = self.temp_file.replace('.tmp', '')
            os.rename(self.temp_file, final_file)

            self.active = False

            print(f"✅ Escritura incremental completada:")
            print(f"   📊 Items escritos: {self.chunks_written:,}")
            print(f"   💾 Tamaño final: {final_size_mb:.2f} MB")
            print(f"   ⏱️  Tiempo total: {elapsed_time:.2f}s")
            print(f"   📈 Velocidad: {self.chunks_written/elapsed_time:.0f} items/s")

            return final_file

        except Exception as e:
            print(f"❌ Error finalizando escritura: {e}")
            return None

    def abort(self):
        """Abortar escritura y eliminar archivo temporal"""
        if self.active and self.file_handle:
            try:
                self.file_handle.close()
                if os.path.exists(self.temp_file):
                    os.remove(self.temp_file)
                print(f"⚠️ Escritura incremental abortada")
            except Exception as e:
                print(f"❌ Error abortando escritura: {e}")
            finally:
                self.active = False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de escritura en tiempo real

        Returns:
            Diccionario con estadísticas
        """
        if not self.active:
            return {}

        elapsed_time = time.time() - self.start_time if self.start_time else 0

        return {
            'chunks_written': self.chunks_written,
            'bytes_written': self.bytes_written,
            'mb_written': self.bytes_written / (1024 * 1024),
            'elapsed_time': elapsed_time,
            'items_per_second': self.chunks_written / elapsed_time if elapsed_time > 0 else 0,
            'active': self.active
        }
