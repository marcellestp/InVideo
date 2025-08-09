import os
import tempfile
import shutil
import imagesize
import exiftool
from flask import Flask, request, render_template, redirect, send_file, session
from functools import wraps
from moviepy import vfx, ImageClip, concatenate_videoclips, VideoFileClip
from werkzeug.utils import secure_filename

HEIGHT_DEFAULT = 1080
WIDTH_DEFAULT = 1920
clips = []
UPLOAD_FOLDER = 'images/'
TIME = 3
FADEIN_TIME = 0.2
FADEOUT_TIME = 0.2
PATH_VIDEO_TEMP = "static/out_temp.mp4"
PATH_VIDEO = "static/output.mp4"
FILES_PATH = os.path.join(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}

# Create the uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    """
    It will ensure that only the defined extensions are accepted when uploading files.
    """ 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_files():
    """
    It will be responsible for uploading only files with the defined extensions.
    """
    if request.method == 'POST':
        # Get the list of files
        files = request.files.getlist('files')
        # Checks if any files are selected
        if not files[0].filename:
            return 'No files selected'
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
            for file in files:
                # secure_filename resolving file with space in name
                filename = secure_filename(file.filename)
                # Adding the lower() to avoid issues with the extension
                # when processing the pictures/videos
                shutil.copy(os.path.join(temp_dir, filename.lower()), UPLOAD_FOLDER)
            shutil.rmtree(temp_dir)
            return 'Files uploaded successfully.'
        else:
            return 'No files uploaded.'
    return None


# Make crop on images greater then 1920 x 1080
def crop_image(img_height, img_width, file):
    """
    It will define default height and width according to the image's position
     (vertical or horizontal).
    """
    # Vertical image
    if img_height > img_width:
        # WIDTH_DEFAULT = 1080
        # clip = ImageClip(app.config['UPLOAD_FOLDER'] + file)
        clip = ImageClip(UPLOAD_FOLDER + file)
        clip = clip.with_effects([vfx.Resize(height=HEIGHT_DEFAULT)])
        new_width, new_height = clip.size
        new_height_center = new_height / 2
        y1_pos = new_height_center - (HEIGHT_DEFAULT / 2)
        y2_pos = new_height_center + (HEIGHT_DEFAULT / 2)
        clip = clip.with_effects([
            vfx.Crop(x1=0, y1=y1_pos, x2=HEIGHT_DEFAULT, y2=y2_pos)])
    else:
        # Horizonte image
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


def process_video():
    """
    It will be responsible for concatenating the existing files
     in the user's directory and processing the video at the end.
    """
    # Using sorted to sort the list of files
    # https://docs.python.org/3/howto/sorting.html
    for file in sorted(os.listdir(UPLOAD_FOLDER)):
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            # with open("images/" + file, "rb") as image_file:
            with open("images/" + file, "rb") as fp:
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
                    clip = crop_image(img_height, img_width, file)

                    try:
                        res = file_exif[0]['EXIF:Orientation']
                    except KeyError as err:
                        res = False

                    if file_exif and res:
                        try:

                            if file_exif[0]['EXIF:Orientation'] in (1, 2):
                                clips.append(clip.with_duration(TIME).with_effects([vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                            elif file_exif[0]['EXIF:Orientation'] in (6, 7):
                                clip = clip.with_duration(TIME)
                                clip = clip.with_effects([vfx.Resize(width=HEIGHT_DEFAULT)])
                                clip = clip.with_effects([vfx.Rotate(270)])
                                clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
                                clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
                                # clip = clip.with_effects([vfx.Resize(LAMBDA_EFFECT)])
                                clips.append(clip)
                            elif file_exif[0]['EXIF:Orientation'] in (5, 8):
                                clips.append(clip.with_duration(TIME).with_effects([vfx.Resize(width=HEIGHT_DEFAULT), vfx.Rotate(90), vfx.FadeIn(FADEIN_TIME), vfx.FadeOut(FADEOUT_TIME)]))
                            elif file_exif[0]['EXIF:Orientation'] in (3, 4):
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
            clip = VideoFileClip(UPLOAD_FOLDER + file)
            clip = clip.with_effects([vfx.Resize(height=HEIGHT_DEFAULT)])
            clip = clip.with_effects([vfx.FadeIn(FADEIN_TIME)])
            clip = clip.with_effects([vfx.FadeOut(FADEOUT_TIME)])
            clips.append(clip)

    video_clip = concatenate_videoclips(clips, method='compose')
    video_clip.write_videofile(PATH_VIDEO_TEMP, fps=24)
    if os.path.exists(PATH_VIDEO):
        os.remove(PATH_VIDEO)
        os.rename(PATH_VIDEO_TEMP, PATH_VIDEO)
    else:
        os.rename(PATH_VIDEO_TEMP, PATH_VIDEO)

    return None


def delete_files():
    """
    It will delete the existing files in the user's directory.
    """
    if request.method == 'POST':
        # Check if there's a video with the same name in the static directory
        if os.path.exists(FILES_PATH):
            for filename in os.listdir(FILES_PATH):
                file_path = os.path.join(FILES_PATH, filename)
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
    if os.path.exists(PATH_VIDEO):
        exist_video = 1
    else:
        exist_video = 0
    return exist_video


# Check if the upload file exist. If yes, the process button will activate
def check_file_upload_exists():
    if os.listdir(FILES_PATH) != []:
        exist_file = 1
    else:
        exist_file = 0
    return exist_file


# Check how many uploaded files exist
def check_quant_upload_exists():
    file_list = len([file for file in os.scandir(FILES_PATH) if file.is_file()])
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


def apology(message, code=400):
    """Render message as an apology to user."""
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
