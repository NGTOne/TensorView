import math
import os

from panorama import Panorama
from roads import BearingEstimator
from adapter import GoogleAdapter, string_coords
from exception import NearestRoadException, AddressNotFoundException

class PanoramaRetriever:
    DEFAULT_FOV = 90

    # Non-premium users will be coerced to this anyways - premium users can
    # have up to 2048x2048
    DEFAULT_SIZE = 640

    def __init__(self, targetDir, apiKey, **kwargs):
        self.targetDir = targetDir
        self.adapter = GoogleAdapter(apiKey)
        self.apiKey = apiKey
        self.size = kwargs.get('size', {'x': self.DEFAULT_SIZE,
                                        'y': self.DEFAULT_SIZE})
        self.fov = kwargs.get('fov', self.DEFAULT_FOV)
        self.useOblique = kwargs.get('oblique', False)

    def retrieve_images(self, locations = []):
        images = []
        locations = self.get_metadata_and_deduplicate(locations)

        # TODO: Parallelize this bit
        for loc in locations:
            images.append(self.get_image(loc['meta'],
                                         loc['forward_heading']))

        return images

    def get_metadata_and_deduplicate(self, locations):
        # We can use Street View metadata to deduplicate location
        # TODO: Clean up this dog's breakfast
        cachedMeta = self.read_id_file()

        metaLocations = []
        for loc in locations:
            try:
                metaLocations.append({'coords': loc['coords'],
                                      'meta': self.image_meta(loc['coords'],
                                                              cachedMeta)})
            except AddressNotFoundException:
                continue # Nothing to do here, carry on

        # Filter out duplicates
        panIDs = set()
        locations = [loc for loc in metaLocations if loc['meta']['pano_id']
                         not in panIDs and (panIDs.add(loc['meta']['pano_id'])
                                            or True)]

        # Forward headings isn't free, so we deduplicate first
        return self.get_forward_headings(locations)

    def image_meta(self, coords, cached):
        coords = string_coords(coords)
        if coords not in cached:
            meta = self.adapter.street_view_image_meta(coords)
            self.cache_meta(coords, meta)
            return meta
        if cached[coords] == 'NOT_FOUND':
            raise AddressNotFoundException()
        return cached[coords]

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
                fullFilename = os.path.join(imgDir, filename)
                self.adapter.street_view_image(panID, self.fov,
                                               self.size['x'], self.size['y'],
                                               heading, 0, fullFilename)
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
        if self.useOblique:
            numIncrements = self.num_images()
            increment = 360.0/numIncrements

            return [(forwardHeading + (i * increment)) % 360
                        for i in range(0, numIncrements)]

        return [(forwardHeading + 90.0) % 360, (forwardHeading - 90.0) % 360]

    def get_forward_headings(self, locations):
        estimator = BearingEstimator(self.apiKey)
        cachedHeadings = self.read_headings_file()
        try:
            full = []
            for loc in locations:
                full.append({'coords': loc['coords'], 'meta': loc['meta'],
                             'forward_heading':
                             (estimator.check_bearing(loc['coords'])
                             if string_coords(loc['coords'])
                             not in cachedHeadings else
                             cachedHeadings[string_coords(loc['coords'])])
                                 % 360})
        except NearestRoadException:
            self.cache_headings(cachedHeadings, full)
            raise
        self.cache_headings(cachedHeadings, full)
        return full

    def id_file(self):
        return os.path.join(self.targetDir, 'points.csv')

    def headings_file(self):
        return os.path.join(self.targetDir, 'headings.csv')

    def cache_meta(self, coords, meta):
        metaFile = self.id_file()
        with open(metaFile, 'a') as f:
            if 'pano_id' in meta:
                f.write(string_coords(coords) + ',' + meta['pano_id'] + ',' +
                    str(meta['location']['lat']) + ',' +
                    str(meta['location']['lng']) + '\n')
            else:
                f.write(string_coords(coords) + ',NOT_FOUND')

    def cache_headings(self, cached, locations):
        headingsFile = self.headings_file()
        with open(headingsFile, 'a') as f:
            for loc in locations:
                stringCoords = string_coords(loc['coords'])
                if stringCoords not in cached:
                    f.write(stringCoords + ',' + str(loc['forward_heading'])
                            + '\n')

    # TODO: Refactor these
    def read_id_file(self):
        idFile = self.id_file()
        if not os.path.isfile(idFile):
            return {}

        cachedPoints = {}
        with open(idFile, 'r') as f:
            for line in f:
                line = line.strip().split(',')
                # We store the true location of each pano, as it is often
                # different from the co-ordinates we ask for
                cachedPoints[line[0] + ',' + line[1]] = \
                    {'pano_id': line[2],
                     'location': {'lat': line[3], 'lng': line[4]}} \
                if line[2] != 'NOT_FOUND' else line[2]
        return cachedPoints

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
