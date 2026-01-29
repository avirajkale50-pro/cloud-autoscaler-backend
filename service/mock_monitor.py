import random
from util.logger import logger
from constants.service_constants import (
    MOCK_UTILIZATION_MIN_NORMAL, MOCK_UTILIZATION_MAX_NORMAL,
    MOCK_UTILIZATION_MIN_VARIANCE, MOCK_UTILIZATION_MAX_VARIANCE,
    MOCK_VARIANCE_ADJUSTMENT, MOCK_NETWORK_IN_MIN, MOCK_NETWORK_IN_MAX,
    MOCK_NETWORK_OUT_MIN, MOCK_NETWORK_OUT_MAX, MOCK_DISK_READ_MIN, MOCK_DISK_READ_MAX
)

def generate_mock_metrics(instance_id):
    # Generate CPU and memory in the 40-50% range with some variation 80% of the time in 40-50%, 20% of the time slightly outside for realism
    if random.random() < 0.8:
        cpu = random.uniform(MOCK_UTILIZATION_MIN_NORMAL, MOCK_UTILIZATION_MAX_NORMAL)
        memory = random.uniform(MOCK_UTILIZATION_MIN_NORMAL, MOCK_UTILIZATION_MAX_NORMAL)
    else:
        cpu = random.uniform(MOCK_UTILIZATION_MIN_VARIANCE, MOCK_UTILIZATION_MAX_VARIANCE)
        memory = random.uniform(MOCK_UTILIZATION_MIN_VARIANCE, MOCK_UTILIZATION_MAX_VARIANCE)
    
    cpu = round(cpu + random.uniform(-MOCK_VARIANCE_ADJUSTMENT, MOCK_VARIANCE_ADJUSTMENT), 2)
    memory = round(memory + random.uniform(-MOCK_VARIANCE_ADJUSTMENT, MOCK_VARIANCE_ADJUSTMENT), 2)
    
    cpu = max(0, min(100, cpu))
    memory = max(0, min(100, memory))
    
    network_in = random.randint(MOCK_NETWORK_IN_MIN, MOCK_NETWORK_IN_MAX)
    network_out = random.randint(MOCK_NETWORK_OUT_MIN, MOCK_NETWORK_OUT_MAX)
    
    disk_read = random.randint(MOCK_DISK_READ_MIN, MOCK_DISK_READ_MAX)
    
    logger.debug(f"Generated mock metrics for {instance_id}: CPU={cpu:.2f}%, Memory={memory:.2f}%")
    
    return {
        'cpu_utilization': cpu,
        'memory_usage': memory,
        'network_in': network_in,
        'network_out': network_out,
        'disk_read': disk_read
    }
