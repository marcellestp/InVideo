"""
Module responsible for most of the operations
"""
import sqlite3
import os
import tempfile
import shutil
import imagesize
import exiftool
from datetime import datetime
from flask import Flask, request, render_template, redirect, send_file, session
from functools import wraps
from moviepy import vfx, ImageClip, concatenate_videoclips, VideoFileClip
from werkzeug.utils import secure_filename

HEIGHT_DEFAULT = 1080
WIDTH_DEFAULT = 1920
clips = []
TIME = 3
FADEIN_TIME = 0.2
FADEOUT_TIME = 0.2

# Specify a directory to store uploaded files.
BASE_PATH = 'images/'
STATIC = "static/"
# PATH_VIDEO = "static/output.mp4"
# PATH_VIDEO_TEMP = "static/out_temp.mp4"
TEMP_FILENAME = "_out_temp.mp4"
FINAL_FILENAME = "_output.mp4"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}

database_file = "invideo.db"
connection = sqlite3.connect(database_file, check_same_thread=False)
db = connection.cursor()

def apology(message, code=400):
    """
    Render message as an apology to user.
    """
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def insert_log(total_files, total_images, total_videos, user_id):
    """
    Insert log in the begining of the process 
     and update de log in the end of the process.
    """
    try:
        if user_id:
            if total_files > 0:
                # print(f"Log: total_files: {total_files}")
                db.execute(
                    "INSERT INTO logs (user_id, total_files, status, date_start) VALUES ( ?, ?, 'processing', ?)",
                        (user_id, total_files, datetime.now())
                )
                connection.commit()

            else:
                # Select the max id_log for the user_id
                db.execute(
                    "SELECT MAX(id) FROM logs WHERE user_id = ?", (user_id,)
                )

                rows = db.fetchall()
                max_id = rows[0][0]
                # print(rows)
                # print(f"max_id log: {max_id}")

                db.execute(
                    "UPDATE logs SET total_images = ?, total_videos = ?, status = 'concluded', date_end = ? WHERE user_id = ? AND id = ?", 
                        (total_images, total_videos, datetime.now(), user_id, max_id)
                )

                connection.commit()


    except KeyError as err:
        print(f"Keyerror: {err}")
        # return None, None


def base_dir(user_id):
    """
    It will concatenate the user_id to the name of the output video and the file folder
     to store the files uploaded by the user in their session.
    """
    try:
        if user_id:
            # print(f"session['user_id']: {session['user_id']}")
            # Create session user folder
            FOLDER_USER = str(user_id) + "/"
            # print(f"FOLDER_USER: {FOLDER_USER}")

            UPLOAD_FOLDER = os.path.join(BASE_PATH, FOLDER_USER)
            PATH_VIDEO = STATIC + str(user_id) + FINAL_FILENAME

            # Create the uploads directory if it doesn't exist
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
        else:
            UPLOAD_FOLDER = 'images/'
            # UPLOAD_FOLDER = UPLOAD_FOLDER

    except KeyError as err:
        print(f"Keyerror: {err}")
        # return None, None


    try:
        if session['user_id']:
            # print(f"session['user_id']: {session['user_id']}")
            # Create session user folder
            FOLDER_USER = str(session['user_id']) + "/"
            UPLOAD_FOLDER = os.path.join(BASE_PATH, FOLDER_USER)
            PATH_VIDEO = STATIC + str(session['user_id']) + FINAL_FILENAME
            # print(f"PATH_VIDEO: {PATH_VIDEO}")

            # Create the uploads directory if it doesn't exist
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
        else:
            UPLOAD_FOLDER = 'images/'

    except RuntimeError as err:
        print(f"Error no try: {err}")
    except KeyError as err:
        print(f"Error no try - keyerror: {err}")
        return None, None

    return UPLOAD_FOLDER, PATH_VIDEO


