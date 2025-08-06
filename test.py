import exiftool

files = ["images/2017-11-24_21-08-55.jpg"]
with exiftool.ExifToolHelper() as et:
    metadata = et.get_metadata(files)
    print(metadata[0]['EXIF:Orientation'])
    # for d in metadata:
    #     print(f"here: {d}")