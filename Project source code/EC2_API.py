import boto3
import paramiko
import time

ssh = None
username = 'ubuntu'  
# Frankfurt -> "D:/Distributed Computing/Project/AWS key/Project-Frankfurt.pem"
private_key_path = "D:/Distributed Computing/Project/AWS keys/Project-Frankfurt.pem"  # stockholm -> D:/Distributed Computing/Project/AWS key/Project-Test-01.pem
public_ip = None  # Define a global variable for storing public DNS

 # Create EC2 client  Frankfurt -> region_name='eu-central-1'
ec2 = boto3.resource('ec2', region_name='eu-central-1') # stockholm 'eu-north-1'
ec2_client = boto3.client('ec2', region_name='eu-central-1')






def initialize_ssh_connection(instance_id):

    instance = ec2.Instance(instance_id)

    public_ip = instance.public_ip_address

    # Establish SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
    ssh.connect(hostname=public_ip, username=username, pkey=private_key)

    return ssh
    




def execute_ssh_commands(ssh_connection):

    # Commands to install Python and required libraries
    install_commands = [
        'sudo apt-get update && sudo apt-get upgrade -y',
        'sudo apt install -y python3 python3-pip python3-dev',
        'sudo apt install -y python3-opencv',
        'sudo apt install -y python3-boto3',
        'sudo apt install -y python3-flask',
        'sudo apt install -y python3-numpy'
        
    ]

    # Execute commands
    for command in install_commands:
        print(f"Executing: {command}")
        stdin, stdout, stderr = ssh_connection.exec_command(command)

        # # Print command output
        # print(stdout.read().decode())

        # Print any errors
        print(stderr.read().decode('utf-8'))






def upload_file(local_file_path, remote_file_path, ssh_connection):
    """
    Uploads a file from the local machine to the specified path on the remote machine using SSH.

    Args:
    - local_file_path (str): Path to the local file to be uploaded.
    - remote_file_path (str): Path on the remote machine where the file will be uploaded.
    - ssh_connection (paramiko.SSHClient): Paramiko SSHClient instance representing the SSH connection.

    Returns:
    - bool: True if the upload was successful, False otherwise.
    """

    try:
        # Open an SFTP session
        sftp = ssh_connection.open_sftp()

        # Upload the file
        sftp.put(local_file_path, remote_file_path)

        # Close the SFTP session
        sftp.close()

        print(f"File '{local_file_path}' uploaded to '{remote_file_path}' successfully.")
        return True
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False






def execute_remote_script_with_args(remote_script_path, ssh_connection, image_path, operation, image_output_name):
    """
    Executes a Python script on the remote machine using SSH.

    Args:
    - remote_script_path (str): Path to the Python script on the remote machine.
    - ssh_connection (paramiko.SSHClient): Paramiko SSHClient instance representing the SSH connection.

    Returns:
    - str: Output of the executed command.
    """

    try:
        # Make the script executable
        ssh_connection.exec_command(f"chmod +x {remote_script_path}")

        # Execute the Python script
        stdin, stdout, stderr = ssh_connection.exec_command(f"python3 {remote_script_path} {image_path} {operation} {image_output_name}")
        
        # Read the output
        output = stdout.read().decode('utf-8')

        # Check for errors
        error = stderr.read().decode('utf-8')
        if error:
            print(f"Error executing script: {error}")
        
        return output
    
    except Exception as e:
        print(f"Error executing script: {str(e)}")
        return None
    



###############################################################
def modify_instance_metadata_options(instance_id):

    response = ec2_client.modify_instance_metadata_options(
        InstanceId=instance_id,
        HttpTokens='optional',  # IMDSv2 setting
    )

    print("Instance metadata options modified successfully.")
    return response





