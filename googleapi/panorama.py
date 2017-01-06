import os
import re

class Panorama:
    def __init__(self, panID, imgDir):
        self.panID = panID
        self.imgDir = imgDir

        self.create_dir(imgDir, 'Could not create directory for panorama '
                        'images.')
        self.create_dir(os.path.join(imgDir, 'segments'), 'Could not create '
                        'directory for segmented panoramas.')

        self.slices, self.segments = self.read_cache()

    def create_dir(self, dirname, error):
        if (not os.path.isdir(dirname)):
            try:
                os.makedirs(dirname)
            except OSError:
                raise OSError(error)

    def read_cache(self):
        slices = [f for f in os.listdir(self.imgDir)
                     if (os.path.isfile(os.path.join(self.imgDir, f))
                     # Regex only matches files that are named after headings
                     and re.match('^-?\d+\.\d+\.jpg$', f, re.IGNORECASE))]
        segmentDir = os.path.join(self.imgDir, 'segments')
        segments = [f for f in os.listdir(segmentDir)
                        if (os.path.isfile(os.path.join(segmentDir, f))
                        and re.match('^-?\d+\.\d+_\d{2,3}_(?:[0-8]\d|90)\.jpg',
                                     f, re.IGNORECASE))]
        return slices, segments

    def set_coords(self, coords):
        self.coords = coords

    def add_slice(self, filename):
        self.slices.append(filename)

    def add_segment(self, filename):
        self.segments.append(filename)

    def slice_count(self):
        return len(self.slices)

    def segment_count(self):
        return len(self.segments)

    def headings(self):
        return [image.replace('.jpg', '') for image in self.slices]

    def segment_info(self):
        info = []
        for segment in self.segments:
            sliced = segment.replace('.jpg', '').split('_')
            info.append({'heading': float(sliced[0]), 'fov': float(sliced[1]),
                         'pitch': float(sliced[2])})
        return info

    def full_slice_names(self):
        return [os.path.join(self.imgDir, image) for image in self.slices]

    def full_segment_names(self):
        return [os.path.join(self.imgDir, 'segments', image)
                    for image in self.segments]

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
