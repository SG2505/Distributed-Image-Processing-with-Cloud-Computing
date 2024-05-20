# Distributed Image Processing Cloud Project

<div align ="center">
  <img src="Project%20source%20code/GUI_needed_files/Image_Pro.png" alt="Logo"/>
</div>

## Overview

The Image Processing Cloud Project leverages the power of cloud computing to provide scalable and efficient image processing services. This project is designed to process images through app UI, utilizing multiple virtual machines (VMs) for distributed processing. It supports various operations such as grayscale conversion, blurring, line detection, and morphological operations.

## Demo

Check out our [YouTube demo](https://youtu.be/1xnuI-0nm1c) to see the project in action across several VMs and computers.

<div align ="center">
  <a href="https://youtu.be/1xnuI-0nm1c" target="_blank" title="Demo video link">
    <img src="Project%20source%20code/GUI_needed_files/Image_Demo_Video.png" alt="Demo video link" title="Demo video link"/>
  </a>
</div>

## Features

- **Fault Tolerance**: Automatically detects unhealthy, Terminated, or unused VMs and compensates by creating additional sufficient VMs.
- **Scalable Processing**: Dynamically scales to handle multiple image processing requests simultaneously.
- **Distributed Computing**: Utilizes multiple VMs for efficient processing.
- **User-Friendly Interface**: Easy-to-use GUI built with CustomTkinter.
- **Various Image Operations**: Supports grayscale, blur, line detection, and more.

## Installation

### Prerequisites

- Python 3.8+
- AWS account with necessary permissions
- CustomTkinter library
- aiohttp library
- boto3 library

### Setup

1. Clone the repository

    ```bash
    git clone https://github.com/Etsh20P/Distributed-Image-Processing-Project.git
    cd "Project source code"
    ```

2. Install the required Python packages

    ```bash
    pip install customtkinter
    pip install aiohttp
    pip install boto3

    ```

## Running the Project

### Running Locally

1. **Start the GUI application**

    ```bash
    python GUI_main.py
    ```

2. **Start and run the 2 initial VMs in the system and execute the script on them (execute this code in main_operation.py file)**

    ```python
    EC2_API.run_ec2_instance('i-i-0e46dff152f7d1361')
    ssh = EC2_API.initialize_ssh_connection('i-0e46dff152f7d1361')
    EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH,ssh)
    
    EC2_API.run_ec2_instance('i-004ebd25392d71168')
    ssh = EC2_API.initialize_ssh_connection('i-004ebd25392d71168')
    EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH,ssh)
    ```

3. **Wait until they're running and healthy in the target group**

    Check the AWS Target group console.


4. **Open the Application**

    The GUI should now be running and accessible for image processing operations.

### Running on AWS

1. **Deploy the Flask Server**

    Deploy the `image_processing_flask.py` script on your EC2 instances.

2. **Configure Load Balancer**

    Set up an AWS Application Load Balancer to distribute the requests to your EC2 instances by creating the load balancer from the AWS console
    and wait until it's active, then copy its DNS and paste it into the load_balancer_url variable in the ALB_API.py file.

3. **Run the Main Application**

    Start the main GUI application and interact with the load-balanced Flask servers for processing.

## Usage

### Image Processing Requests

  ```python
  import ALB_API

  # Send a processing request
  download_link, instance_id = await ALB_API.send_image_processing_request(
      image_path='path/to/image.png',
      operation='grayscale',
      output_name='output_image.png',
      s3_bucket='your-s3-bucket'
  )

  print(f"Download link: {download_link}")
  print(f"Processed by Instance ID: {instance_id}")
  ```

### Health Check

  ```python
  from main_operations import get_instances_health

  global_all_instances_health = get_instances_health(TARGET_GROUP_ARN)
  print(global_all_instances_health)
  ```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Ensure any changes are well-documented and tested.


