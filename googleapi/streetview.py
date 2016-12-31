import math
import os

from panorama import Panorama
from roads import BearingEstimator
from adapter import GoogleAdapter

class ImageRetriever:
    # Specified by Google
    MAX_FOV = 120
    DEFAULT_FOV = 90

    # Specified by Google; if the request specifies more it'll just go to this
    # silently
    MAX_SIZE = 640

    def __init__(self, targetDir, apiKey, fov = DEFAULT_FOV,
                 size = {'x': MAX_SIZE, 'y': MAX_SIZE}):
        self.targetDir = targetDir
        self.adapter = GoogleAdapter(apiKey)
        self.apiKey = apiKey
        self.size = size
        if (fov > self.MAX_FOV):
            raise ValueError('Requested field-of-view (FOV) cannot exceed '
                + self.MAX_FOV + 'degrees. If the docs say it can be more than '
                'this, please contact a maintainer so they can fix it.')
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
        cachedFiles = cached.files

        # TODO: Better error handling here
        for heading in headings:
            filename = str(heading) + '.jpg'
            if (filename not in cachedFiles):
                filename = os.path.join(imgDir, filename)
                self.adapter.street_view_image(panID, self.fov,
                                               self.size['x'], self.size['y'],
                                               heading, filename)
                cached.add_image(filename)

        return cached

    def get_cached_image(self, panID, headings):
        cachedPano = Panorama(panID, os.path.join(self.targetDir, panID))
        cachedPano.clear_cache(headings)
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
        return [{'coords': loc['coords'],
                 'forward_heading': estimator.check_bearing(loc['coords'])}
               for loc in locations]
