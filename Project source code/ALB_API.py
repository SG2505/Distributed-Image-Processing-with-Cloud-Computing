import aiohttp
import asyncio
import os
import json




async def send_image_processing_request(image_path, operation, output_name, s3_bucket):
    # Load balancer URL
    load_balancer_url = 'http://Image-Processing-ALB-960172611.eu-central-1.elb.amazonaws.com/process_image' 

    # Read the image file
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    # Request data
    request_data = aiohttp.FormData()
    request_data.add_field('image', image_data, filename = os.path.basename(image_path))
    request_data.add_field('operation', operation)
    request_data.add_field('output_name', output_name)
    request_data.add_field('s3_bucket', s3_bucket)

    async with aiohttp.ClientSession() as session:
        async with session.post(load_balancer_url, data=request_data) as response:
            if response.status == 200:
                print("Image processing request sent successfully to the load balancer.")
                
                response_json = await response.json()  # Parse JSON response
                download_link = response_json.get('download_link')  # Extract download link
                instance_id = response_json.get('Instance_ID')  # Extract instance id

                if download_link:
                    print(f"Download link: {download_link}")
                else:
                    print("Failed to get download link from the response.")

                if instance_id:
                    print(f"Instance ID: {instance_id}")
                else:
                    print("Failed to get instance id from the response.")
                
                return download_link, instance_id
                
                
            else:
                error_message = await response.text()
                print(f"Failed to send image processing request to the load balancer. Error: {error_message}")


# async def main():
#     await send_image_processing_request(
#         image_path='C:/Users/oem/Downloads/store.png',
#         operation='grayscale',
#         output_name='grayScaled.png',
#         s3_bucket='dist-frank-proj'
#     )

# #     # await send_image_processing_request(
# #     #     image_path='C:/Users/oem/Downloads/sudoku.png',
# #     #     operation='blur',
# #     #     output_name='blured.png',
# #     #     s3_bucket='dist-frank-proj'
# #     # )
    
# #     # await send_image_processing_request(
# #     #     image_path='C:/Users/oem/Downloads/sudoku.png',
# #     #     operation='line_detection',
# #     #     output_name='LineDetected.png',
# #     #     s3_bucket='dist-frank-proj'
# #     # )

# #     # await send_image_processing_request(
# #     #     image_path='C:/Users/oem/Downloads/sudoku.png',
# #     #     operation='frame_contour_detection',
# #     #     output_name='frameDetected.png',
# #     #     s3_bucket='dist-frank-proj'
# #     # )
    
# #     # await send_image_processing_request(
# #     #     image_path='C:/Users/oem/Downloads/sudoku.png',
# #     #     operation='morphological_operations',
# #     #     output_name='morphological.png',
# #     #     s3_bucket='dist-frank-proj'
# #     # )

    

# # Run the asynchronous function
# asyncio.run(main())
