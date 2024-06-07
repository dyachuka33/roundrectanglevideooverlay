import subprocess
import os
import shutil
import json
import random
import time
from PIL import Image

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

def zoom(value):
    crop_width = int(width * value / 100)
    crop_height = int(height * value / 100)

    return f"{width-crop_width}:{height-crop_height}"

options = {
    "blur": {"filter": "boxblur"},
    "rotate": {"filter": "rotate", "format": lambda value: value * (3.141592 / 180)},
    "mirror": {"filter": "hflip", "direct": True},
    "sharpen": {"filter": "unsharp", "format": lambda value: ("3:3:1.5", "5:5:2", "3:3:5", "13:13:2.5", "13:13:5")[value-1]},
    "pad": {"filter": "pad", "format": lambda value: f"width=iw+{value*2}:height=ih+{value*2}:x={value}:y={value}:color=black"},
    "speed": {"filter": "setpts", "format": lambda value: f"{1/value}*PTS"},
    "zoom": {"filter": "crop", "format": zoom},
    "brigthness": {"filter": "eq", "format": lambda value: f"brightness={value}"},
    "contrast": {"filter": "eq", "format": lambda value: f"contrast={value}"},
    "saturation": {"filter": "eq", "format": lambda value: f"saturation={value}"},
    "gamma": {"filter": "eq", "format": lambda value: f"gamma={value}"}
    }   


def generate_ffmpeg_command(input_path, presets, output_path):
    global width, height, duration_t

    is_image = is_image_file(input_path)
    width, height, duration_t = get_video_dimensions(input_path)

    #We need to add extra frames for filters, some filters on hardware needs frames to be fixed.
    command = f'ffmpeg -i "{input_path}" -filter_complex "[0:v]split={len(presets)}{"".join([f"[in{i+1}]" for i in range(len(presets))])};'

    for idx, preset in enumerate(presets, start=1):
        filters = ""

        for i, value in enumerate(preset):
            if value == 0:
                if all(item == 0 for item in preset):
                    filters = "null"
                    break
                continue
                

            option_dict = options.get(list(options.keys())[i])
            filter = option_dict.get("filter")

            if "format" in option_dict:
                filters += f"{filter}={option_dict.get('format')(value)},"
            elif "direct" in option_dict:
                filters += f"{filter},"
            else:
                filters += f"{filter}={value},"

        if filters != "":
            filters = filters[:-1:] if filters[-1] == "," else filters

        command += f"[in{idx}]{filters}[out{idx}];"
        # command += 
    #todo: bitrate control - bvr, crf, cbr - crf is best but hevc_nvenc doesn't support?
    #using 2 pass encoding
    #scaling filter should use the lancz interpolation to improve quality though speed becomes slow
    #brightness testing.
    command = command[:-1:] if command[-1] == ";" else command

    filename = os.path.basename(input_path).split('.')[0]
    if is_image:
        mappings = "".join([f' -map [out{i+1}] -s {width}x{height} "{output_path}{filename}_{i}.png"' for i in range(len(presets))])
    else :
        mappings = "".join([f' -map [out{i+1}] -map 0:a -c:v h264_nvenc -s {width}x{height} -b:v 3500k "{output_path}{filename}_{i}.mp4"' for i in range(len(presets))])

    command = f'{command}"{mappings}'

    return command

def run_ffmpeg_command(command):
    os.system(command)


def is_image_file(file_path):
    try:
        img = Image.open(file_path)
        img.verify()  # Attempt to open and verify the image file
        return True
    except (IOError, SyntaxError):
        return False

def get_presets(json_file):
    mode = 2
    if input("1- Auto create presets\n2- Get presets from json\n>>>") == "1":
        mode = 1
        num_of_presets = int(input("Number of presets:\n>>>"))

        presets = []
        for _ in range(num_of_presets):
            preset = []
            for key, value in json_file["options"].items():
                orange = [int(x) for x in value.split(", ")[1].split("-")]
                preset.append(random.randint(orange[0], orange[1]))
            presets.append(preset)
        json_file["presets"] = presets
    return json_file, mode


def clean_output_folder():
    print("Clearing output folder...")
    shutil.rmtree("output")
    os.mkdir("output/")

def main():
    global config
    
    os.system('cls' if os.name == 'nt' else 'clear')

    config = json.load(open('settings.json', 'r'))
    presets, chosen_mode = get_presets(config)
    if chosen_mode == 2:
        if input("\n1-Use all presets\n2-Use selected number of presets\n>>>") == "2":
            n = int(input("Input number: "))
            preset_list = presets.get("presets")
            presets["presets"] = (preset_list * ((n + len(preset_list) - 1) // len(preset_list)))[:n]

    if presets["clear_output_folder"] == "True":
        clean_output_folder()

    input_path = presets["input_path"] if presets["input_path"][-1] in ["/", "\\"] else presets["input_path"] + "\\"
    files = os.listdir(input_path)
    #files = [x.replace(" ", "").replace("(", "-").replace(")", "-") for x in files_dir]
    
    os.system('cls' if os.name == 'nt' else 'clear')
    topaz = "n"
    resolution = False
    resolution_str = ('*'.join(resolution) if type(resolution) == list else 'Default') + "\n"
    header = f"________________________________________\nInput info:\n    Total videos: {len(files)}\n    Size: {round(sum([os.path.getsize('input/' + f) for f in os.listdir('input/')]) / 1000000, 2)} MB\n    Presets: {len(presets.get('presets'))}\nSettings:\n    Multiprocessing: {'Enabled' if config.get('multiprocessing') == 'True' else 'Disabled'}\n{'        Resolution: ' + resolution_str if config.get('multiprocessing') == 'True' else ''}    AI Enchancing: {'Enabled' if topaz == 'y' else 'Disabled'}\n    Output folder auto clean: {'Enabled' if presets.get('clear_output_folder') == 'True' else 'Disabled'}\n________________________________________"
    print(header)
    exiftool_commands = presets.get("exiftool_commands")
    exiftool_commands_num = len(exiftool_commands)
    for file in files:
        print(f"Processing: {file}")

        path = presets["input_path"] + file

        output_path = f"output/{file.split('.')[0].replace(' ', '_')}/"
        os.mkdir(output_path)

        command = generate_ffmpeg_command(path, presets=presets.get("presets"), output_path=output_path)

        run_ffmpeg_command(command)

        
        if presets["remove_exif"] != "True":
            continue
        output_files = os.listdir(output_path)
        for idx, output_file in enumerate(output_files):
            outfile = output_path + output_file
            try:
                print(f"Removing exif from {outfile}")
                os.system(f"exiftool -all= -overwrite_original {outfile}")
                command = exiftool_commands[idx%exiftool_commands_num]
                command[-1] = outfile
                subprocess.run(command)
            except:
                print("Failed to remove metadata")
                raise RuntimeWarning

    print(header)
    print("All videos Done!")


if __name__ == "__main__":
    main()