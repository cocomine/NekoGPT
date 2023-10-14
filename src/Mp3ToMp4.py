import os
import subprocess


def convert(file_name: str, target_file_name: str, image_file_name: str = "image.png"):
    """
    convert mp3 to mp4
    :param file_name: Input file name
    :param target_file_name: Target file name
    :param image_file_name: Image file name
    """
    # convert mp3 to mp4
    subprocess.run(f"ffmpeg -y -loop 1 -framerate 1 -i {image_file_name} -i {file_name} -map 0:v -map 1:a -r 10 -vf "
                   f"\"scale='iw-mod(iw,2)':'ih-mod(ih,2)',format=yuv420p\" -movflags +faststart -shortest -fflags "
                   f"+shortest -max_interleave_delta 100M {target_file_name}", shell=True)
    # remove mp3
    os.remove(file_name)
