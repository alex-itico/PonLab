"""
PON NetSim
Motor de simulación integrado de netPONPy
"""

from typing import Optional, Dict, Any
from ..data.pon_request import Request
from ..pon.pon_olt import OLT


class EventEvaluator:
    """Interfaz base para evaluadores de eventos"""
    
    def on_init(self):
        """Callback al iniciar simulación"""
        pass
    
    def on_update(self, attributes: Dict[str, Any]):
        """Callback en cada paso de simulación"""
        pass
    
    def on_run_end(self, attributes: Dict[str, Any]):
        """Callback al finalizar simulación"""
        pass


class NetSim:
    """Simulador de red PON integrado de netPONPy"""
    
    def __init__(self, network: OLT):
        """
        Inicializar simulador
        
        Args:
            network: Red PON (OLT) a simular
        """
        self.request: Optional[Request] = None
        self.network = network
        self.steps = 0

        # Métricas globales
        self.total_delay = 0.0
        self.total_attended_capacity = 0.0
        self.total_requests_processed = 0
        self.successful_requests = 0
        
        # Historial de métricas
        self.delay_history = []
        self.throughput_history = []
        self.utilization_history = []

    def run(self, timesteps: int, callback: Optional[EventEvaluator] = None):
        """
        Ejecutar simulación por número de pasos
        
        Args:
            timesteps: Número de pasos de simulación
            callback: Evaluador de eventos opcional
        """
        print(f"🚀 Iniciando simulación NetSim: {timesteps} pasos")
        
        callback and callback.on_init()
        self.steps = 0
        self.request = self.network.init()
        
        while self.steps < timesteps:
            try:
                # Obtener próxima solicitud
                current_request = self.network.get_next_request()
                requests_to_process = [current_request] if not isinstance(current_request, list) else current_request
                
                # Procesar cada solicitud
                for request in requests_to_process:
                    success, processed_request = self.network.proccess(request)
                    self.update_metrics(success, processed_request)
                    
                    # Callback con estado público
                    callback and callback.on_update(self.get_public_attributes())
                
                self.steps += 1
                
                if self.steps % 100 == 0:  # Log cada 100 pasos
                    print(f"📊 Paso {self.steps}: Delay promedio: {self.get_mean_delay():.3f}s, "
                          f"Throughput: {self.get_mean_throughput():.2f}MB/s")
                    
            except Exception as e:
                print(f"❌ Error en paso {self.steps}: {e}")
                break
        
        # Estadísticas finales
        mean_fragmented_time = self.network.fragmented_time / self.steps if self.steps > 0 else 0
        
        print(f"✅ Simulación completada:")
        print(f"   • Pasos ejecutados: {self.steps}")
        print(f"   • Delay promedio: {self.get_mean_delay():.6f}s")
        print(f"   • Tiempo fragmentado promedio: {mean_fragmented_time:.6f}s")
        print(f"   • Throughput promedio: {self.get_mean_throughput():.3f}MB/s")
        print(f"   • Solicitudes exitosas: {self.successful_requests}/{self.total_requests_processed}")
        
        callback and callback.on_run_end(self.get_public_attributes())

    def run_for_time(self, time: float, callback: Optional[EventEvaluator] = None):
        """
        Ejecutar simulación por tiempo específico
        
        Args:
            time: Tiempo de simulación en segundos
            callback: Evaluador de eventos opcional
        """
        print(f"🚀 Iniciando simulación NetSim: {time}s de tiempo simulado")
        
        callback and callback.on_init()
        self.steps = 0
        self.request = self.network.init()
        
        while self.network.clock < time:
            try:
                success, processed_request = self.network.proccess(self.request)
                self.update_metrics(success, processed_request)
                self.steps += 1
                
                callback and callback.on_update(self.get_public_attributes())
                self.request = self.network.get_next_request()
                
                # Log periódico
                if self.steps % 1000 == 0:
                    print(f"📊 t={self.network.clock:.3f}s, Paso {self.steps}: "
                          f"Delay promedio: {self.get_mean_delay():.3f}s")
                    
            except Exception as e:
                print(f"❌ Error en t={self.network.clock:.3f}s: {e}")
                break
        
        # Estadísticas finales por enlace
        print(f"📊 Estadísticas finales de enlaces:")
        for link_id, link in self.network.links.items():
            mean_traffic = link.bitrate_transmitted / time if time > 0 else 0
            print(f"   • Enlace {link_id}: {mean_traffic:.3f} MB/s promedio")
        
        # Estadísticas globales
        mean_fragmented_time = self.network.fragmented_time / self.steps if self.steps > 0 else 0
        
        print(f"✅ Simulación completada:")
        print(f"   • Tiempo simulado: {time}s (real: {self.network.clock:.3f}s)")
        print(f"   • Pasos ejecutados: {self.steps}")
        print(f"   • Delay promedio: {self.get_mean_delay():.6f}s")
        print(f"   • Tiempo fragmentado promedio: {mean_fragmented_time:.6f}s")
        print(f"   • Throughput promedio: {self.get_mean_throughput():.3f}MB/s")
        
        callback and callback.on_run_end(self.get_public_attributes())

    def update_metrics(self, success: bool, request: Request):
        """
        Actualizar métricas de la simulación
        
        Args:
            success: Si la transmisión fue exitosa
            request: Solicitud procesada
        """
        self.total_requests_processed += 1
        
        if success:
            self.successful_requests += 1
            
            # Calcular delay
            delay = request.get_delay()
            if delay < float('inf'):  # Solo si tiene departure_time válido
                self.total_delay += delay
                self.delay_history.append({
                    'step': self.steps,
                    'time': self.network.clock,
                    'delay': delay,
                    'onu_id': request.source_id
                })
            
            # Calcular throughput
            capacity = request.get_total_traffic()
            self.total_attended_capacity += capacity
            self.throughput_history.append({
                'step': self.steps,
                'time': self.network.clock,
                'throughput': capacity,
                'onu_id': request.source_id
            })
        
        # Calcular utilización de red
        if self.network.transmition_rate > 0:
            current_utilization = (request.get_total_traffic() / self.network.transmition_rate) * 100
            self.utilization_history.append({
                'step': self.steps,
                'time': self.network.clock,
                'utilization': current_utilization
            })

    def get_mean_delay(self) -> float:
        """Obtener delay promedio"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_delay / self.successful_requests

    def get_mean_throughput(self) -> float:
        """Obtener throughput promedio"""
        if self.steps == 0:
            return 0.0
        return self.total_attended_capacity / self.steps
        
    def get_network_utilization(self) -> float:
        """Obtener utilización promedio de la red"""
        if not self.utilization_history:
            return 0.0
        return sum(record['utilization'] for record in self.utilization_history) / len(self.utilization_history)

    def get_public_attributes(self) -> Dict[str, Any]:
        """Obtener atributos públicos para callbacks"""
        return {
            'steps': self.steps,
            'network_clock': self.network.clock,
            'total_requests_processed': self.total_requests_processed,
            'successful_requests': self.successful_requests,
            'total_delay': self.total_delay,
            'total_attended_capacity': self.total_attended_capacity,
            'mean_delay': self.get_mean_delay(),
            'mean_throughput': self.get_mean_throughput(),
            'network_utilization': self.get_network_utilization(),
            'network_stats': self.network.get_olt_stats(),
            'onu_stats': {onu_id: onu.get_onu_stats() for onu_id, onu in self.network.onus.items()}
        }
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Obtener resumen completo de la simulación"""
        return {
            'simulation_stats': {
                'total_steps': self.steps,
                'simulation_time': self.network.clock,
                'fragmented_time': self.network.fragmented_time,
                'total_requests': self.total_requests_processed,
                'successful_requests': self.successful_requests,
                'success_rate': (self.successful_requests / self.total_requests_processed * 100) if self.total_requests_processed > 0 else 0
            },
            'performance_metrics': {
                'mean_delay': self.get_mean_delay(),
                'mean_throughput': self.get_mean_throughput(),
                'network_utilization': self.get_network_utilization(),
                'total_capacity_served': self.total_attended_capacity
            },
            'network_stats': self.network.get_olt_stats(),
            'onu_stats': {onu_id: onu.get_onu_stats() for onu_id, onu in self.network.onus.items()},
            'history_sizes': {
                'delay_samples': len(self.delay_history),
                'throughput_samples': len(self.throughput_history),
                'utilization_samples': len(self.utilization_history)
            }
        }
    
    def reset_simulation(self):
        """Reiniciar simulación"""
        self.request = None
        self.steps = 0
        self.total_delay = 0.0
        self.total_attended_capacity = 0.0
        self.total_requests_processed = 0
        self.successful_requests = 0
        
        # Limpiar historiales
        self.delay_history.clear()
        self.throughput_history.clear()
        self.utilization_history.clear()
        
        # Reiniciar red
        self.network.reset_stats()
        for onu in self.network.onus.values():
            onu.reset_stats()
        
        print("🔄 Simulación reiniciada")
    
    def __str__(self) -> str:
        return f"NetSim(steps={self.steps}, clock={self.network.clock:.3f}s, requests={self.total_requests_processed})"
    
    def __repr__(self) -> str:
        return self.__str__()