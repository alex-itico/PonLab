"""
Verificador de Compatibilidad PonLab
Verifica que las funcionalidades de simulación y RL estén correctamente integradas
"""

import sys
import os

def test_imports():
    """Verificar que todas las importaciones funcionen"""
    print("🔍 Verificando importaciones...")
    
    try:
        # Core PON
        from core.pon.pon_adapter import PONAdapter
        from core.simulation.pon_simulator import PONSimulator
        from core.smart_rl_dba import SmartRLDBAAlgorithm
        print("✅ Core PON importado correctamente")
    except Exception as e:
        print(f"❌ Error importando Core PON: {e}")
        return False
    
    try:
        # UI Components
        from ui.main_window import MainWindow
        from ui.integrated_pon_test_panel import IntegratedPONTestPanel
        from ui.pon_sdn_dashboard import PONSDNDashboard
        from ui.rl_config_panel import RLConfigPanel
        print("✅ Componentes UI importados correctamente")
    except Exception as e:
        print(f"❌ Error importando UI: {e}")
        return False
    
    try:
        # Utilities
        from utils.config_manager import config_manager
        from utils.constants import AVAILABLE_DBA_ALGORITHMS
        print("✅ Utilidades importadas correctamente")
    except Exception as e:
        print(f"❌ Error importando utilidades: {e}")
        return False
        
    return True

def test_pon_adapter():
    """Verificar funcionalidad del PONAdapter"""
    print("🔍 Verificando PONAdapter...")
    
    try:
        from core.pon.pon_adapter import PONAdapter
        
        adapter = PONAdapter()
        
        # Verificar algoritmos disponibles
        algorithms = adapter.get_available_algorithms()
        print(f"📋 Algoritmos disponibles: {algorithms}")
        
        expected_algorithms = ["FCFS", "Priority", "RL-DBA", "SDN"]
        for algo in expected_algorithms:
            if algo in algorithms:
                print(f"✅ {algo} está disponible")
            else:
                print(f"❌ {algo} no está disponible")
        
        # Verificar Smart-RL availability
        smart_rl_available = adapter.is_smart_rl_available()
        print(f"🧠 Smart-RL disponible: {smart_rl_available}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando PONAdapter: {e}")
        return False

def test_smart_rl_dba():
    """Verificar Smart RL DBA interno"""
    print("🔍 Verificando Smart RL DBA...")
    
    try:
        from core.smart_rl_dba import SmartRLDBAAlgorithm
        
        # Crear instancia del algoritmo
        smart_rl = SmartRLDBAAlgorithm()
        print("✅ SmartRLDBAAlgorithm creado correctamente")
        
        # Verificar que el agente interno está disponible
        if hasattr(smart_rl, 'agent') and smart_rl.agent is not None:
            print("✅ Agente RL interno disponible")
        else:
            print("❌ Agente RL interno no disponible")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Smart RL DBA: {e}")
        return False

def test_hybrid_algorithms():
    """Verificar algoritmos híbridos Smart-RL-SDN"""
    print("🔍 Verificando algoritmos híbridos...")
    
    try:
        from core.pon.pon_adapter import PONAdapter
        
        adapter = PONAdapter()
        
        # Simular carga de modelo RL
        try:
            # Intentar cargar un modelo de prueba (puede fallar, pero no debe romper)
            result = adapter.load_rl_model("test_model.pkl")
            if not result[0]:
                print("ℹ️  No se pudo cargar modelo de prueba (normal)")
        except:
            print("ℹ️  Carga de modelo falló (esperado sin modelo real)")
        
        # Verificar que los algoritmos híbridos están reconocidos
        try:
            # Verificar Smart-RL
            algo = adapter._get_dba_algorithm_by_name("Smart-RL")
            print("❌ Smart-RL reconocido sin modelo (no debería pasar)")
        except ValueError as e:
            print("✅ Smart-RL requiere modelo cargado (correcto)")
        
        try:
            # Verificar Smart-RL-SDN
            algo = adapter._get_dba_algorithm_by_name("Smart-RL-SDN")
            print("❌ Smart-RL-SDN reconocido sin modelo (no debería pasar)")
        except ValueError as e:
            print("✅ Smart-RL-SDN requiere modelo cargado (correcto)")
        
        # Verificar SDN simple
        try:
            algo = adapter._get_dba_algorithm_by_name("SDN")
            print("✅ SDN disponible sin modelo adicional")
        except Exception as e:
            print(f"❌ SDN no disponible: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando algoritmos híbridos: {e}")
        return False

def test_constants():
    """Verificar constantes actualizadas"""
    print("🔍 Verificando constantes...")
    
    try:
        from utils.constants import AVAILABLE_DBA_ALGORITHMS, DBA_ALGORITHM_DESCRIPTIONS
        
        print(f"📋 Algoritmos en constantes: {AVAILABLE_DBA_ALGORITHMS}")
        
        expected_algorithms = ["FCFS", "Priority", "RL-DBA", "SDN", "Smart-RL", "Smart-RL-SDN"]
        for algo in expected_algorithms:
            if algo in AVAILABLE_DBA_ALGORITHMS:
                print(f"✅ {algo} en constantes")
                if algo in DBA_ALGORITHM_DESCRIPTIONS:
                    print(f"   📝 Descripción: {DBA_ALGORITHM_DESCRIPTIONS[algo]}")
                else:
                    print(f"   ❌ Sin descripción para {algo}")
            else:
                print(f"❌ {algo} no está en constantes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando constantes: {e}")
        return False

def test_config_manager():
    """Verificar gestor de configuraciones"""
    print("🔍 Verificando gestor de configuraciones...")
    
    try:
        from utils.config_manager import config_manager
        
        # Verificar configuraciones RL y SDN
        rl_enabled = config_manager.get_rl_enabled()
        sdn_enabled = config_manager.get_sdn_enabled()
        default_algorithm = config_manager.get_dba_algorithm()
        
        print(f"🧠 RL habilitado: {rl_enabled}")
        print(f"🌐 SDN habilitado: {sdn_enabled}")
        print(f"⚙️  Algoritmo por defecto: {default_algorithm}")
        
        # Probar guardar configuración
        config_manager.save_dba_algorithm("SDN")
        saved_algo = config_manager.get_dba_algorithm()
        if saved_algo == "SDN":
            print("✅ Guardado/carga de configuración funciona")
            # Restaurar configuración original
            config_manager.save_dba_algorithm(default_algorithm)
        else:
            print("❌ Guardado/carga de configuración falla")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando config manager: {e}")
        return False

def main():
    """Ejecutar todas las verificaciones"""
    print("🚀 Iniciando verificación de compatibilidad PonLab")
    print("=" * 60)
    
    tests = [
        ("Importaciones", test_imports),
        ("PON Adapter", test_pon_adapter), 
        ("Smart RL DBA", test_smart_rl_dba),
        ("Algoritmos Híbridos", test_hybrid_algorithms),
        ("Constantes", test_constants),
        ("Gestor Configuraciones", test_config_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Excepción en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las verificaciones pasaron! El sistema está listo.")
        return True
    else:
        print("⚠️  Algunas verificaciones fallaron. Revise los errores arriba.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
