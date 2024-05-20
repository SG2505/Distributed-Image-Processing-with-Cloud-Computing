from flask import Flask, request, jsonify
import requests
import cv2
import boto3
import numpy as np
import traceback
import os


app = Flask(__name__)



@app.route('/health')
def health_check():
    # Perform any necessary health checks here
    # Return a successful response if the application is healthy
    return 'OK', 200



@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        # Check if the request contains a file
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        # Get the image file from the request
        image_file = request.files['image']

        # Read the image file using OpenCV
        image = cv2.imdecode(np.fromstring(image_file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Get other request parameters
        operation = request.form['operation']
        output_image_name = request.form['output_name']
        s3_bucket_name = request.form['s3_bucket']

        # Get instance ID
        instance_id = get_instance_id()

        # Perform image processing
        output_image_path = f'/home/ubuntu/{output_image_name}'
        image_processing(image, output_image_path, operation)

        # Upload processed image to S3
        s3_key = f'processed_images/{output_image_name}'
        upload_to_s3(output_image_path, s3_bucket_name, s3_key)

        # Get download link for processed image
        download_link = get_s3_download_link(s3_bucket_name, s3_key)

        return jsonify({'download_link': download_link, 'Instance_ID': instance_id}), 200

    except Exception as e:
        # Log error and return internal server error
        print("Error processing image:", e)
        traceback.print_exc()  # Print detailed traceback
        return jsonify({'error': 'Internal Server Error'}), 500



def image_processing(image, output_image_path, operation):

    try:
        processed_image = None

        # Perform the specified operation
        if operation == 'color_inversion':
            processed_image = cv2.bitwise_not(image)
        elif operation == 'grayscale':
            processed_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif operation == 'blur':
            processed_image = cv2.GaussianBlur(image, (15, 15), 0)
        elif operation == 'edge_detection':
            processed_image = cv2.Canny(image, 100, 200)  # Perform edge detection
        elif operation == 'thresholding':
            _, processed_image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)


        ##### advanced image processing ######
        elif operation == 'line_detection':

            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=200)

            # Check if any lines are detected
            if lines is not None:
                for line in lines:
                    rho, theta = line[0]
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a * rho
                    y0 = b * rho
                    x1 = int(x0 + 1000 * (-b))
                    y1 = int(y0 + 1000 * (a))
                    x2 = int(x0 - 1000 * (-b))
                    y2 = int(y0 - 1000 * (a))

                    cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
            else:
                print("No lines detected.")
            processed_image = image


        elif operation == 'frame_contour_detection':

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contourImage = image.copy()
            cv2.drawContours(contourImage, contours, -1, (0, 255, 0), 2)
            processed_image = contourImage
            
        elif operation == 'morphological_operations':

            dilation_kernel_size=5
            erosion_kernel_size=5
            opening_iterations=1
            closing_iterations=1

            dilation_kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
            opening_kernel = np.ones((erosion_kernel_size, erosion_kernel_size), np.uint8)
            closing_kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)

            dilated_image = cv2.dilate(image, dilation_kernel, iterations=1)
            opened_image = cv2.morphologyEx(dilated_image, cv2.MORPH_OPEN, opening_kernel, iterations=opening_iterations)
            processed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, closing_kernel, iterations=closing_iterations)
            

        else:
            raise ValueError("Invalid operation specified.")


        # Check if processed_image is None
        if processed_image is None:
            raise ValueError("Image processing failed. No processed image.")

        # Write the processed image to disk
        cv2.imwrite(output_image_path, processed_image)

    except Exception as e:
        # Log error and re-raise exception
        print("Error in image processing:", e)
        traceback.print_exc()  # Print detailed traceback
        raise


def upload_to_s3(local_file_path, bucket_name, s3_key):
    try:
        # Upload the file to S3
        s3 = boto3.resource('s3')
        s3.Bucket(bucket_name).upload_file(local_file_path, s3_key)
    except Exception as e:
        # Log error and re-raise exception
        print("Error uploading to S3:", e)
        traceback.print_exc()  # Print detailed traceback
        raise



# Function to get EC2 instance ID
def get_instance_id():
    try:
        # Make an HTTP GET request to retrieve the instance ID
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
        if response.status_code == 200:
            return response.text
        else:
            return None
        
    except Exception as e:
        # Log error and return None
        print("Error getting instance ID:", e)
        traceback.print_exc()  # Print detailed traceback
        return None



def get_s3_download_link(bucket_name, s3_file_path):
    return f'https://{bucket_name}.s3.amazonaws.com/{s3_file_path}'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
