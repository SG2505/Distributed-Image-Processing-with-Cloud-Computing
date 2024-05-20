import EC2_API
import S3_API
import time
import boto3
import threading
from datetime import datetime, timedelta  # Import datetime module


# Initialize AWS clients
ec2_client = boto3.client('ec2')
elbv2_client = boto3.client('elbv2')

# Define scaling parameters
MAX_REQUESTS_BEFORE_SCALING = 5
MAX_NUMBER_OF_INSTANCES = 8
DESIRED_INSTANCE_COUNT = 2
TARGET_GROUP_ARN ='arn:aws:elasticloadbalancing:eu-central-1:851725392781:targetgroup/Image-Processing-Frank-TG/4594d70e60686eda'
IMAGE_PROCESSING_SCRIPT_PATH = 'D:/Distributed Computing/Project/Project source code/image_processing_flask.py'
REMOTE_SCRIPT_PATH = '/home/ubuntu/image_processing_flask_script.py'

REQUESTS_PER_INSTANCE = 5
request_count = 0

global_all_instances_health = {}









def get_instances_health(target_group_arn):
    # Initialize the ELBv2 client
    elbv2_client = boto3.client('elbv2')

    # Get target health descriptions for the specified target group
    response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)

    # Extract instance IDs and health statuses from the response
    instances_health = {}
    for target_health in response['TargetHealthDescriptions']:
        instance_id = target_health['Target']['Id']
        health_status = target_health['TargetHealth']['State']
        instances_health[instance_id] = health_status

    return instances_health


def get_number_of_instances_in_target_group(target_group_arn):
    # Initialize the ELBv2 client
    elbv2_client = boto3.client('elbv2')

    try:
        # Describe target health to get information about targets in the target group
        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        
        # Count the number of instances in the target group
        instance_count = len(response['TargetHealthDescriptions'])
        
        return instance_count
    except Exception as e:
        print(f"Error: {e}")
        return None





def count_healthy_instances(instance_status_dict):
    # Initialize count
    healthy_count = 0
    
    # Iterate over dictionary values
    for status in instance_status_dict.values():
        # Check if status is 'healthy'
        if status == 'healthy':
            healthy_count += 1
    
    return healthy_count




def add_instance_to_target():
    new_instance_id = EC2_API.create_ec2_instance()  # Create new instances
    EC2_API.assign_iam_role_to_instance(new_instance_id, 'S3-Access')
    EC2_API.add_instance_to_target_group(new_instance_id, TARGET_GROUP_ARN)
    ssh = EC2_API.initialize_ssh_connection(new_instance_id)
    EC2_API.execute_ssh_commands(ssh)
    EC2_API.modify_instance_metadata_options(new_instance_id)
    EC2_API.upload_file(IMAGE_PROCESSING_SCRIPT_PATH, REMOTE_SCRIPT_PATH, ssh)
    EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH, ssh)





def get_unhealthy_instance_ids(instances_health):
    unhealthy_instance_ids = []
    for instance_id, health_status in instances_health.items():
        if health_status != 'healthy':
            unhealthy_instance_ids.append(instance_id)
    return unhealthy_instance_ids





