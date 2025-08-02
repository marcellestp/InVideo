from flask import Flask, request, render_template, redirect, url_for, flash
from functools import wraps
from exif import Image
from glob import glob
from moviepy import *
from werkzeug.utils import secure_filename
import imagesize
import multiprocessing
import os
# import pyautogui
import time


app = Flask(__name__)

# Define a secret key for Flask
app.secret_key = "your_secret_key_here"

# Specify a directory to store uploaded files -- TODO Acrescentar a sessao do user
UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Increase the server timeout value to 300 seconds  -  comecou apresentar a mensagem 413 Request Entity Too Large
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300

# Will limit the maximum allowed payload to 16 megabytes. If a larger file is transmitted, Flask will raise a RequestEntityTooLarge exception.
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

height_default = 1080
clips = []
files_path = os.path.join(app.config['UPLOAD_FOLDER'])
path_video_temp = "static/out_temp.mp4"
path_video = "static/output.mp4"

# Create the uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Make crop on images greater then 1920 x 1080
def crop_image(img_height, img_width, file):

    # Vertical image
    if img_height > img_width:
        width_default = 1080
        clip = ImageClip("images/" + file)
        clip = clip.with_effects([vfx.Resize(height=height_default)])
        new_width, new_height = clip.size
        new_height_center = new_height / 2
        y1_pos = new_height_center - (height_default / 2)
        y2_pos = new_height_center + (height_default / 2)
        clip = clip.with_effects([vfx.Crop(x1=0, y1=y1_pos, x2=width_default, y2=y2_pos)])
    else:
        # Horizonte image
        width_default = 1920
        clip = ImageClip("images/" + file)
        clip = clip.with_effects([vfx.Resize(width=width_default)])
        new_width, new_height = clip.size
        new_height_center = new_height / 2
        y1_pos = new_height_center - (height_default / 2)
        y2_pos = new_height_center + (height_default / 2)
        clip = clip.with_effects([vfx.Crop(x1=0, y1=y1_pos, x2=width_default, y2=y2_pos)])

    return clip


def upload_files():
    if request.method == 'POST':
        # Get the list of uploaded files
        files = request.files.getlist('file[]')
        if files:
            # Save each file to the uploads directory
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename.lower()))
            # return 'Files uploaded successfully.'
        else:
            return 'No files uploaded.'

    # return render_template('index.html')


def process_video():
    clips = []
    TIME = 3
    FADEIN_TIME = 0.2
    FADEOUT_TIME = 0.2
    FULL_HD = 1920
    ratio_hd = round(1920 / 1080, 2)
    # LAMBDA_EFFECT = lambda t : 1+0.02*t

    # Using sorted to sort the list of files
    # https://docs.python.org/3/howto/sorting.html
    for file in sorted(os.listdir("images/")):
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            with open("images/" + file, "rb") as image_file:
                file_exif = Image(image_file)
                try:
                    img_height = file_exif.image_height
                    img_width = file_exif.image_width
                except AttributeError:
                    img_width, img_height = imagesize.get("images/" + file)
                except KeyError:
                    img_width, img_height = imagesize.get("images/" + file)

                # Check the aspect ratio, and if diff of 1.77, crop the image
                ratio = round(img_height / img_width, 2)
                if ratio != ratio_hd:
                    clip = crop_image(img_height, img_width, file)

                if file_exif.has_exif:
                    try:

                        if (file_exif.orientation == 1 or file_exif.orientation == 2):
                            clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                        elif (file_exif.orientation == 6 or file_exif.orientation == 7):
                            clip = clip.with_duration(TIME)
                            clip = clip.with_effects([vfx.Resize(width=1080)])
                            clip = clip.with_effects([vfx.Rotate(270)])
                            clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
                            clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
                            # clip = clip.with_effects([vfx.Resize(LAMBDA_EFFECT)])
                            clips.append(clip)

                        elif (file_exif.orientation == 5 or file_exif.orientation == 8):
                            clips.append(clip.with_duration(TIME).with_effects([vfx.Resize(width=1080), vfx.Rotate(90), vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                        elif (file_exif.orientation == 3 or file_exif.orientation == 4):
                            clips.append(clip.with_duration(TIME).with_effects([vfx.Resize(width=1080), vfx.Rotate(180), vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                        else:
                            clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                    except AttributeError:
                        clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                    except ValueError:
                        clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))

                else:
                    clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))

        # If video
        if file.endswith(".mp4"):
            clip = VideoFileClip("images/" + file)
            clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
            clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
            clips.append(clip)

    video_clip = concatenate_videoclips(clips, method='compose')
    video_clip.write_videofile(path_video_temp, fps=24)
    if os.path.exists(path_video):
        os.remove(path_video)
        os.rename(path_video_temp, path_video)
    else:
        os.rename(path_video_temp, path_video)

    # pyautogui.hotkey('f5')

    return redirect('/')


def delete_files():
    if request.method == 'POST':
        # Check if there's a video with the same name in the static directory
        if os.path.exists(files_path):
            for filename in os.listdir(files_path):
                file_path = os.path.join(files_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f'Erro ao deletar {file_path}: {e}')

    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def upload_process_download():
    if request.method == 'POST':
        # Check which button was clicked
        if request.form.get('upload'):
            # Call the upload function
            upload_files()
            # created because the process wasn't enable
            time.sleep(1)
            return redirect("/")
        elif request.form.get('process'):
            # Call the process function
            process = multiprocessing.Process(target=process_video)
            process.start()
            return redirect('/')
        elif request.form.get('delete'):
            # Call the delete function
            return delete_files()

    # Check if video file exist. If yes, the download button will activate
    if os.path.exists(path_video):
        exist_video = 1
    else:
        exist_video = 0

    # Check if the upload file exist. If yes, the process button will activate
    if os.listdir(files_path) != []:
        exist_file = 1
    else:
        exist_file = 0

    return render_template('index.html', exist_video = exist_video, exist_file = exist_file)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)

