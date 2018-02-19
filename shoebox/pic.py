# shoebox.pic

pictureExts = [".jpg", ".jpeg", ".gif", ".png", ".tif"]

nailSizes = [128, 244]

# return PIL image rotated according to EXIF orientation value
def fix_image_orientation(im):
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif and 274 in exif:  # 274 = Orientation
            orientation = exif[274]
            if orientation == 3:  # 3 = Bottom/Right
                return im.rotate(180, expand=True)
            elif orientation == 6:  # 6 = Right/Top
                return im.rotate(270, expand=True)
            elif orientation == 8:  # 8 = Left/Bottom
                return im.rotate(90, expand=True)
    return im
