import boto3

# Create S3 client
s3_client = boto3.client('s3')





def S3_create_bucket(name):

    if str(name).islower():

        # Specify the bucket name
        bucket_name = name

        # Specify the location constraint for the bucket (if necessary)
        location_constraint = {'LocationConstraint': 'eu-central-1'} # stockholm eu-north-1

        # Create S3 bucket with the specified location constraint
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location_constraint)


        print(f'S3 bucket {bucket_name} has been created.')
    
    else:
        print('bucket name should be in lowercase')


def S3_delete_bucket(name):

    # Specify the name of the bucket to delete
    bucket_name = name

    # Delete the bucket
    s3_client.delete_bucket(Bucket=bucket_name)

    print(f'S3 bucket {bucket_name} has been deleted.')


def S3_upload_file(bucket_name,folder_name, file_path, file_name):


    # Upload the file to the folder in the S3 bucket
    s3_client.upload_file(file_path, bucket_name, folder_name + file_name)

    print(f'File {file_name} uploaded to folder {folder_name} in bucket {bucket_name}.')


def S3_download_file(bucket_name, path_to_file, local_file_path):

    # Download the image from the S3 bucket
    s3_client.download_file(bucket_name, path_to_file, local_file_path)

    print(f'Image downloaded from S3 bucket to {local_file_path}.')


def S3_delete_directory_objs(bucket_name, folder_prefix):

    # List objects in the "folder" prefix
    objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

    # Delete each object in the "folder" prefix
    for obj in objects.get('Contents', []):
        s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

    print(f'Objects within folder {folder_prefix} deleted from bucket {bucket_name}.')



def S3_delete_file(bucket_name, file_path):

    # Delete the file from the S3 bucket
    s3_client.delete_object(Bucket=bucket_name, Key=file_path)

    print(f'File {file_path} deleted from bucket {bucket_name}.')