import random
from util.logger import logger

def generate_mock_metrics(instance_id):
    """
    Generate mock metrics for testing without AWS CLI.
    Generates realistic metrics mostly in the 40-50% utilization range.
    
    Args:
        instance_id: The instance ID to generate metrics for
        
    Returns:
        Dictionary with mock metrics in the same format as fetch_instance_metrics
    """
    # Generate CPU and memory in the 40-50% range with some variation
    # 80% of the time in 40-50%, 20% of the time slightly outside for realism
    if random.random() < 0.8:
        cpu = random.uniform(40, 50)
        memory = random.uniform(40, 50)
    else:
        # Occasional variation outside the main range
        cpu = random.uniform(35, 60)
        memory = random.uniform(35, 60)
    
    # Add small random variations to make it more realistic
    cpu = round(cpu + random.uniform(-2, 2), 2)
    memory = round(memory + random.uniform(-2, 2), 2)
    
    # Ensure values stay within valid bounds (0-100%)
    cpu = max(0, min(100, cpu))
    memory = max(0, min(100, memory))
    
    # Generate network metrics (in bytes)
    # Simulate moderate network activity
    network_in = random.randint(1000000, 5000000)  # 1-5 MB
    network_out = random.randint(500000, 3000000)  # 0.5-3 MB
    
    # Simulate disk read activity
    disk_read = random.randint(100000, 1000000)  # 100KB-1MB
    
    logger.info(f"Generated mock metrics for {instance_id}: CPU={cpu:.2f}%, Memory={memory:.2f}%")
    
    return {
        'cpu_utilization': cpu,
        'memory_usage': memory,
        'network_in': network_in,
        'network_out': network_out,
        'disk_read': disk_read
    }
