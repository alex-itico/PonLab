#!/usr/bin/env python3
"""
Test de validación de conexiones ONU-ONU
Este script prueba que las ONUs no puedan conectarse entre sí
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.devices.device_types import OLT, ONU
from core.connections.connection_manager import ConnectionManager

def test_onu_connection_validation():
    """Probar las validaciones de conexión PON"""
    print("🧪 Iniciando test de validación de conexiones PON...")
    
    # Crear dispositivos de prueba
    olt1 = OLT("OLT-Central", 100, 100)
    onu1 = ONU("ONU-Cliente1", 200, 150)
    onu2 = ONU("ONU-Cliente2", 200, 250)
    
    # Crear gestor de conexiones
    connection_manager = ConnectionManager()
    
    print(f"\n📱 Dispositivos creados:")
    print(f"  • {olt1.name} (tipo: {olt1.device_type})")
    print(f"  • {onu1.name} (tipo: {onu1.device_type})")
    print(f"  • {onu2.name} (tipo: {onu2.device_type})")
    
    # Test 1: Intentar conectar ONU con ONU (debería fallar)
    print(f"\n🔍 Test 1: Intentar conectar {onu1.name} con {onu2.name}")
    can_connect, error_msg = connection_manager.can_connect(onu1, onu2)
    
    if not can_connect:
        print(f"✅ CORRECTO: Conexión bloqueada")
        print(f"📝 Mensaje: {error_msg}")
    else:
        print(f"❌ ERROR: La conexión debería estar bloqueada")
    
    # Test 2: Conectar ONU con OLT (debería funcionar)
    print(f"\n🔍 Test 2: Intentar conectar {onu1.name} con {olt1.name}")
    can_connect, error_msg = connection_manager.can_connect(onu1, olt1)
    
    if can_connect:
        print(f"✅ CORRECTO: Conexión ONU-OLT permitida")
    else:
        print(f"❌ ERROR: La conexión ONU-OLT debería estar permitida")
        print(f"📝 Mensaje: {error_msg}")
    
    # Test 3: Conectar OLT con ONU (debería funcionar)
    print(f"\n🔍 Test 3: Intentar conectar {olt1.name} con {onu2.name}")
    can_connect, error_msg = connection_manager.can_connect(olt1, onu2)
    
    if can_connect:
        print(f"✅ CORRECTO: Conexión OLT-ONU permitida")
    else:
        print(f"❌ ERROR: La conexión OLT-ONU debería estar permitida")
        print(f"📝 Mensaje: {error_msg}")
    
    print(f"\n🎯 Test completado!")

if __name__ == "__main__":
    test_onu_connection_validation()
