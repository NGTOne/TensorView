import os
import re

class Panorama:
    def __init__(self, panID, imgDir):
        self.panID = panID
        self.imgDir = imgDir

        if (not os.path.isdir(imgDir)):
            try:
                os.makedirs(imgDir)
            except OSError:
                raise OSError('Could not create directory for panorama images.')

        self.files = self.find_files()

    def find_files(self):
        return [f for f in os.listdir(self.imgDir)
                if (os.path.isfile(os.path.join(self.imgDir, f))
                    and re.match('^-?\d+\.\d+\.jpg$', f, re.IGNORECASE))]
                    # Regex only matches files that are named after headings

    def set_coords(self, coords):
        self.coords = coords

    def add_image(self, filename):
        self.files.append(filename)

    def file_count(self):
        return len(self.files)

    def headings(self):
        return [image.replace('.jpg', '') for image in self.files]

    def full_filenames(self):
        return [os.path.join(self.imgDir, image) for image in self.files]

    def clear_cache(self, headings):
        # We don't want to delete the directory because we'll likely be writing
        # to it again soon anyways
        safeImages = []
        if (len(headings) == self.file_count()):
           images = [str(heading) + '.jpg' for heading in headings]
           safeImages = [image for image in images if image in self.files]

        for f in self.files:
            if f not in safeImages:
                os.remove(os.path.join(self.imgDir, f))
        self.files = [f for f in self.files if f in safeImages]