def allowed_file(filename):
    """
    Ensure that only the defined extensions are accepted when uploading files.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_files():
    """
    Upload files selected by the user uploading only files with the allowed extensions.
    """
    if request.method == 'POST':
        # print(session['user_id'])
        UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id = None)
        # Get the list of files
        files = request.files.getlist('files')
        # Checks if any files are selected
        if not files[0].filename:
            # print(f"AUDIT: upload no files")
            # no files are selected
            return 0

        elif files:
            temp_dir = tempfile.mkdtemp()
            # Save each file to the uploads directory
            for file in files:
                if file and allowed_file(file.filename):
                    # secure_filename resolving file with space in name
                    filename = secure_filename(file.filename)
                    # Adding the lower() to avoid issues with the extension
                    # when processing the pictures/videos
                    file.save(os.path.join(temp_dir, filename.lower()))
                else:
                    # selected not allowed files
                    return 1
            for file in files:
                # secure_filename resolving file with space in name
                filename = secure_filename(file.filename)
                # Adding the lower() to avoid issues with the extension
                # when processing the pictures/videos
                shutil.copy(os.path.join(temp_dir, filename.lower()), UPLOAD_FOLDER)
            shutil.rmtree(temp_dir)
            return 'Files uploaded successfully'
        else:
            return apology("No files uploaded", 204)
    # return None
    return render_template('apology.html')


# # Make crop on images greater then 1920 x 1080
# def crop_image(user_id, img_height, img_width, file):
#     """
#     Define default height and width according to the image's position
#      (vertical or horizontal).
#     """
#     UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id)
#     # print(f"UPLOAD_FOLDER inside crop_image: {UPLOAD_FOLDER}")
#     # Vertical image
#     if img_height > img_width:
#         print(f"Vertical inside crop_image: {img_width}")
#         # WIDTH_DEFAULT = 1080
#         # clip = ImageClip(app.config['UPLOAD_FOLDER'] + file)
#         clip = ImageClip(UPLOAD_FOLDER + file)
#         clip = clip.with_effects([vfx.Resize(height=HEIGHT_DEFAULT)])
#         new_width, new_height = clip.size
#         # new_height_center = new_height / 2
#         # y1_pos = new_height_center - (HEIGHT_DEFAULT / 2)
#         # y2_pos = new_height_center + (HEIGHT_DEFAULT / 2)
#         # clip = clip.with_effects([
#         #     vfx.Crop(x1=0, y1=y1_pos, x2=HEIGHT_DEFAULT, y2=y2_pos)])
#     else:
#         # Horizonte image
#         print(f"Horizontal inside crop_image: {img_width}")
#         # WIDTH_DEFAULT = 1920
#         clip = ImageClip(UPLOAD_FOLDER + file)
#         clip = clip.with_effects([vfx.Resize(width=WIDTH_DEFAULT)])
#         new_width, new_height = clip.size
#         new_height_center = new_height / 2
#         y1_pos = new_height_center - (HEIGHT_DEFAULT / 2)
#         y2_pos = new_height_center + (HEIGHT_DEFAULT / 2)
#         clip = clip.with_effects([
#             vfx.Crop(x1=0, y1=y1_pos, x2=WIDTH_DEFAULT, y2=y2_pos)])

#     return clip


# Make crop on Vertical images
def crop_image_vert(user_id, img_height, img_width, file):
    """
    Define default height and width according to the image's position
     (vertical or horizontal).
    """
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id)
    # print(f"UPLOAD_FOLDER inside crop_image: {UPLOAD_FOLDER}")
    # Vertical image
    # if img_height > img_width:
    print(f"Vertical inside crop_image: {img_width}")
    # WIDTH_DEFAULT = 1080
    # clip = ImageClip(app.config['UPLOAD_FOLDER'] + file)
    clip = ImageClip(UPLOAD_FOLDER + file)
    clip = clip.with_effects([vfx.Resize(height=HEIGHT_DEFAULT)])
    new_width, new_height = clip.size
    # new_height_center = new_height / 2
    # y1_pos = new_height_center - (HEIGHT_DEFAULT / 2)
    # y2_pos = new_height_center + (HEIGHT_DEFAULT / 2)
    # clip = clip.with_effects([
    #     vfx.Crop(x1=0, y1=y1_pos, x2=HEIGHT_DEFAULT, y2=y2_pos)])
    

    return clip


# Make crop on horizontal images 
def crop_image_horiz(user_id, img_height, img_width, file):
    """
    Define default height and width according to the image's position
     (vertical or horizontal).
    """
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id)
    # print(f"UPLOAD_FOLDER inside crop_image: {UPLOAD_FOLDER}")
    # Vertical image
    # if img_height > img_width:

    # Horizonte image
    print(f"Horizontal inside crop_image: {img_width}")
    # WIDTH_DEFAULT = 1920
    clip = ImageClip(UPLOAD_FOLDER + file)
    clip = clip.with_effects([vfx.Resize(width=WIDTH_DEFAULT)])
    new_width, new_height = clip.size
    new_height_center = new_height / 2
    y1_pos = new_height_center - (HEIGHT_DEFAULT / 2)
    y2_pos = new_height_center + (HEIGHT_DEFAULT / 2)
    clip = clip.with_effects([
        vfx.Crop(x1=0, y1=y1_pos, x2=WIDTH_DEFAULT, y2=y2_pos)])

    return clip


