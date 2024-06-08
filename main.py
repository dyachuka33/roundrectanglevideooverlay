import json
import subprocess
import os

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
def crop_video(input_file, output_file, size, radius = 0):
    command = ""
    if radius == 0 :
        command = f'ffmpeg -y -i {input_file} -c:v libx264 -preset ultrafast -vf "crop={size["Width"]}:{size["Height"]}" {output_file}'
    else:
        command = f'ffmpeg -y -i {input_file} -c:v libx264 -preset ultrafast -vf "[0:v]crop={size["Width"]}:{size["Height"]}[crop];[crop]format=yuva420p,geq=lum='+"'p(X,Y)':a='if(gt(abs(W/2-X),W/2-20)*gt(abs(H/2-Y),H/2-20),if(lte(hypot(20-(W/2-abs(W/2-X)),20-(H/2-abs(H/2-Y))),20),255,0),255)'"+ f'" {output_file}'
    os.system(command)

#resize video
def resize_video(input_video, output_video, size):
    command = f'ffmpeg -y -i {input_video} -c:v libx264 -preset ultrafast -s {size["Width"]}x{size["Height"]} {output_video}'
    os.system(command)

#first resize and then crop to get the biggest cropped and quality video
def resize_crop_video(input_video, output_video, target_size, radius = 0):
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
    crop_video(temp_file, output_video, target_size, radius)

#overlay overlay_video on top of background_video
def overlay(background_video, overlay_video, output_file):
    background_video_width, background_video_height, background_video_duration = get_video_dimensions(background_video)
    overlay_video_width, overlay_video_height, overlay_video_duration = get_video_dimensions(overlay_video)
    duration = background_video_duration if background_video_duration < overlay_video_duration else overlay_video_duration
    overlay_position_x = int((background_video_width - overlay_video_width) / 2)
    overlay_position_y = int((background_video_height - overlay_video_height) / 2)
    command = f'ffmpeg -y -i {background_video} -i {overlay_video} -filter_complex "[0:v][1:v]overlay={overlay_position_x}:{overlay_position_y}:enable=' + f"'between(t, 0, {duration})'" + f'" -c:v libx264 -preset ultrafast {output_file}'
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
resize_crop_video(overlay_file, temp_overlay_file, overlay_dimension, 40)
overlay(temp_background_file, temp_overlay_file, output_file)

f.close()