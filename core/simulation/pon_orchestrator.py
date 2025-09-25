"""
PON Orchestrator
Orquestador PON integrado de netPONPy con interfaz mejorada para PonLab
"""

import numpy as np
from typing import Dict, List, Any, Optional
from enum import Enum

from ..algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm
from ..pon.pon_olt import OLT
from ..pon.pon_onu import ONU
from ..utilities.pon_traffic import get_traffic_scenario, calculate_realistic_lambda


class SimulatorStatus(Enum):
    """Estado del simulador"""
    N_A = "N_A"
    ALLOCATED = "ALLOCATED"
    NOT_ALLOCATED = "NOT_ALLOCATED"


class SimulationResult:
    """Resultado de un paso de simulación"""
    
    def __init__(self, status: SimulatorStatus, metrics: Dict[str, Any], done: bool, info: Dict[str, Any]):
        self.status = status
        self.metrics = metrics
        self.done = done
        self.info = info


class PONOrchestrator:
    """
    Orquestador PON independiente que encapsula toda la lógica del dominio.
    
    Inspirado en el patrón simulator.py de Dream-On-Gym, separa completamente
    la lógica de simulación del entorno RL.
    """
    
    def __init__(self, num_onus: int = 4, traffic_scenario: str = "residential_medium",
                 episode_duration: float = 1.0, simulation_timestep: float = 0.001):
        """
        Inicializar orquestador PON.
        
        Args:
            num_onus: Número de ONUs en la red
            traffic_scenario: Escenario de tráfico
            episode_duration: Duración del episodio en segundos
            simulation_timestep: Paso de simulación en segundos
        """
        self.num_onus = num_onus
        self.traffic_scenario = traffic_scenario
        self.episode_duration = episode_duration
        self.simulation_timestep = simulation_timestep
        self.steps_per_episode = int(episode_duration / simulation_timestep)
        
        # Estado del orquestador
        self.current_step = 0
        self._goal_connections = 10000
        self._last_status = SimulatorStatus.N_A
        
        # Componentes del orquestador
        self.olt = None
        self.current_request = None
        self.onus_config = None
        self.dba_algorithm = None  # Se configurará después con set_dba_algorithm()
        
        # Métricas acumulativas
        self.episode_metrics = {
            'delays': [],
            'throughputs': [],
            'total_transmitted': 0,
            'total_requests': 0,
            'buffer_levels_history': []
        }
        
        # Control de métricas
        self.cumulative_transmitted = 0.0
        self.episode_start_time = 0.0
        
        # Callback para logging detallado
        self.log_callback = None
        
        # Inicializar componentes
        self._create_components()
    
    def set_log_callback(self, callback):
        """Establecer callback para logging detallado"""
        self.log_callback = callback
    
    def _log_event(self, category: str, message: str):
        """Enviar evento al log callback si está disponible"""
        if self.log_callback:
            formatted_message = f"[{category}] {message}"
            self.log_callback(formatted_message)
    
    def _create_components(self):
        """Crear componentes del simulador (OLT, ONUs)"""
        # Crear ONUs
        self.onus_config = self._create_onus()
        
        # Crear OLT con algoritmo DBA modular (FCFS por defecto)
        links_data = {str(i): {"length": 1.0} for i in range(self.num_onus)}
        default_dba = FCFSDBAAlgorithm()
        
        self.olt = OLT(
            id="olt_sim",
            onus=self.onus_config,
            dba_algorithm=default_dba,
            links_data=links_data,
            transmition_rate=1024.0
        )
        
        # Inicializar solicitud actual
        self.current_request = None
        
        self._log_event("INIT", f"Componentes creados: OLT con {self.num_onus} ONUs")
    
    def _create_onus(self) -> Dict[str, ONU]:
        """Crear configuración de ONUs"""
        scenario_config = get_traffic_scenario(self.traffic_scenario)
        onus = {}
        
        for i in range(self.num_onus):
            onu_id = str(i)
            sla = 100.0 + i * 50.0  # SLAs diferenciados
            lambda_rate = calculate_realistic_lambda(sla, scenario_config)
            
            traffic_probs = {
                "highest": 0.1,
                "high": 0.2,
                "medium": 0.4,
                "low": 0.2,
                "lowest": 0.1
            }
            
            onus[onu_id] = ONU(
                id=onu_id,
                name=f"ONU_{i}",
                traffic_transmition_probs=traffic_probs,
                transmition_rate=100.0,
                service_level_agreement=sla,
                buffer_size=500,
                mean_arrival_rate=lambda_rate,
                avg_request_size_mb=scenario_config["request_size_mb"],
                traffic_sizes_mb=scenario_config.get("traffic_sizes_mb", None)
            )
        
        self._log_event("ONUS", f"{self.num_onus} ONUs creadas con escenario {self.traffic_scenario}")
        return onus
    
    def init(self) -> None:
        """Inicializar simulador - solo orquestación, OLT maneja el tráfico"""
        # Inicializar OLT y obtener primera solicitud - delegar todo a la arquitectura original
        self.current_request = self.olt.init()
        self.episode_start_time = self.olt.clock
        self._log_event("INIT", f"Simulador inicializado en t={self.episode_start_time:.6f}")
    
    def step(self, action: Any) -> SimulationResult:
        """
        Ejecutar un paso de simulación.
        
        Args:
            action: Acción a aplicar en el algoritmo DBA
            
        Returns:
            SimulationResult con estado, métricas, flag done e info.
        """
        # Aplicar acción al algoritmo DBA
        self._apply_dba_algorithm(action)
        
        # Ejecutar simulación por un timestep
        metrics = self._simulate_timestep()
        
        # Actualizar métricas
        self.episode_metrics['delays'].extend(metrics.get('delays', []))
        self.episode_metrics['throughputs'].extend(metrics.get('throughputs', []))
        self.episode_metrics['total_transmitted'] += metrics.get('transmitted', 0)
        self.episode_metrics['total_requests'] += metrics.get('requests_processed', 0)
        
        # Actualizar niveles de buffer
        current_buffer_levels = self.get_buffer_levels()
        self.episode_metrics['buffer_levels_history'].append(current_buffer_levels)
        
        # Actualizar paso
        self.current_step += 1
        
        # Verificar si el episodio ha terminado
        done = self.current_step >= self.steps_per_episode
        
        # Definir estado basado en si la solicitud fue procesada
        if metrics.get('requests_processed', 0) > 0:
            self._last_status = SimulatorStatus.ALLOCATED if metrics.get('transmitted', 0) > 0 else SimulatorStatus.NOT_ALLOCATED
        
        # Log detallado si está habilitado
        if metrics.get('requests_processed', 0) > 0:
            self._log_event("STEP", f"Paso {self.current_step}: {metrics['requests_processed']} solicitudes, "
                          f"{metrics.get('transmitted', 0):.3f}MB transmitidos")
        
        return SimulationResult(
            status=self._last_status,
            metrics=metrics,
            done=done,
            info={
                'step': self.current_step,
                'sim_time': self.olt.clock,
                'buffer_levels': current_buffer_levels
            }
        )
    
    def reset(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reiniciar simulador al estado inicial preservando configuración DBA"""
        # Preservar configuración DBA actual
        current_dba_algorithm = self.dba_algorithm
        
        # Reiniciar estado
        self.current_step = 0
        self.episode_metrics = {
            'delays': [],
            'throughputs': [],
            'total_transmitted': 0,
            'total_requests': 0,
            'buffer_levels_history': []
        }
        self.cumulative_transmitted = 0.0
        self.episode_start_time = 0.0
        self._last_status = SimulatorStatus.N_A
        
        # Recrear componentes
        self._create_components()
        
        # Restaurar configuración DBA
        if current_dba_algorithm is not None:
            self.set_dba_algorithm(current_dba_algorithm)
        
        # Inicializar
        self.init()
        
        self._log_event("RESET", "Simulador reiniciado")
        
        return {
            'buffer_levels': self.get_buffer_levels(),
            'sim_time': self.olt.clock,
            'step': self.current_step
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado completo del simulador para monitoreo"""
        return {
            'buffer_levels': self.get_buffer_levels(),
            'delays': self.get_delays(),
            'throughputs': self.get_throughputs(),
            'sim_time': self.olt.clock,
            'step': self.current_step,
            'total_transmitted': self.episode_metrics['total_transmitted'],
            'total_requests': self.episode_metrics['total_requests']
        }
    
    def get_buffer_levels(self) -> List[float]:
        """Obtener niveles de buffer normalizados [0-1] para todas las ONUs"""
        buffer_levels = []
        for i in range(self.num_onus):
            onu_id = str(i)
            onu = self.olt.onus[onu_id]
            level = len(onu.buffer) / max(onu.buffer.size, 1)
            buffer_levels.append(min(level, 1.0))
        return buffer_levels
    
    def get_delays(self) -> List[Dict[str, Any]]:
        """Obtener delays recientes (últimos 10)"""
        return self.episode_metrics['delays'][-10:]
    
    def get_throughputs(self) -> List[Dict[str, Any]]:
        """Obtener throughputs recientes (últimos 10)"""
        return self.episode_metrics['throughputs'][-10:]
    
    def last_request_is_allocated(self) -> SimulatorStatus:
        """Obtener estado de la última solicitud procesada"""
        return self._last_status
    
    def set_dba_algorithm(self, algorithm: DBAAlgorithmInterface) -> None:
        """Establecer algoritmo DBA para el simulador"""
        self.dba_algorithm = algorithm        
        self.olt.set_dba_algorithm(algorithm)
        self._log_event("DBA", f"Algoritmo DBA configurado: {algorithm.get_algorithm_name()}")
    
    def get_allocation_probability(self) -> float:
        """Calcular probabilidad de asignación en intervalo de tiempo - más preciso para redes PON"""
        # Obtener conteo de paquetes perdidos por overflow de buffer de todas las ONUs
        total_lost_packets = sum(onu.lost_packets_count for onu in self.olt.onus.values())
        
        # Total de solicitudes intentadas = procesadas + perdidas en buffers
        total_attempted = self.episode_metrics['total_requests'] + total_lost_packets
        
        if total_attempted == 0:
            return 1.0  # Sin solicitudes = 100% éxito de asignación
        
        # Solicitudes exitosamente asignadas y transmitidas (tienen delays registrados)
        successfully_allocated = sum(1 for d in self.episode_metrics['delays'] if d.get('delay', 0) > 0)
        
        # Probabilidad de asignación = asignaciones exitosas / total intentadas
        return successfully_allocated / total_attempted
    
    def get_blocking_probability(self) -> float:
        """Método legacy para compatibilidad - retorna 1 - allocation_probability"""
        return 1.0 - self.get_allocation_probability()
    
    def get_simulation_time(self) -> float:
        """Tiempo de simulación actual"""
        return self.olt.clock if self.olt else 0.0
    
    @property
    def goal_connections(self) -> int:
        return self._goal_connections
    
    @goal_connections.setter
    def goal_connections(self, value: int) -> None:
        self._goal_connections = value
    
    def _apply_dba_algorithm(self, action: Any):
        """Aplicar algoritmo DBA modular con la acción del agente"""
        
        # Verificar si el algoritmo DBA está configurado
        if self.dba_algorithm is None:
            return
        # Establecer la acción en el OLT para algoritmos RL
        self.olt.set_action(action)
    
    def _simulate_timestep(self) -> Dict[str, Any]:
        """Simular un timestep usando OLT - orquestación pura.
        
        Delega completamente a la arquitectura OLT original sin interferir
        con la generación natural de tráfico Poisson.
        """
        metrics = {
            'delays': [],
            'throughputs': [],
            'transmitted': 0,
            'requests_processed': 0
        }
        
        try:
            start_time = self.olt.clock
            target_time = start_time + self.simulation_timestep
            
            while self.olt.clock < target_time and self.current_request:
                # Procesar solicitud usando OLT
                success, processed_request = self.olt.proccess(self.current_request)
                
                if success:
                    # Cálculo de delay
                    delay = processed_request.departure_time - processed_request.created_at
                    
                    # Cálculo de throughput
                    traffic_mb = processed_request.get_total_traffic()
                    self.cumulative_transmitted += traffic_mb
                    
                    # Acumulación de throughput
                    elapsed_time = self.olt.clock - self.episode_start_time
                    if elapsed_time > 0:
                        throughput_mbps = self.cumulative_transmitted / elapsed_time
                    else:
                        throughput_mbps = 0.0
                    
                    metrics['delays'].append({
                        'delay': delay,
                        'onu_id': processed_request.source_id
                    })
                    metrics['throughputs'].append({
                        'throughput': throughput_mbps,
                        'onu_id': processed_request.source_id
                    })
                    metrics['transmitted'] += traffic_mb
                
                metrics['requests_processed'] += 1
                
                # Obtener próxima solicitud del OLT
                try:
                    self.current_request = self.olt.get_next_request()
                except:
                    break
                    
        except Exception as e:
            # En caso de error, registrarlo y continuar
            self._log_event("ERROR", f"Error durante timestep de simulación: {e}")
        
        return metrics
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas del orquestador"""
        olt_stats = self.olt.get_olt_stats() if self.olt else {}
        onu_stats = {onu_id: onu.get_onu_stats() for onu_id, onu in (self.olt.onus.items() if self.olt else {})}
        
        return {
            'orchestrator_info': {
                'num_onus': self.num_onus,
                'traffic_scenario': self.traffic_scenario,
                'episode_duration': self.episode_duration,
                'simulation_timestep': self.simulation_timestep,
                'current_step': self.current_step,
                'steps_per_episode': self.steps_per_episode
            },
            'episode_metrics': self.episode_metrics.copy(),
            'cumulative_transmitted': self.cumulative_transmitted,
            'allocation_probability': self.get_allocation_probability(),
            'blocking_probability': self.get_blocking_probability(),
            'olt_stats': olt_stats,
            'onu_stats': onu_stats
        }
    
    def __str__(self) -> str:
        dba_name = self.dba_algorithm.get_algorithm_name() if self.dba_algorithm else "None"
        return f"PONOrchestrator(onus={self.num_onus}, scenario={self.traffic_scenario}, dba={dba_name})"
    
    def __repr__(self) -> str:
        return self.__str__()