def auto_scaling_and_Fault_tolerance():

    global request_count
    Fault_Tolerance_flag = False
    Auto_Scaling_flag = False

    while True:
        # Get monitoring metrics

        # request_count = get_request_count()
        all_instances_health = get_instances_health(TARGET_GROUP_ARN)
        existing_instances_count = get_number_of_instances_in_target_group(TARGET_GROUP_ARN)

        healthy_instances_count = count_healthy_instances(all_instances_health)
        print(f"healthy_instances_count = {healthy_instances_count}")

        # each interation check on unhealthy and remove them
        unhealthy_instances = get_unhealthy_instance_ids(all_instances_health)

        for instance_id in unhealthy_instances:
            print(f"Terminating instance {instance_id}...")
            EC2_API.terminate_ec2_instance(instance_id)
            print(f"Instance {instance_id} terminated successfully.")
            all_instances_health.pop(instance_id, None)
            print("Terminated instances removed from instances_health dictionary.")
            existing_instances_count -= 1
            
        ###################################################### scaling ##################################################################
        # calculate the required instances based on request count
        if request_count % 3 == 0:
            Needed_Vms = request_count // REQUESTS_PER_INSTANCE
        
        else:
            Needed_Vms = (request_count // REQUESTS_PER_INSTANCE) +1
        
        actual_desired_instances = Needed_Vms - existing_instances_count

        # Check if scaling up is needed based on the calculated required instances
        print(f"desired_instances = {actual_desired_instances}, Needed_Vms= {Needed_Vms} , existing_instances= {existing_instances_count} , request_count= {request_count} ")
        if (actual_desired_instances < 0) and (actual_desired_instances != 0):
            actual_desired_instances *= -1
            for i in range(actual_desired_instances):

                if existing_instances_count <= DESIRED_INSTANCE_COUNT:
                    break
                EC2_API.terminate_ec2_instance(list(all_instances_health.keys())[i])
                existing_instances_count -= 1
                
        elif actual_desired_instances != 0:

            if (actual_desired_instances + existing_instances_count) >= MAX_NUMBER_OF_INSTANCES:
                actual_desired_instances = MAX_NUMBER_OF_INSTANCES - existing_instances_count

            if actual_desired_instances != 0:
                Auto_Scaling_flag = True

            for _ in range(actual_desired_instances):
                instance_scale_thread = threading.Thread(target=add_instance_to_target)
                instance_scale_thread.start()
        
        

        ####################################################### Fault Tolerance #########################################################

        # Check if scaling up is needed based on healthy instance count
        # DESIRED_INSTANCE_COUNT instead of 2
        if not Auto_Scaling_flag:
            if (healthy_instances_count < DESIRED_INSTANCE_COUNT) and (existing_instances_count < MAX_NUMBER_OF_INSTANCES):
                
                instances_needed = max(0, DESIRED_INSTANCE_COUNT - healthy_instances_count)
                if instances_needed != 0:
                    Fault_Tolerance_flag = True

                print(f"instance needed in fault tolerance = {instances_needed}")
                for _ in range(instances_needed):

                    instance_fault_thread = threading.Thread(target=add_instance_to_target)
                    instance_fault_thread.start()
                    

            elif (healthy_instances_count < existing_instances_count) and (existing_instances_count < MAX_NUMBER_OF_INSTANCES):   
                instances_needed = max(0, existing_instances_count - healthy_instances_count)
                if instances_needed != 0:
                    Fault_Tolerance_flag = True

                print(f"instance needed in fault tolerance = {instances_needed}")
                for _ in range(instances_needed):

                    instance_fault_thread = threading.Thread(target=add_instance_to_target)
                    instance_fault_thread.start()


                
        if Fault_Tolerance_flag or Auto_Scaling_flag:
            request_count = 0
            Fault_Tolerance_flag = Auto_Scaling_flag = False
            time.sleep(400)  # wait until instances created, add to target group and become healthy
        
        else:
            request_count = 0
            time.sleep(60)
        

# def update_health_dictionary():

#     global global_all_instances_health

#     while True:
    
#         global_all_instances_health = get_instances_health(TARGET_GROUP_ARN)
#         #GUI update status and machines
#         time.sleep(30)


# def main():
#     global request_count
    
   
  
#     # try to test the get_req_count
#     # try to link the requests count with the request of the ALB file
#     # link with gui

# EC2_API.run_ec2_instance('i-0ef6f74543c8d27dc')
# ssh = EC2_API.initialize_ssh_connection('i-0ef6f74543c8d27dc')
# EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH,ssh)

# EC2_API.run_ec2_instance('i-0025c7ff8c7bef4ae')
# ssh = EC2_API.initialize_ssh_connection('i-0025c7ff8c7bef4ae')
# EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH,ssh)

#     # print(get_instances_health(TARGET_GROUP_ARN))

    
#     #####################################################################################
#     Scale_and_fault_thread = threading.Thread(target=auto_scaling_and_Fault_tolerance)
#     Scale_and_fault_thread.start()

#     time.sleep(30)

#     request_count = 48

#     time.sleep(450)

#     request_count = 3

#     Scale_and_fault_thread.join()
    
    

# if __name__ == "__main__":
#     main()
