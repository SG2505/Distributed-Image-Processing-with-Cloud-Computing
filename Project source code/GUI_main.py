from tkinter import PhotoImage, filedialog
import tkinter
import customtkinter
from PIL import Image
import os
from urllib.parse import urlparse
import webbrowser
from ALB_API import send_image_processing_request
import time
from main_operations import get_unhealthy_instance_ids, count_healthy_instances, get_number_of_instances_in_target_group, get_instances_health
import EC2_API
import asyncio
import threading
from PIL import Image, ImageDraw


# Define scaling parameters
MAX_REQUESTS_BEFORE_SCALING = 5
MAX_NUMBER_OF_INSTANCES = 8
DESIRED_INSTANCE_COUNT = 2
TARGET_GROUP_ARN ='arn:aws:elasticloadbalancing:eu-central-1:851725392781:targetgroup/Image-Processing-Frank-TG/4594d70e60686eda'
IMAGE_PROCESSING_SCRIPT_PATH = 'D:/Distributed Computing/Project/Project source code/image_processing_flask.py'
REMOTE_SCRIPT_PATH = '/home/ubuntu/image_processing_flask_script.py'

REQUESTS_PER_INSTANCE = 3
request_count = 0


my_font_family = 'Cascadia Mono SemiBold'




customtkinter.set_appearance_mode("light")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk() 
app.title('Image Pro')
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
app.geometry(f"{screen_width}x{screen_height}")
upload_icon = customtkinter.CTkImage(Image.open('GUI_needed_files/upload.png'), size=(35,35))
app_image = customtkinter.CTkImage(Image.open('GUI_needed_files/setting_1.png'), size=(50,50))
app_image_label = customtkinter.CTkLabel(master=app,image=app_image, text='')
app_image_label.place(x=10,y=10)
my_font = customtkinter.CTkFont(family=my_font_family,size=16, weight="bold")
my_font_family_customrkinter = customtkinter.CTkFont(family=my_font_family, weight="bold")
imagePro_label = customtkinter.CTkLabel(master=app, text='Image Pro', font=my_font)
imagePro_label.place(x=65,y=32)


ALB_operations = {'Color Inversion':'color_inversion','Grayscale':'grayscale', 'Blur':'blur','Edge Detection':'edge_detection', 'Thresholding':'thresholding','Line Detection':'line_detection', 'Frame Contour Detection':'frame_contour_detection', 'Morphological operations':'morphological_operations'}
filenames=[]
recent_images = {}
####################### RIGHT FRAME #########################
def upload_images():
    global filenames
    filenames = list(filedialog.askopenfilenames(multiple=True))
    if len(filenames) == 1:
        display_single_image(filenames[0])
        uplaod_frame.pack(expand=True)
        upload_btn.pack_forget()
        remove_button.pack_forget()
        remove_button.pack(expand=True)
        inner_frame2.pack_forget()
        inner_frame2.pack(expand=True)
    elif len(filenames) > 1:
        display_multiple_images(filenames)
        uplaod_frame.pack(expand=True)
        remaining_label.pack()
        upload_btn.pack_forget()
        remove_button.pack(expand=True)
        inner_frame2.pack_forget()
        inner_frame2.pack(expand=True)
        


def display_single_image(filename):
  # Load the image and resize if needed]
  image = customtkinter.CTkImage(Image.open(filename), size=(230,230))
  # Display image in the frame
  upload_label.configure(image=image,text='')
  upload_label.image = image  # Keep a reference to avoid garbage collection

def display_multiple_images(filenames):
  # Display first image and indicate remaining count
    image = customtkinter.CTkImage(Image.open(filenames[0]), size=(230,230)) 

    upload_label.configure(image=image,text='')
    upload_label.image = image
    remaining_count = len(filenames) - 1
    remaining_label.configure(text=f"+{remaining_count} other images",font=remaining_label_font)

def remove_images():
    global filenames
    remove_button.pack_forget()
    uplaod_frame.pack_forget()
    inner_frame2.pack_forget()
    remaining_label.pack_forget()
    upload_btn.pack(expand=True)
    inner_frame2.pack(expand=True)
    filenames.clear()

def show_popup(message):
  # Create a popup window
  popup = customtkinter.CTkToplevel(master=app, fg_color="black")
  popup.attributes('-topmost', True)
  popup.title("Error!")
  popup.geometry('300x150+500+300')  # Set size

  # Label within the popup
  label = customtkinter.CTkLabel(popup, text=message, text_color="white")
  label.place(relx=0.5,rely=0.3, anchor=customtkinter.CENTER)

  # Button to close the popup
  close_button = customtkinter.CTkButton(popup, text="Close", command=popup.destroy)
  close_button.place(relx=0.5,rely=0.5,anchor=customtkinter.CENTER)


