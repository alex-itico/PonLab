"""
Device Types (Tipos de Dispositivos)
Implementaciones específicas para dispositivos OLT y ONU
"""

from .device import Device
from ..algorithms.upstream_scheduler import UpstreamScheduler
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import numpy as np
import time

class OLT(Device):
    """Optical Line Terminal - Equipo central de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("OLT", name, x, y)
        
        # Propiedades básicas del OLT
        self.properties = {
            'model': 'OLT-Generic',
            'status': 'online',
            'location': '',
            'notes': '',
            'total_bandwidth': 10000,  # 10 Gbps
            'allocated_bandwidth': 0,
            'transmission_rate': 4096.0,  # Tasa de transmisión en Mbps (4 Gbps por defecto)
            'polling_cycle_time': 2.0,  # Tiempo de ciclo de polling en ms
            'guard_time': 0.1,  # Tiempo de guarda entre transmisiones en ms
        }
        
        # Estado del protocolo PON
        self.registered_onus = {}  # ID -> ONU object
        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self._poll_onus)
        self.current_onu_index = 0
        self.simulation_active = False
        
        # Estadísticas
        self.stats = {
            'total_polls': 0,
            'successful_responses': 0,
            'timeouts': 0,
            'bandwidth_requests': []
        }
        
        # Crear scheduler después de definir las propiedades
        try:
            self.scheduler = UpstreamScheduler(self.properties['total_bandwidth'])
        except Exception as e:
            print(f"Error al crear scheduler: {e}")
            self.scheduler = None
    
    def register_onu(self, onu):
        """Registrar una ONU en el OLT"""
        self.registered_onus[onu.id] = onu
        onu.set_olt_reference(self)
        print(f"🔗 ONU {onu.name} registrada en OLT {self.name}")
    
    def unregister_onu(self, onu_id):
        """Desregistrar una ONU del OLT"""
        if onu_id in self.registered_onus:
            onu = self.registered_onus[onu_id]
            onu.set_olt_reference(None)
            del self.registered_onus[onu_id]
            print(f"🔌 ONU {onu.name} desregistrada del OLT {self.name}")
    
    def start_polling(self):
        """Iniciar el ciclo de polling"""
        if not self.registered_onus:
            print("WARNING No hay ONUs registradas para polling")
            return
        
        self.simulation_active = True
        self.current_onu_index = 0
        self.stats = {
            'total_polls': 0,
            'successful_responses': 0,
            'timeouts': 0,
            'bandwidth_requests': []
        }
        
        polling_interval = int(self.properties['polling_cycle_time'] * 1000)  # Convertir a ms
        self.polling_timer.start(polling_interval)
        print(f"🔄 Iniciando polling con ciclo de {self.properties['polling_cycle_time']}s")
    
    def stop_polling(self):
        """Detener el ciclo de polling"""
        self.simulation_active = False
        self.polling_timer.stop()
        print("⏹️ Polling detenido")
    
    def _poll_onus(self):
        """Ejecutar un ciclo de polling de todas las ONUs"""
        if not self.simulation_active or not self.registered_onus:
            return
        
        onu_list = list(self.registered_onus.values())
        
        for onu in onu_list:
            self._poll_single_onu(onu)
    
    def _poll_single_onu(self, onu):
        """Realizar polling a una ONU específica"""
        self.stats['total_polls'] += 1
        
        # Simular tiempo de propagación
        propagation_delay = np.random.uniform(0.1, 0.5)  # 0.1-0.5 ms
        
        try:
            # Enviar mensaje de polling
            response = onu.handle_poll_request()
            
            if response:
                self.stats['successful_responses'] += 1
                bandwidth_request = response.get('bandwidth_request', 0)
                
                if bandwidth_request > 0:
                    self.stats['bandwidth_requests'].append({
                        'onu_id': onu.id,
                        'onu_name': onu.name,
                        'timestamp': time.time(),
                        'request': bandwidth_request
                    })
                    
                    print(f"📊 Polling ONU {onu.name}: {bandwidth_request} Mbps solicitados")
                else:
                    print(f"✅ Polling ONU {onu.name}: Sin solicitudes de ancho de banda")
            else:
                self.stats['timeouts'] += 1
                print(f"⏰ Timeout en polling de ONU {onu.name}")
                
        except Exception as e:
            self.stats['timeouts'] += 1
            print(f"❌ Error en polling de ONU {onu.name}: {e}")
    
    def get_polling_stats(self):
        """Obtener estadísticas del polling"""
        if self.stats['total_polls'] > 0:
            success_rate = (self.stats['successful_responses'] / self.stats['total_polls']) * 100
        else:
            success_rate = 0
            
        return {
            'total_polls': self.stats['total_polls'],
            'successful_responses': self.stats['successful_responses'],
            'timeouts': self.stats['timeouts'],
            'success_rate': success_rate,
            'registered_onus': len(self.registered_onus),
            'total_bandwidth_requests': len(self.stats['bandwidth_requests'])
        }
    
    # ═══════════════════════════════════════════════════════════
    # 🔗 INTEGRACIÓN CON PON OLT CORE
    # ═══════════════════════════════════════════════════════════
    
    def create_pon_olt_instance(self, onus_dict: dict = None, links_data: dict = None):
        """
        Crear instancia de PON OLT core sincronizada con las propiedades del dispositivo
        
        Args:
            onus_dict: Diccionario de ONUs {onu_id: ONU_instance}
            links_data: Configuración de enlaces {link_id: {length: km}}
        """
        try:
            # Import lazy para evitar dependencias circulares
            from ..pon.pon_olt import OLT as PonOLT
            
            # Usar valores por defecto si no se proporcionan
            if onus_dict is None:
                onus_dict = {}
            
            if links_data is None:
                links_data = {"0": {"length": 0.5}, "1": {"length": 0.5}}
            
            # Crear instancia PON OLT con propiedades sincronizadas
            self._pon_olt_instance = PonOLT(
                id=self.id,
                onus=onus_dict,
                dba_algorithm=None,  # Se puede configurar después
                links_data=links_data,
                transmission_rate=self.properties['transmission_rate'],  # ⚡ Sincronizado!
                seed=12345
            )
            
            print(f"🔗 PON OLT core creado para {self.name} con transmission_rate={self.properties['transmission_rate']} Mbps")
            return self._pon_olt_instance
            
        except ImportError as e:
            print(f"❌ Error importando PON OLT core: {e}")
            return None
        except Exception as e:
            print(f"❌ Error creando PON OLT core: {e}")
            return None
    
    def get_pon_olt_instance(self):
        """Obtener instancia PON OLT (lazy loading)"""
        if not hasattr(self, '_pon_olt_instance') or self._pon_olt_instance is None:
            return self.create_pon_olt_instance()
        return self._pon_olt_instance
    
    def sync_transmission_rate(self):
        """Sincronizar tasa de transmisión con la instancia PON OLT core"""
        if hasattr(self, '_pon_olt_instance') and self._pon_olt_instance is not None:
            self._pon_olt_instance.transmission_rate = self.properties['transmission_rate']
            print(f"🔄 Transmission rate sincronizada: {self.properties['transmission_rate']} Mbps")
    
    def update_property(self, key: str, value):
        """Override para sincronizar cambios de propiedades con PON OLT core"""
        if key in self.properties:
            self.properties[key] = value
            
            # Sincronización especial para transmission_rate
            if key == 'transmission_rate':
                self.sync_transmission_rate()
            
            self.properties_changed.emit()
            print(f"📝 Propiedad {key} actualizada a: {value}")


class ONU(Device):
    """Optical Network Unit - Equipo terminal de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("ONU", name, x, y)
        
        # Propiedades básicas de la ONU
        self.properties = {
            'model': 'ONU-Generic',  # Modelo del equipo
            'status': 'online',      # Estado operacional
            'location': '',          # Ubicación física
            'notes': '',              # Notas adicionales
            'upstream_bandwidth': 1000,  # 1 Gbps max bandwidth
            'allocated_bandwidth': 0,
            'transmission_rate': 1024.0,  # Tasa de transmisión en Mbps (1 Gbps por defecto)
            'traffic_profile': 'constant',
            'mean_rate': 500,  # Mbps
            'burst_size': 100,   # Mbps
            'response_probability': 0.95,  # Probabilidad de responder al polling
            'queue_size': 0,  # Tamaño actual de la cola de datos
            'max_queue_size': 1000  # Tamaño máximo de cola en MB
        }
        
        # Estado del protocolo
        self.olt_reference = None
        self.registration_id = None
        self.last_poll_time = 0
        self.transmission_window = None  # Ventana de transmisión asignada
        
        # Estadísticas de la ONU
        self.stats = {
            'polls_received': 0,
            'responses_sent': 0,
            'data_transmitted': 0,  # MB
            'bandwidth_requests_sent': 0
        }
        
        # Buffer de datos simulado
        self.data_buffer = []
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self._generate_traffic)
    
    def set_olt_reference(self, olt):
        """Establecer referencia al OLT"""
        self.olt_reference = olt
        if olt:
            self.registration_id = f"REG_{self.id[:8]}"
            print(f"📡 ONU {self.name} conectada con OLT {olt.name}")
        else:
            self.registration_id = None
            print(f"📡 ONU {self.name} desconectada del OLT")
    
    def start_traffic_generation(self):
        """Iniciar generación de tráfico simulado"""
        # Generar tráfico cada 500ms
        self.buffer_timer.start(500)
    
    def stop_traffic_generation(self):
        """Detener generación de tráfico"""
        self.buffer_timer.stop()
    
    def _generate_traffic(self):
        """Generar tráfico de datos basado en el perfil configurado"""
        if self.properties['status'] != 'online':
            return
            
        # Simular llegada de datos según el perfil de tráfico
        traffic_amount = self.generate_bandwidth_request() / 8  # Convertir Mbps a MB/s
        traffic_amount = traffic_amount * 0.5  # Ajustar por intervalo de 500ms
        
        # Agregar al buffer si hay espacio
        if self.properties['queue_size'] + traffic_amount <= self.properties['max_queue_size']:
            self.properties['queue_size'] += traffic_amount
            self.data_buffer.append({
                'timestamp': time.time(),
                'size': traffic_amount,
                'priority': np.random.choice(['high', 'normal', 'low'], p=[0.1, 0.7, 0.2])
            })
    
    def handle_poll_request(self):
        """Manejar solicitud de polling del OLT"""
        self.stats['polls_received'] += 1
        self.last_poll_time = time.time()
        
        # Simular posibilidad de no responder (pérdida de paquetes, fallos, etc.)
        if np.random.random() > self.properties['response_probability']:
            return None  # No responder (timeout)
        
        # Calcular solicitud de ancho de banda basada en el buffer actual
        bandwidth_request = 0
        if self.properties['queue_size'] > 0:
            # Convertir datos en cola a solicitud de ancho de banda (MB -> Mbps)
            bandwidth_request = min(
                self.properties['queue_size'] * 8,  # MB * 8 = Mbits
                self.properties['upstream_bandwidth']
            )
            
            if bandwidth_request > 0:
                self.stats['bandwidth_requests_sent'] += 1
        
        # Preparar respuesta
        response = {
            'onu_id': self.id,
            'registration_id': self.registration_id,
            'status': self.properties['status'],
            'bandwidth_request': bandwidth_request,
            'queue_size': self.properties['queue_size'],
            'priority_data': len([d for d in self.data_buffer if d['priority'] == 'high']),
            'timestamp': time.time()
        }
        
        self.stats['responses_sent'] += 1
        return response
    
    def receive_grant(self, granted_bandwidth, transmission_window):
        """Recibir asignación de ancho de banda del OLT"""
        self.properties['allocated_bandwidth'] = granted_bandwidth
        self.transmission_window = transmission_window
        
        if granted_bandwidth > 0:
            # Simular transmisión de datos
            self._transmit_data(granted_bandwidth)
            print(f"📤 ONU {self.name}: Transmitiendo con {granted_bandwidth} Mbps asignados")
    
    def _transmit_data(self, bandwidth_mbps):
        """Simular transmisión de datos durante la ventana asignada"""
        # Calcular cuántos datos se pueden transmitir
        max_data_mb = bandwidth_mbps / 8  # Convertir Mbps a MB/s
        
        # Transmitir datos disponibles hasta el límite
        transmitted = 0
        transmitted_packets = []
        
        while self.data_buffer and transmitted < max_data_mb:
            packet = self.data_buffer.pop(0)
            if transmitted + packet['size'] <= max_data_mb:
                transmitted += packet['size']
                transmitted_packets.append(packet)
                self.properties['queue_size'] -= packet['size']
            else:
                # Packet fragmentado, devolver lo que no se puede transmitir
                remaining = packet['size'] - (max_data_mb - transmitted)
                packet['size'] = remaining
                self.data_buffer.insert(0, packet)
                break
        
        self.stats['data_transmitted'] += transmitted
        
        # Limpiar ventana de transmisión
        self.transmission_window = None
        self.properties['allocated_bandwidth'] = 0
    
    def generate_bandwidth_request(self):
        """Generar solicitud de ancho de banda realista basada en el perfil de tráfico"""
        if self.properties['traffic_profile'] == 'constant':
            return self.properties['mean_rate']
            
        elif self.properties['traffic_profile'] == 'variable':
            # Distribución normal alrededor de la media
            request = np.random.normal(
                self.properties['mean_rate'],
                self.properties['mean_rate'] * 0.2
            )
            return max(0, min(request, self.properties['upstream_bandwidth']))
            
        elif self.properties['traffic_profile'] == 'burst':
            # Modelo simple de ráfagas
            if np.random.random() < 0.3:  # 30% probabilidad de ráfaga
                return min(
                    self.properties['mean_rate'] + self.properties['burst_size'],
                    self.properties['upstream_bandwidth']
                )
            return self.properties['mean_rate']
    
    def get_onu_stats(self):
        """Obtener estadísticas de la ONU"""
        return {
            'polls_received': self.stats['polls_received'],
            'responses_sent': self.stats['responses_sent'],
            'data_transmitted': self.stats['data_transmitted'],
            'bandwidth_requests_sent': self.stats['bandwidth_requests_sent'],
            'current_queue_size': self.properties['queue_size'],
            'allocated_bandwidth': self.properties['allocated_bandwidth'],
            'response_rate': (self.stats['responses_sent'] / max(1, self.stats['polls_received'])) * 100
        }


# Factory function para crear dispositivos
def create_device(device_type, name=None, x=0, y=0):
    """Factory para crear dispositivos según tipo"""
    if device_type.upper() == "OLT":
        return OLT(name, x, y)
    elif device_type.upper() == "ONU":
        return ONU(name, x, y)
    else:
        raise ValueError(f"Tipo de dispositivo no soportado: {device_type}")
