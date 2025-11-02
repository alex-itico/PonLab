"""
Gestor de Dispositivos Personalizados
Maneja la creación, edición, eliminación y almacenamiento de dispositivos OLT/ONU personalizados
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class CustomDeviceManager:
    """Gestor de dispositivos personalizados"""
    
    def __init__(self):
        self.custom_devices_dir = os.path.join("resources", "custom_devices")
        self.olt_file = os.path.join(self.custom_devices_dir, "custom_olt.json")
        self.onu_file = os.path.join(self.custom_devices_dir, "custom_onu.json")
        
        # Crear directorio si no existe
        self._ensure_directory()
        
        # Inicializar archivos si no existen
        self._initialize_files()
    
    def _ensure_directory(self):
        """Crear directorio de dispositivos personalizados si no existe"""
        if not os.path.exists(self.custom_devices_dir):
            os.makedirs(self.custom_devices_dir)
            print(f"📁 Directorio creado: {self.custom_devices_dir}")
    
    def _initialize_files(self):
        """Inicializar archivos JSON si no existen"""
        if not os.path.exists(self.olt_file):
            self._save_json(self.olt_file, [])
            print(f"📄 Archivo creado: {self.olt_file}")
        
        if not os.path.exists(self.onu_file):
            self._save_json(self.onu_file, [])
            print(f"📄 Archivo creado: {self.onu_file}")
    
    def _load_json(self, file_path: str) -> List[Dict]:
        """Cargar datos desde archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando {file_path}: {e}")
            return []
    
    def _save_json(self, file_path: str, data: List[Dict]):
        """Guardar datos en archivo JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Guardado exitoso: {file_path}")
        except Exception as e:
            print(f"❌ Error guardando {file_path}: {e}")
    
    def _generate_id(self, device_type: str) -> str:
        """Generar ID único para dispositivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"CUSTOM_{device_type.upper()}_{timestamp}"
    
    # ===== OPERACIONES OLT =====
    
    def load_custom_olts(self) -> List[Dict]:
        """Cargar todos los OLT personalizados"""
        return self._load_json(self.olt_file)
    
    def save_custom_olt(self, device_data: Dict) -> Dict:
        """
        Guardar nuevo OLT personalizado
        
        Args:
            device_data: Diccionario con datos del dispositivo
                {
                    'name': str,
                    'transmission_rate': int,
                    'pon_ports': int,
                    'buffer_capacity': int,
                    'dba_algorithm': str
                }
        
        Returns:
            Diccionario con el dispositivo guardado (incluye ID y fecha)
        """
        olts = self.load_custom_olts()
        
        # Validar nombre duplicado
        if any(olt['name'] == device_data['name'] for olt in olts):
            raise ValueError(f"Ya existe un OLT con el nombre '{device_data['name']}'")
        
        # Generar ID y agregar metadata
        device_data['id'] = self._generate_id('OLT')
        device_data['type'] = 'CUSTOM_OLT'
        device_data['created_at'] = datetime.now().isoformat()
        device_data['modified_at'] = datetime.now().isoformat()
        
        # Agregar a la lista
        olts.append(device_data)
        
        # Guardar
        self._save_json(self.olt_file, olts)
        
        print(f"✅ OLT personalizado creado: {device_data['name']} (ID: {device_data['id']})")
        return device_data
    
    def update_custom_olt(self, device_id: str, device_data: Dict) -> Optional[Dict]:
        """
        Actualizar OLT personalizado existente
        
        Args:
            device_id: ID del dispositivo a actualizar
            device_data: Nuevos datos del dispositivo
        
        Returns:
            Diccionario actualizado o None si no se encuentra
        """
        olts = self.load_custom_olts()
        
        # Buscar el dispositivo
        for i, olt in enumerate(olts):
            if olt['id'] == device_id:
                # Validar nombre duplicado (excepto si es el mismo)
                if any(o['name'] == device_data['name'] and o['id'] != device_id for o in olts):
                    raise ValueError(f"Ya existe un OLT con el nombre '{device_data['name']}'")
                
                # Mantener metadata original
                device_data['id'] = olt['id']
                device_data['type'] = olt['type']
                device_data['created_at'] = olt['created_at']
                device_data['modified_at'] = datetime.now().isoformat()
                
                # Actualizar
                olts[i] = device_data
                self._save_json(self.olt_file, olts)
                
                print(f"✅ OLT actualizado: {device_data['name']} (ID: {device_id})")
                return device_data
        
        print(f"❌ OLT no encontrado: {device_id}")
        return None
    
    def delete_custom_olt(self, device_id: str) -> bool:
        """
        Eliminar OLT personalizado
        
        Args:
            device_id: ID del dispositivo a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        olts = self.load_custom_olts()
        
        # Filtrar el dispositivo
        original_count = len(olts)
        olts = [olt for olt in olts if olt['id'] != device_id]
        
        if len(olts) < original_count:
            self._save_json(self.olt_file, olts)
            print(f"✅ OLT eliminado: {device_id}")
            return True
        
        print(f"❌ OLT no encontrado: {device_id}")
        return False
    
    def get_custom_olt_by_id(self, device_id: str) -> Optional[Dict]:
        """Obtener OLT personalizado por ID"""
        olts = self.load_custom_olts()
        for olt in olts:
            if olt['id'] == device_id:
                return olt
        return None
    
    # ===== OPERACIONES ONU =====
    
    def load_custom_onus(self) -> List[Dict]:
        """Cargar todos los ONU personalizados"""
        return self._load_json(self.onu_file)
    
    def save_custom_onu(self, device_data: Dict) -> Dict:
        """
        Guardar nuevo ONU personalizado
        
        Args:
            device_data: Diccionario con datos del dispositivo
                {
                    'name': str,
                    'color': str
                }
        
        Returns:
            Diccionario con el dispositivo guardado (incluye ID y fecha)
        """
        onus = self.load_custom_onus()
        
        # Validar nombre duplicado
        if any(onu['name'] == device_data['name'] for onu in onus):
            raise ValueError(f"Ya existe un ONU con el nombre '{device_data['name']}'")
        
        # Generar ID y agregar metadata
        device_data['id'] = self._generate_id('ONU')
        device_data['type'] = 'CUSTOM_ONU'
        device_data['created_at'] = datetime.now().isoformat()
        device_data['modified_at'] = datetime.now().isoformat()
        
        # Agregar a la lista
        onus.append(device_data)
        
        # Guardar
        self._save_json(self.onu_file, onus)
        
        print(f"✅ ONU personalizado creado: {device_data['name']} (ID: {device_data['id']})")
        return device_data
    
    def update_custom_onu(self, device_id: str, device_data: Dict) -> Optional[Dict]:
        """
        Actualizar ONU personalizado existente
        
        Args:
            device_id: ID del dispositivo a actualizar
            device_data: Nuevos datos del dispositivo
        
        Returns:
            Diccionario actualizado o None si no se encuentra
        """
        onus = self.load_custom_onus()
        
        # Buscar el dispositivo
        for i, onu in enumerate(onus):
            if onu['id'] == device_id:
                # Validar nombre duplicado (excepto si es el mismo)
                if any(o['name'] == device_data['name'] and o['id'] != device_id for o in onus):
                    raise ValueError(f"Ya existe un ONU con el nombre '{device_data['name']}'")
                
                # Mantener metadata original
                device_data['id'] = onu['id']
                device_data['type'] = onu['type']
                device_data['created_at'] = onu['created_at']
                device_data['modified_at'] = datetime.now().isoformat()
                
                # Actualizar
                onus[i] = device_data
                self._save_json(self.onu_file, onus)
                
                print(f"✅ ONU actualizado: {device_data['name']} (ID: {device_id})")
                return device_data
        
        print(f"❌ ONU no encontrado: {device_id}")
        return None
    
    def delete_custom_onu(self, device_id: str) -> bool:
        """
        Eliminar ONU personalizado
        
        Args:
            device_id: ID del dispositivo a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        onus = self.load_custom_onus()
        
        # Filtrar el dispositivo
        original_count = len(onus)
        onus = [onu for onu in onus if onu['id'] != device_id]
        
        if len(onus) < original_count:
            self._save_json(self.onu_file, onus)
            print(f"✅ ONU eliminado: {device_id}")
            return True
        
        print(f"❌ ONU no encontrado: {device_id}")
        return False
    
    def get_custom_onu_by_id(self, device_id: str) -> Optional[Dict]:
        """Obtener ONU personalizado por ID"""
        onus = self.load_custom_onus()
        for onu in onus:
            if onu['id'] == device_id:
                return onu
        return None


# Instancia global del gestor
custom_device_manager = CustomDeviceManager()