def process_video(user_id):
    """
    Concatenates the existing files
     in the user's directory and processing the video at the end.
    """
    # print(f"AUDIT: Process_video")
    # print(f"session {session['user_id']}")
    # print(f"session: {user_id}")
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id)
    total_files = len(os.listdir(UPLOAD_FOLDER))
    total_images = 0
    total_videos = 0
    insert_log(total_files, total_images, total_videos, user_id)
    # print(f"UPLOAD_FOLDER under process: {UPLOAD_FOLDER}")
    # Using sorted to sort the list of files
    # https://docs.python.org/3/howto/sorting.html
    for file in sorted(os.listdir(UPLOAD_FOLDER)):
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            # cont images
            total_images = total_images + 1

            # with open("images/" + file, "rb") as image_file:
            with open(UPLOAD_FOLDER + file, "rb") as fp:
            # with open("images/" + file, "rb") as fp:
                with exiftool.ExifToolHelper() as image_file:
                    file_exif = image_file.get_metadata(fp.name)
                    try:
                        img_height = file_exif[0]['File:ImageHeight']
                        img_width = file_exif[0]['File:ImageWidth']
                    except AttributeError:
                        img_width, img_height = imagesize.get(UPLOAD_FOLDER + file)
                    except KeyError:
                        img_width, img_height = imagesize.get(UPLOAD_FOLDER + file)
                    # Crop images to the default size of 1920x1080
                    # clip = crop_image(user_id, img_height, img_width, file)

                    try:
                        res = file_exif[0]['EXIF:Orientation']
                    except KeyError as err:
                        res = False

                    if file_exif and res:
                        try:

                            if file_exif[0]['EXIF:Orientation'] in (1, 2):
                                clip = crop_image_horiz(user_id, img_height, img_width, file)
                                clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                            elif file_exif[0]['EXIF:Orientation'] in (6, 7):
                                clip = crop_image_vert(user_id, img_height, img_width, file)
                                clip = clip.with_duration(TIME)
                                clip = clip.with_effects([vfx.Resize(width=HEIGHT_DEFAULT)])
                                clip = clip.with_effects([vfx.Rotate(270)])
                                clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
                                clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
                                # clip = clip.with_effects([vfx.Resize(LAMBDA_EFFECT)])
                                clips.append(clip)
                            elif file_exif[0]['EXIF:Orientation'] in (5, 8):
                                clip = crop_image_vert(user_id, img_height, img_width, file)
                                clips.append(clip.with_duration(TIME).with_effects([vfx.Resize(width=HEIGHT_DEFAULT), vfx.Rotate(90), vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                            elif file_exif[0]['EXIF:Orientation'] in (3, 4):
                                clip = crop_image_horiz(user_id, img_height, img_width, file)
                                clips.append(clip.with_duration(TIME).with_effects([vfx.Resize(width=HEIGHT_DEFAULT), vfx.Rotate(180), vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                            else:
                                clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                        except AttributeError:
                            clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                        except ValueError:
                            clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))

                    else:
                        clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))

        # If file is video .mp4 or .mov
        if file.endswith(".mp4") or file.endswith(".mov"):
            total_videos = total_videos + 1
            clip = VideoFileClip(UPLOAD_FOLDER + file)
            clip = clip.with_effects([vfx.Resize(height=HEIGHT_DEFAULT)])
            clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
            clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
            clips.append(clip)

    video_clip = concatenate_videoclips(clips, method='compose')
    PATH_VIDEO_TEMP = STATIC + str(user_id) + TEMP_FILENAME
    video_clip.write_videofile(PATH_VIDEO_TEMP, fps=24)
    insert_log(0, total_images, total_videos, user_id)

    if os.path.exists(PATH_VIDEO):
        os.remove(PATH_VIDEO)
        os.rename(PATH_VIDEO_TEMP, PATH_VIDEO)
    else:
        os.rename(PATH_VIDEO_TEMP, PATH_VIDEO)

    return None


def delete_files():
    """
    Delete the existing files in the user's directory
     and the video generated by the app.
    """
    if request.method == 'POST':
        UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id = None)
        # Check if there's a video with the same name in the static directory
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f'Erro ao deletar {file_path}: {e}')
        # Check if there's a output video and delete
        if os.path.exists(PATH_VIDEO):
            os.remove(PATH_VIDEO)


# Check if video file exist. If yes, the download button will activate
def check_video_exists():
    """
    Checks if the processed video exists. If yes, 
     the View and Download buttons will activate.
    """
    # print(f"AUDIT check_video_exists")
    # print(f"session inside check_video_exists: {session['user_id']}")
    
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id = None)
    # print(f"PATH_VIDEO: {PATH_VIDEO}")
    if os.path.exists(PATH_VIDEO):
        exist_video = 1
    else:
        exist_video = 0
    return exist_video
    # return None

# Check if the upload file exist. If yes, the process button will activate
def check_file_upload_exists():
    """
    Check if there are files sent. If yes, the process button will activate
    """
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id = None)
    if os.listdir(UPLOAD_FOLDER) != []:
        exist_file = 1
    else:
        exist_file = 0
    return exist_file


  # Check how many uploaded files exist
def check_quant_upload_exists():
    """
    Check how many uploaded files exist to present on the main page for the user.
    """
    UPLOAD_FOLDER, PATH_VIDEO = base_dir(user_id = None)
    file_list = len([file for file in os.scandir(UPLOAD_FOLDER) if file.is_file()])
    return file_list


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
