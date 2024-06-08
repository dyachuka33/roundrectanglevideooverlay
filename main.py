import json
import subprocess
import os

#delete all files
def delete_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    except OSError:
        print("Error occurred while deleting files.")
#get the width, height and duration of the video
def get_video_dimensions(file_path):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration',
        '-of', 'json',
        file_path
    ]

    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    width = data['streams'][0]['width']
    height = data['streams'][0]['height']
    duration = data['streams'][0]['duration']

    return width, height, duration

#crop input video which has size dimention from central part
def crop_video(input_file, output_file, size):
    command = f'ffmpeg -y -i {input_file} -c:v libx264 -preset ultrafast -vf "crop={size["Width"]}:{size["Height"]}" {output_file}'
    os.system(command)

#resize video
def resize_video(input_video, output_video, size):
    command = f'ffmpeg -y -i {input_video} -c:v libx264 -preset ultrafast -s {size["Width"]}x{size["Height"]} {output_video}'
    os.system(command)

#first resize and then crop to get the biggest cropped and quality video
def resize_crop_video(input_video, output_video, target_size):
    temp_file = "./temp/temp.mp4"
    input_width, input_height, _ = get_video_dimensions(input_video)
    width_ratio = target_size["Width"]/input_width
    height_ratio = target_size["Height"]/input_height
    ratio = width_ratio if width_ratio < height_ratio else height_ratio
    resize_width = int((input_width * ratio + 15) / 16 ) * 16
    resize_height = int ((input_height * ratio + 15) / 16 ) * 16
    resize_size = {
        "Width": resize_width,
        "Height": resize_height
    }
    resize_video(input_video, temp_file, resize_size)
    crop_video(temp_file, output_video, target_size)

#overlay overlay_video on top of background_video
def overlay_round_video(background_video, overlay_video, output_file, radius=0):
    background_video_width, background_video_height, _ = get_video_dimensions(background_video)
    overlay_video_width, overlay_video_height, _ = get_video_dimensions(overlay_video)

    overlay_position_x = int((background_video_width - overlay_video_width) / 2)
    overlay_position_y = int((background_video_height - overlay_video_height) / 2)
    command = f'ffmpeg -y -i {background_video} -i {overlay_video} -c:v libx264 -preset ultrafast -filter_complex "[1:v]format=yuva420p,geq=lum='+f"'p(X,Y)':a='if(gt(abs(W/2-X),W/2-{radius})*gt(abs(H/2-Y),H/2-{radius}),if(lte(hypot({radius}-(W/2-abs(W/2-X)),{radius}-(H/2-abs(H/2-Y))),{radius}),255,0),255)'[overlay];[0:v][overlay]overlay=x={overlay_position_x}:y={overlay_position_y}" + f'" {output_file}'
    os.system(command)


f = open("settings.json")
settings = json.load(f)
input_file = settings["InputFile"]
overlay_file = settings["OverlayFile"]
output_file = settings["OutputFile"]
output_dimension = settings["OutputDimension"]
overlay_dimension = settings["OverlayDimension"]

temp_background_file = "./temp/background_file.mp4"
temp_overlay_file = "./temp/overlay.mp4"


resize_crop_video(input_file, temp_background_file, output_dimension)
resize_crop_video(overlay_file, temp_overlay_file, overlay_dimension)
overlay_round_video(temp_background_file, temp_overlay_file, output_file, 32)
delete_files_in_directory('./temp')
f.close()