async def apply_operation_async():
    await Apply_operation(operations.get())

def apply_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(apply_operation_async())

def apply_async_thread():
    thread = threading.Thread(target=apply_async)
    thread.start()


async def Apply_operation(operation):
        
  global request_count, filenames


  progress_bar.set(0)
  if len(filenames) == 0:
    show_popup('Please choose an image to upload.')
    return
  
  elif operation == '':
    show_popup("Please choose an operation.")
    return
  
  uplaod_frame.pack_forget()
  inner_frame2.pack_forget()
  remove_button.pack_forget()
  remaining_label.pack_forget() 
  upload_btn.pack(expand=True)
  # remove_button.pack(expand=True)
  inner_frame2.pack(expand=True)
  progress_label.configure(text="Progress 0%")

  if len(filenames) == 1:
    progress_bar.configure(mode="indeterminate",indeterminate_speed=0.5)
    progress_bar.start()
    progress_label.configure(text=f'Progress ...')

  else:
      progress_bar.configure(mode="determinate", determinate_speed=0.7)
      step_size = round(1/len(filenames), 2)
      step_size2=0
      
      

  s3_bucket='dist-frank-proj'
  
  
  for file in filenames:
      
    image_url = urlparse(file)                   
    image_name = operation + '_' + os.path.basename(image_url.path)  
    download_link , instance_id = await send_image_processing_request(file, ALB_operations[operation], image_name, s3_bucket)
    recent_images[image_name]= download_link
    image_name_1 = image_name.split('_')[1]
    add_recent_images(image_name_1, operation, download_link)
    add_to_log(f"image: {image_name_1} sent to instance: {instance_id}")

    
    if len(filenames) > 1:
      step_size2 += step_size
      progress_bar.set(step_size2)
      progress_level = int(round(step_size2*100, 0))
      progress_label.configure(text=f'Progress {progress_level}%')
    

    request_count +=1
  
  if len(filenames) == 1:
      progress_bar.configure(mode="determinate")
      progress_bar.stop()
      
  progress_label.configure(text='Progress 100%')

  progress_bar.set(1)

  print(request_count)
  filenames.clear()
    


def operation_selected(operation):
    operations.configure(fg_color="#244b83", text_color="white")
    

frame1 = customtkinter.CTkFrame(master=app ,width=300,height=600,border_width=1,corner_radius=15,fg_color='#f2f2f2')
frame1.pack(side='right',padx=40)
frame1.pack_propagate(False)
remove_button = customtkinter.CTkButton(master = frame1,text='Remove Images', font= my_font_family_customrkinter, text_color='black',width=200, height=35,fg_color='#8ebcff', corner_radius=20, command=lambda: remove_images())
upload_btn = customtkinter.CTkButton(master = frame1,text='Upload Image',font= my_font_family_customrkinter,image=upload_icon,compound='top' ,text_color='black' ,width=250, height=250,fg_color='#8ebcff', corner_radius=15, command=upload_images)
uplaod_frame = customtkinter.CTkFrame(master = frame1, width=250, height=260,fg_color='#8ebcff',corner_radius=15)
uplaod_frame.pack_propagate(False)
upload_label = customtkinter.CTkLabel(master=uplaod_frame,text='')
upload_label.pack(pady=10)
remaining_label = customtkinter.CTkLabel(master=frame1,text='')
remaining_label_font= customtkinter.CTkFont(family=my_font_family, weight='bold',size=14)
# remaining_label.pack()
inner_frame2 = customtkinter.CTkFrame(master = frame1, width=250, height=150,fg_color='#8ebcff',corner_radius=15)

# **Centering the inner frames:**
# Use `pack` with `expand=True` for both frames
upload_btn.pack(expand=True)
inner_frame2.pack(expand=True)
inner_frame2.pack_propagate(False)

operation_label = customtkinter.CTkLabel(master=inner_frame2, text='Choose Operation', font= my_font_family_customrkinter)
operation_label.pack(anchor='nw',padx=10, pady=5)
operation_values = ['Color Inversion','Grayscale', 'Blur','Edge Detection', 'Thresholding','Line Detection', 'Frame Contour Detection', 'Morphological operations']
operations = customtkinter.CTkComboBox(master =inner_frame2, width = 200, height=35, values=operation_values,corner_radius=15, state='readonly', command=operation_selected )
operations.pack(expand = True)



    
Apply_button = customtkinter.CTkButton(master=inner_frame2,text='Apply',font= my_font_family_customrkinter, width=200,height=35,corner_radius=20,fg_color='#3e3c3c', command= apply_async_thread)
Apply_button.pack(expand=True)


############################ END OF RIGHT FRAME ##################################


