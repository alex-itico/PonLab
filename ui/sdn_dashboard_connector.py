"""
SDN Dashboard Connector
Conector entre OLT_SDN y el Dashboard SDN para actualización automática de métricas
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from typing import Optional
import typing

if typing.TYPE_CHECKING:
    from core.pon.pon_sdn import OLT_SDN
    from ui.pon_sdn_dashboard import PONSDNDashboard


class SDNDashboardConnector(QObject):
    """
    Conector que vincula OLT_SDN con el Dashboard SDN
    Actualiza automáticamente las métricas del dashboard
    """
    
    # Señal emitida cuando las métricas se actualizan
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.olt_sdn_instance: Optional['OLT_SDN'] = None
        self.dashboard: Optional['PONSDNDashboard'] = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.auto_update_enabled = False
        
    def set_olt_sdn(self, olt_sdn: 'OLT_SDN'):
        """
        Configurar la instancia de OLT_SDN a monitorear
        
        Args:
            olt_sdn: Instancia de OLT_SDN
        """
        self.olt_sdn_instance = olt_sdn
        print(f"[SDNDashboardConnector] OLT_SDN configurado: {olt_sdn.id if olt_sdn else 'None'}")
        
    def set_dashboard(self, dashboard: 'PONSDNDashboard'):
        """
        Configurar el dashboard a actualizar
        
        Args:
            dashboard: Instancia del dashboard SDN
        """
        self.dashboard = dashboard
        # Conectar señal de métricas al dashboard
        self.metrics_updated.connect(dashboard.update_metrics)
        print("[SDNDashboardConnector] Dashboard configurado y conectado")
        
    def start_auto_update(self, interval_ms: int = 1000):
        """
        Iniciar actualización automática del dashboard
        
        Args:
            interval_ms: Intervalo de actualización en milisegundos
        """
        if self.olt_sdn_instance and self.dashboard:
            self.update_timer.start(interval_ms)
            self.auto_update_enabled = True
            print(f"[SDNDashboardConnector] Auto-actualización iniciada (cada {interval_ms}ms)")
        else:
            print("[SDNDashboardConnector] ERROR: OLT_SDN o Dashboard no configurados")
            
    def stop_auto_update(self):
        """Detener actualización automática del dashboard"""
        self.update_timer.stop()
        self.auto_update_enabled = False
        print("[SDNDashboardConnector] Auto-actualización detenida")
        
    def update_now(self):
        """Forzar actualización inmediata del dashboard"""
        self._update_metrics()
        
    def _update_metrics(self):
        """Actualizar métricas del dashboard desde OLT_SDN"""
        if not self.olt_sdn_instance:
            print("[SDNDashboardConnector] No hay OLT_SDN configurado")
            return
            
        try:
            # Obtener métricas del OLT_SDN
            metrics = self.olt_sdn_instance.get_sdn_dashboard()
            
            # Emitir señal con las métricas
            self.metrics_updated.emit(metrics)
            
            print(f"[SDNDashboardConnector] Métricas actualizadas - Fairness: {metrics['global_metrics'].get('current_fairness', 0):.3f}")
            
        except Exception as e:
            print(f"[SDNDashboardConnector] Error al actualizar métricas: {e}")
            import traceback
            traceback.print_exc()
            
    def is_connected(self) -> bool:
        """Verificar si el conector está completamente configurado"""
        return self.olt_sdn_instance is not None and self.dashboard is not None
        
    def get_status(self) -> dict:
        """Obtener estado del conector"""
        return {
            'olt_sdn_configured': self.olt_sdn_instance is not None,
            'dashboard_configured': self.dashboard is not None,
            'auto_update_enabled': self.auto_update_enabled,
            'is_connected': self.is_connected()
        }
