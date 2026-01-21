import boto3
from datetime import datetime, timedelta

def get_cloudwatch_client(region):
    return boto3.client('cloudwatch', region_name=region)

def get_ec2_client(region):
    return boto3.client('ec2', region_name=region)

def get_metric(cw_client, instance_id, metric_name, namespace, stat='Average'):
    try:
        response = cw_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            # this is because the aws cloudwatch metircs are not always available so i am checking last 10 min
            StartTime=datetime.utcnow() - timedelta(minutes=10),
            EndTime=datetime.utcnow(),
            # first 60 seconds which is there I am considering as the metrics
            Period=60,
            Statistics=[stat]
        )
        if response['Datapoints']:
            # Sort by timestamp to get the absolute latest value
            return sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1][stat]
    except Exception as e:
        print(f"Error fetching metric {metric_name} for {instance_id}: {e}")
    return None

def fetch_instance_metrics(instance_id, region):
    cw = get_cloudwatch_client(region)
    
    cpu = get_metric(cw, instance_id, 'CPUUtilization', 'AWS/EC2')
    # Memory metrics usually come from the CloudWatch Agent (custom namespace 'CWAgent')
    # If the agent is not installed/configured, this will return None
    memory = get_metric(cw, instance_id, 'mem_used_percent', 'CWAgent')
    net_in = get_metric(cw, instance_id, 'NetworkIn', 'AWS/EC2')
    net_out = get_metric(cw, instance_id, 'NetworkOut', 'AWS/EC2')
    disk_read = get_metric(cw, instance_id, 'DiskReadBytes', 'AWS/EC2')
    
    return {
        'cpu_utilization': cpu,
        'memory_usage': memory,
        'network_in': net_in,
        'network_out': net_out,
        'disk_read': disk_read
    }

def verify_connection(instance_id, region):
    """
    Verifies if we can connect to AWS and find the instance.
    Returns (True, instance_details_dict) or (False, error_message).
    """
    try:
        ec2 = get_ec2_client(region)
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if response['Reservations'] and response['Reservations'][0]['Instances']:
            instance = response['Reservations'][0]['Instances'][0]
            return True, instance
        return False, "Instance not found"
    except Exception as e:
        return False, str(e)