instnaces_font = customtkinter.CTkFont(family=my_font_family,size=14, weight="bold", underline=True)
instances_number_label = customtkinter.CTkLabel(master=app,text="Total VMs: 0", font=instnaces_font)
instances_number_label.place(x=60,y=90)

########################## FRAME THAT HOLDS THE MACHINES STATUES ###########################
machines_frame = customtkinter.CTkScrollableFrame(master=app ,width=1050,height=175,fg_color="#f2f2f2",border_width=1,corner_radius=15,orientation='horizontal')
machines_frame.place(x=55, y=123)

########################## END OF FRAME THAT HOLDS THE MACHINES STATUES ###########################



######################### PROGRESS BAR ##############################
progress_bar = customtkinter.CTkProgressBar(master=app, width=1085, height=10, progress_color="#244b83",mode='determinate')
progress_bar.set(0)
progress_label = customtkinter.CTkLabel(master=app,text="Progress 0%", font = my_font_family_customrkinter)
progress_bar.place(x=52,y=390)
progress_label.place(x=52,y=360)

my_font2 = customtkinter.CTkFont(family=my_font_family,size=18, weight="bold")
receent_label = customtkinter.CTkLabel(master=app, text="Recent Images",font=my_font2)
receent_label.place(x=655,y=445)

my_font_logs = customtkinter.CTkFont(family=my_font_family,size=13, weight="bold")
######################### END OF PROGRESS BAR ##############################



######################## FRAME THAT HOLDS THE RECENT IMAGES ##########################
recent_frame= customtkinter.CTkScrollableFrame(master=app, width=450,height=200, border_width=1,corner_radius=15, fg_color='#f2f2f2')
recent_frame.place(x=650,y=480)
recent_frame_label = customtkinter.CTkLabel(master=recent_frame, text="No Processed images yet...",font=my_font2, text_color="#c9c5c5")
recent_frame_label.pack(anchor=customtkinter.CENTER,  fill=customtkinter.X, expand=False, side="top", pady=90)


logs_frame= customtkinter.CTkScrollableFrame(master=app, width=550,height=200, border_width=1,corner_radius=15, fg_color='#f2f2f2')
logs_frame.place(x=50,y=480)
logs_frame_label = customtkinter.CTkLabel(master=logs_frame, text="No Logs yet...", font=my_font2, text_color="#c9c5c5")
logs_frame_label.pack(anchor=customtkinter.CENTER, fill=customtkinter.X, expand=False, side="top", pady=90)  
logs_label = customtkinter.CTkLabel(master=app, text="Logs",font=my_font2)
logs_label.place(x=55,y=445)


   


def add_to_log(message_log):

  if logs_frame_label.winfo_exists():
     logs_frame_label.destroy()

  log_text_frame= customtkinter.CTkFrame(master=logs_frame,width=520,height=50,corner_radius=15,border_width=1,fg_color='#244b83')
  log_text_frame.pack_propagate(False)
  log_text_frame.pack(expand=True,pady=10)
  log = customtkinter.CTkLabel(master=log_text_frame, text=message_log,font=my_font_logs, text_color="white")
  log.pack(expand=True, side="left")



gallery_image = customtkinter.CTkImage(Image.open('GUI_needed_files/photo.png'), size=(32,32))
download_image = customtkinter.CTkImage(Image.open('GUI_needed_files/downloading.png'), size=(32,32))

def add_recent_images(image_name, operation, download_link):

  if recent_frame_label.winfo_exists():
    recent_frame_label.destroy()

  download_frame= customtkinter.CTkFrame(master=recent_frame ,width=420,height=50,corner_radius=15,border_width=1,fg_color='#8ebcff')
  download_frame.pack(expand=True,pady=10)
  gallery_label = customtkinter.CTkLabel(master=download_frame,image=gallery_image, text="")
  gallery_label.place(x=7,y=7)
  imagenumber_label = customtkinter.CTkLabel(master=download_frame, text=image_name)
  imagenumber_label.place(x=45,y=10)
  operation_done_label = customtkinter.CTkLabel(master=download_frame, text=operation)
  operation_done_label.place(x=180,y=10)
  download_button = customtkinter.CTkButton(master = download_frame,text='',image=download_image, width=5,height=32,fg_color='#8ebcff',border_spacing=0,hover=False , command=lambda: webbrowser.open(download_link))
  download_button.place(x= 365, y = 7)
######################## END OF FRAME THAT HOLDS THE RECENT IMAGES ##########################
  



def are_not_dicts_equal(dict1, dict2):
    """
    Check if two dictionaries are equal.

    Args:
    - dict1 (dict): First dictionary.
    - dict2 (dict): Second dictionary.

    Returns:
    - bool: True if dictionaries are equal, False otherwise.
    """
    if len(dict1) != len(dict2):
        return True

    for key, value in dict1.items():
        if key not in dict2 or dict2[key] != value:
            return True

    return False






