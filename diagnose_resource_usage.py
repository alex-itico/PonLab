"""
Diagnóstico de uso de recursos del simulador híbrido
Identifica problemas de memoria y CPU
"""

import sys
import os
import psutil
import time
import gc
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def monitor_resources(func_name, func):
    """Monitor resource usage during function execution"""
    process = psutil.Process()
    
    # Medición inicial
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    initial_cpu = process.cpu_percent()
    
    print(f"\n=== MONITORING: {func_name} ===")
    print(f"Initial Memory: {initial_memory:.1f} MB")
    
    start_time = time.time()
    
    try:
        result = func()
        success = True
    except Exception as e:
        print(f"ERROR: {e}")
        result = None
        success = False
    
    end_time = time.time()
    
    # Medición final
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    final_cpu = process.cpu_percent()
    duration = end_time - start_time
    
    print(f"Final Memory: {final_memory:.1f} MB")
    print(f"Memory Delta: +{final_memory - initial_memory:.1f} MB")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Success: {success}")
    
    return result, success, {
        'memory_delta': final_memory - initial_memory,
        'duration': duration,
        'success': success
    }

def test_event_queue_scaling():
    """Test how event queue scales with time"""
    from core.hybrid_pon_simulator import HybridPONSimulator
    
    print("\n=== EVENT QUEUE SCALING TEST ===")
    
    durations = [0.01, 0.1, 1.0]  # 10ms, 100ms, 1s
    
    for duration in durations:
        print(f"\nTesting duration: {duration}s")
        
        def run_simulation():
            simulator = HybridPONSimulator(num_onus=4, traffic_scenario="residential_light")
            # Contar eventos antes de ejecutar
            initial_events = simulator.event_queue.get_pending_events_count()
            print(f"  Initial events in queue: {initial_events}")
            
            results = simulator.run_simulation(duration)
            
            # Verificar eventos restantes
            remaining_events = simulator.event_queue.get_pending_events_count()
            print(f"  Remaining events in queue: {remaining_events}")
            
            # Verificar métricas acumuladas
            total_delays = len(simulator.metrics.get('delays', []))
            total_throughputs = len(simulator.metrics.get('throughputs', []))
            total_buffer_history = len(simulator.metrics.get('buffer_levels_history', []))
            
            print(f"  Delays stored: {total_delays}")
            print(f"  Throughputs stored: {total_throughputs}")
            print(f"  Buffer history entries: {total_buffer_history}")
            
            return results
        
        result, success, metrics = monitor_resources(f"Simulation_{duration}s", run_simulation)
        
        if not success:
            print(f"  FAILED at {duration}s - likely resource issue")
            break
        
        # Forzar garbage collection
        gc.collect()
        time.sleep(0.5)

def test_onu_scaling():
    """Test how simulator scales with number of ONUs"""
    from core.hybrid_pon_simulator import HybridPONSimulator
    
    print("\n=== ONU SCALING TEST ===")
    
    onu_counts = [2, 4, 8, 16]
    
    for num_onus in onu_counts:
        print(f"\nTesting {num_onus} ONUs")
        
        def run_simulation():
            simulator = HybridPONSimulator(
                num_onus=num_onus, 
                traffic_scenario="residential_light"
            )
            return simulator.run_simulation(0.05)  # 50ms fixed duration
        
        result, success, metrics = monitor_resources(f"ONUs_{num_onus}", run_simulation)
        
        if not success or metrics['memory_delta'] > 100:  # More than 100MB is problematic
            print(f"  RESOURCE LIMIT reached at {num_onus} ONUs")
            break
        
        gc.collect()
        time.sleep(0.5)

def test_traffic_generation():
    """Test traffic generation patterns"""
    from core.hybrid_onu import HybridONU
    from core.event_queue import EventQueue, EventType
    from core.traffic_scenarios import get_traffic_scenario, calculate_realistic_lambda
    
    print("\n=== TRAFFIC GENERATION TEST ===")
    
    scenario_config = get_traffic_scenario("residential_medium")
    lambda_rate = calculate_realistic_lambda(100.0, scenario_config)  # 100 Mbps SLA
    
    print(f"Lambda rate: {lambda_rate:.2f} packets/second")
    
    def test_onu_traffic():
        event_queue = EventQueue()
        onu = HybridONU("test_onu", lambda_rate, scenario_config)
        
        # Schedule initial packet
        onu.schedule_first_packet(event_queue, 0.0)
        
        # Simulate packet generation for a short time
        events_processed = 0
        simulation_time = 0.0
        max_simulation_time = 0.1  # 100ms
        
        while (event_queue.has_events() and 
               event_queue.peek_next_time() <= max_simulation_time and 
               events_processed < 1000):  # Safety limit
            
            event = event_queue.get_next_event()
            simulation_time = event.timestamp
            
            if event.event_type == EventType.PACKET_GENERATED:
                onu.generate_packet(event_queue, event.timestamp)
            
            events_processed += 1
        
        print(f"  Events processed: {events_processed}")
        print(f"  Simulation time reached: {simulation_time:.6f}s")
        print(f"  Events remaining: {event_queue.get_pending_events_count()}")
        
        # Check queue sizes
        total_packets = sum(len(q.packets) for q in onu.queues.values())
        total_bytes = sum(q.total_bytes for q in onu.queues.values())
        
        print(f"  Total packets in queues: {total_packets}")
        print(f"  Total bytes in queues: {total_bytes}")
        
        return events_processed
    
    result, success, metrics = monitor_resources("Traffic_Generation", test_onu_traffic)

def main():
    """Run resource usage diagnostics"""
    print("=== RESOURCE USAGE DIAGNOSTIC ===")
    print(f"Python version: {sys.version}")
    print(f"Available Memory: {psutil.virtual_memory().available / 1024 / 1024:.0f} MB")
    print(f"Available CPU cores: {psutil.cpu_count()}")
    
    try:
        # Test 1: Event queue scaling
        test_event_queue_scaling()
        
        # Test 2: ONU scaling  
        test_onu_scaling()
        
        # Test 3: Traffic generation
        test_traffic_generation()
        
    except Exception as e:
        print(f"\nFATAL ERROR in diagnostics: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== DIAGNOSTIC COMPLETE ===")
    print("\nCheck the results above to identify resource bottlenecks.")

if __name__ == "__main__":
    main()