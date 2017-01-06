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

        self.slices = self.find_cached_slices()

    def find_cached_slices(self):
        return [f for f in os.listdir(self.imgDir)
                if (os.path.isfile(os.path.join(self.imgDir, f))
                    and re.match('^-?\d+\.\d+\.jpg$', f, re.IGNORECASE))]
                    # Regex only matches files that are named after headings

    def set_coords(self, coords):
        self.coords = coords

    def add_slice(self, filename):
        self.slices.append(filename)

    def slice_count(self):
        return len(self.slices)

    def headings(self):
        return [image.replace('.jpg', '') for image in self.slices]

    def full_slice_names(self):
        return [os.path.join(self.imgDir, image) for image in self.slices]

    def clean_up_slice_cache(self, headings):
        # We don't want to delete the directory because we'll likely be writing
        # to it again soon anyways
        safeImages = []
        if (len(headings) == self.file_count()):
           images = [str(heading) + '.jpg' for heading in headings]
           safeImages = [image for image in images if image in self.slices]

        for f in self.slices:
            if f not in safeImages:
                os.remove(os.path.join(self.imgDir, f))
        self.slices = [f for f in self.slices if f in safeImages]