def update_health_dictionary():

    global global_all_instances_health
    old_dict_instances = {}

    while True:
    
        global_all_instances_health = get_instances_health(TARGET_GROUP_ARN)
        print(global_all_instances_health)

        if are_not_dicts_equal(old_dict_instances,global_all_instances_health):

          i = len(list(global_all_instances_health.keys()))

          instances_number_label.configure(text=f"Total VMs: {len(list(global_all_instances_health.keys()))}")

          for widget in machines_frame.winfo_children():

            try:
                widget.destroy()
            except Exception as e:
                print("error")
                print(e)

          for instance_id, health_status in global_all_instances_health.items():

            frame_state1 = customtkinter.CTkFrame(master=machines_frame ,width=150,height=150,fg_color="#f2f2f2")
            frame_state1.pack(side='right',padx=55)
            cloud_icon1 = customtkinter.CTkImage(Image.open('GUI_needed_files/cloud-server.png'), size=(100,100))
            cloud_label1 = customtkinter.CTkLabel(master=frame_state1,image=cloud_icon1, text='')
            cloud_label1.pack()

            # Create labels for instance ID and health status separately
            instance_name = customtkinter.CTkLabel(master=frame_state1, text=f'VM {i}', font= my_font_family_customrkinter)
            instance_id_label = customtkinter.CTkLabel(master=frame_state1, text=f'ID: {instance_id}', font= my_font_family_customrkinter)
            health_status_label = customtkinter.CTkLabel(master=frame_state1, text=f'Status: {health_status}', font= my_font_family_customrkinter)

            
            instance_name.pack()
            instance_id_label.pack()
            health_status_label.pack()
            i -=1

            
        old_dict_instances = global_all_instances_health
        #GUI update status and machines
        time.sleep(15)








def add_instance_to_target():
    new_instance_id = EC2_API.create_ec2_instance()  # Create new instances
    add_to_log(f"configuring {new_instance_id} instance...")
    EC2_API.assign_iam_role_to_instance(new_instance_id, 'S3-Access')
    ssh = EC2_API.initialize_ssh_connection(new_instance_id)
    EC2_API.execute_ssh_commands(ssh)
    EC2_API.modify_instance_metadata_options(new_instance_id)
    add_to_log(f"adding {new_instance_id} instance to target group...")
    EC2_API.add_instance_to_target_group(new_instance_id, TARGET_GROUP_ARN)
    EC2_API.upload_file(IMAGE_PROCESSING_SCRIPT_PATH, REMOTE_SCRIPT_PATH, ssh)
    add_to_log(f"executing Script on {new_instance_id} instance...")
    EC2_API.execute_remote_script(REMOTE_SCRIPT_PATH, ssh)






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
            print(f"Terminating unhealthy instance {instance_id}...")
            add_to_log(f"Terminating unhealthy instance {instance_id}...")
            EC2_API.terminate_ec2_instance(instance_id)
            print(f"Instance {instance_id} terminated successfully.")
            # add_to_log(f"Instance {instance_id} terminated successfully.")
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
                
                add_to_log(f"Terminating instance {list(all_instances_health.keys())[i]} for scaling down...")
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

            add_to_log(f"creating {actual_desired_instances} new instance(s) for scaling up...")
        
        

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
                add_to_log(f"creating {instances_needed} new instance(s) for fault tolerance...")
                    

            elif (healthy_instances_count < existing_instances_count) and (existing_instances_count < MAX_NUMBER_OF_INSTANCES):   
                instances_needed = max(0, existing_instances_count - healthy_instances_count)
                if instances_needed != 0:
                    Fault_Tolerance_flag = True

                print(f"instance needed in fault tolerance = {instances_needed}")
                for _ in range(instances_needed):
                    
                    instance_fault_thread = threading.Thread(target=add_instance_to_target)
                    instance_fault_thread.start()
                add_to_log(f"creating {instances_needed} new instance(s) for fault tolerance...")


                
        if Fault_Tolerance_flag or Auto_Scaling_flag:
            request_count = 0
            Fault_Tolerance_flag = Auto_Scaling_flag = False
            time.sleep(400)  # wait until instances created, add to target group and become healthy
        
        else:
            request_count = 0
            time.sleep(60)






Health_thread = threading.Thread(target=update_health_dictionary)
Health_thread.start()

Scale_and_fault_thread = threading.Thread(target=auto_scaling_and_Fault_tolerance)
Scale_and_fault_thread.start()

try:
    app.mainloop()
except Exception as e:
    pass 