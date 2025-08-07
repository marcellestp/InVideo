"""
docstring here
"""
import multiprocessing
import os
import time
from flask import Flask, request, render_template, redirect, send_file
from invideo.tasks import *


app = Flask(__name__)


# Specify a directory to store uploaded files.
UPLOAD_FOLDER = 'images/'
FILES_PATH = os.path.join(UPLOAD_FOLDER)
PATH_VIDEO_TEMP = "static/out_temp.mp4"
PATH_VIDEO = "static/output.mp4"


@app.route('/download')
def download_files():
    """
    It will download the video files in the user's Downloads directory.
    """
    try:
        return send_file(PATH_VIDEO, as_attachment=True)
    except FileNotFoundError:
        return "File not found!", 404


@app.route('/', methods=['GET', 'POST'])
def upload_process_download():
    """
    It will be responsible for identify which option the user
     is selecting on the system's main page.
    """
    if request.method == 'POST':
        # Check which button was clicked
        if request.form.get('upload'):
            # Call the upload function
            upload_files()
            # Created because the process button wasn't showing up after upload
            time.sleep(1)
            return redirect("/")
        if request.form.get('process'):
            # Call the process function
            process = multiprocessing.Process(target=process_video)
            process.start() # Begin the process execution
            process.join()  # Wait for the process to finish
            return redirect('/')
        if request.form.get('delete'):
            # Call the delete function
            delete_files()
            return redirect('/')

    exist_video = check_video_exists()
    exist_file = check_file_upload_exists()
    file_list = check_quant_upload_exists()
    
    return render_template('index.html', exist_video=exist_video,
        exist_file=exist_file, file_list=file_list)


if __name__ == '__main__':
    app.run(debug=True)