def execute_remote_script(remote_script_path, ssh_connection):
    """
    Executes a Python script on the remote machine using SSH.

    Args:
    - remote_script_path (str): Path to the Python script on the remote machine.
    - ssh_connection (paramiko.SSHClient): Paramiko SSHClient instance representing the SSH connection.

    Returns:
    - str: Output of the executed command.
    """
   

    try:
        # Make the script executable
        ssh_connection.exec_command(f"sudo chmod a+x {remote_script_path}")
        print(f"Script {remote_script_path} made executable successfully.")

        # Execute the Python script        
        stdin, stdout, stderr = ssh_connection.exec_command(f"sudo python3 {remote_script_path}")

        # Read the output
        output = stdout.read().decode('utf-8')
        print(f"Script output:\n{output}")

        # Check for errors
        error = stderr.read().decode('utf-8')
        if error:
            print(f"Error executing script: {error}")

        return output
        

    except Exception as e:
        print(f"Error executing script: {str(e)}")
        return None





def create_ec2_instance(): #instance_name

    # Key pair name for (Frankfurt) -> Project-Frankfurt
    key_pair_name = "Project-Frankfurt" # stockholm "Project-Test-01"

    # AMI ID for Ubuntu (Frankfurt)-> ami-01e444924a2233b07
    ubuntu_ami_id = 'ami-01e444924a2233b07' # stockholm 'ami-0705384c0b33c194c'


    # Security group id for Frankfurt -> sg-0734464f28a13491f
    security_group_id = "sg-0734464f28a13491f" # stockholm "sg-05fb1384edf49343b"

    # Instance type Frankfurt -> t2.micro
    instance_type = "t2.micro" # stockholm t3.micro

    # # Tag Specifications
    # tags = [
    #     {
    #         'Key': 'Name',
    #         'Value': instance_name
    #     }
    # ]

    # Create EC2 instance
    instance = ec2.create_instances(
        ImageId=ubuntu_ami_id,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        KeyName=key_pair_name,
        SecurityGroupIds=[security_group_id],
        # TagSpecifications=[
        #     {
        #         'ResourceType': 'instance',
        #         'Tags': tags
        #     }
        # ]
    )

    instance[0].wait_until_running()
    time.sleep(60)
    print ("instance created successfully")
    return instance[0].id  # Return the instance ID





def terminate_ec2_instance(instance_id):
    
    try:
        instance = ec2.Instance(instance_id)
        instance.terminate()
    except Exception as e:
        print(f"Error terminating instance {instance_id}: {str(e)}")





def stop_ec2_instance(instance_id):
    
    try:
        instance = ec2.Instance(instance_id)
        instance.stop()
        print(f"Instance {instance_id} stopped successfully.")
    except Exception as e:
        print(f"Error stopping instance {instance_id}: {str(e)}")





def run_ec2_instance(instance_id):
    
    try:
        instance = ec2.Instance(instance_id)
        instance.start()
        instance.wait_until_running() #######
        time.sleep(60)
        print(f"Instance {instance_id} started successfully.")
    except Exception as e:
        print(f"Error starting instance {instance_id}: {str(e)}")





def assign_iam_role_to_instance(instance_id, iam_role_name):
    """
    Assigns an IAM role to an EC2 instance.

    Args:
    - instance_id (str): The ID of the EC2 instance.
    - iam_role_name (str): The name of the IAM role to be assigned.

    Returns:
    - bool: True if the operation was successful, False otherwise.
    """

    try:
        # Create EC2 client  Frankfurt -> region_name='eu-central-1
        ec2_client = boto3.client('ec2', region_name='eu-central-1') # stockholm eu-north-1

        # Associate IAM role with instance
        response = ec2_client.associate_iam_instance_profile(
            IamInstanceProfile={
                'Name': iam_role_name
            },
            InstanceId=instance_id
        )

        print(f"IAM role '{iam_role_name}' successfully assigned to instance '{instance_id}'.")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    




def add_instance_to_target_group(instance_id, target_group_arn):
    elbv2_client = boto3.client('elbv2')
    
    response = elbv2_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[
            {
                'Id': instance_id,
            },
        ]
    )
    
    print(f"Instance {instance_id} added to target group {target_group_arn}")



