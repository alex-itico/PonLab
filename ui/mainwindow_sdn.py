"""
MainWindow SDN methods for PON Simulator
"""

class MainWindowSDNMixin:
    def update_sdn_metrics(self, metrics):
        """Actualizar métricas del dashboard SDN"""
        if not metrics:
            print("⚠️ No hay métricas SDN para actualizar")
            return False
            
        if not self.sdn_dashboard:
            # Intentar crear el dashboard si no existe
            self.setup_sdn_dashboard()
            if not self.sdn_dashboard:
                print("❌ Error: No se pudo crear el dashboard SDN")
                return False
        
        try:
            self.sdn_dashboard.update_metrics(metrics)
            onu_count = len(metrics.get('onu_metrics', {}))
            print(f"📊 Métricas SDN actualizadas en dashboard ({onu_count} ONUs)")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando métricas SDN: {e}")
            import traceback
            traceback.print_exc()
            return False