import math
import os

from panorama import Panorama
from roads import BearingEstimator
from adapter import GoogleAdapter, string_coords
from exception import AddressNotFoundException

class PanoramaRetriever:
    DEFAULT_FOV = 90

    # Non-premium users will be coerced to this anyways - premium users can
    # have up to 2048x2048
    DEFAULT_SIZE = 640

    def __init__(self, targetDir, apiKey, fov = DEFAULT_FOV,
                 size = {'x': DEFAULT_SIZE, 'y': DEFAULT_SIZE}):
        self.targetDir = targetDir
        self.adapter = GoogleAdapter(apiKey)
        self.apiKey = apiKey
        self.size = size
        self.fov = fov

    def retrieve_images(self, locations = []):
        images = []
        locations = self.get_forward_headings(locations)

        # TODO: Parallelize this bit
        for loc in locations:
            try:
                meta = self.image_meta(loc['coords']);
                images.append(self.get_image(meta, loc['forward_heading']))
            except AddressNotFoundException:
                # Nothing here, let's move on to the next one
                continue

        return images

    def image_meta(self, coords):
        return self.adapter.street_view_image_meta(coords)

    def get_image(self, meta, forwardHeading):
        panID = meta['pano_id']

        imgDir = os.path.join(self.targetDir, panID)
        headings = self.calculate_pano_headings(forwardHeading)
        cached = self.get_cached_image(panID, headings)
        cached.set_coords(str(meta['location']['lat']) + ',' +
                          str(meta['location']['lng']))

        return self.get_panorama(cached, headings, panID, imgDir)

    def get_panorama(self, cached, headings, panID, imgDir):
        cachedSlices = cached.slices

        # TODO: Better error handling here
        for heading in headings:
            filename = str(heading) + '.jpg'
            if (filename not in cachedSlices):
                filename = os.path.join(imgDir, filename)
                self.adapter.street_view_image(panID, self.fov,
                                               self.size['x'], self.size['y'],
                                               heading, 0, filename)
                cached.add_slice(filename)

        return cached

    def get_cached_image(self, panID, headings):
        cachedPano = Panorama(panID, os.path.join(self.targetDir, panID))
        cachedPano.clean_up_slice_cache(headings)
        return cachedPano

    def num_images(self):
        if (360 % self.fov == 0):
            return 360/self.fov
        return math.ceil(360.0/self.fov)

    def calculate_pano_headings(self, forwardHeading):
        # The Street View API views heading as 0 = due north = 360
        numIncrements = self.num_images()
        increment = 360.0/numIncrements

        return [forwardHeading + (i * increment)
                    for i in range(0, numIncrements)]

    def get_forward_headings(self, locations):
        estimator = BearingEstimator(self.apiKey)
        cachedHeadings = self.read_headings_file()
        full = [{'coords': loc['coords'],
                 'forward_heading':
                  estimator.check_bearing(loc['coords'])
                      if string_coords(loc['coords'])
                      not in cachedHeadings else
                      cachedHeadings[string_coords(loc['coords'])]}
               for loc in locations]
        self.cache_headings(cachedHeadings, full)
        return full

    def headings_file(self):
        return os.path.join(self.targetDir, 'headings.csv')

    def cache_headings(self, cached, locations):
        headingsFile = self.headings_file()
        with open(headingsFile, 'a') as f:
            for loc in locations:
                stringCoords = string_coords(loc['coords'])
                if stringCoords not in cached:
                    f.write(stringCoords + ',' + str(loc['forward_heading'])
                            + '\n')

    def read_headings_file(self):
        headingsFile = self.headings_file()
        if not os.path.isfile(headingsFile):
            return {}

        headings = {}
        with open(headingsFile, 'r') as f:
            for line in f:
                line = line.strip().split(',')
                headings[line[0] + ',' + line[1]] = float(line[2])
        return headings
