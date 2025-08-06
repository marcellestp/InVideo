import exiftool

# files = ["images/2017-11-24_21-08-55.jpg"]
files = ["images/20250702_164054-collage.jpg"]

with exiftool.ExifToolHelper() as image_file:
    file_exif = image_file.get_metadata(files)
    print(f"Orientation: {file_exif[0]}")
    # print(f"Orientation: {file_exif[0]['EXIF:Orientation']}")
    print(f"File:ImageHeight: {file_exif[0]['File:ImageHeight']}")
    # print(f"EXIF:ImageHeight: {file_exif[0]['EXIF:ImageHeight']}")

    print(f"File:ImageWidth: {file_exif[0]['File:ImageWidth']}")
    # print(f"EXIF:ImageWidth: {file_exif[0]['EXIF:ImageWidth']}")
