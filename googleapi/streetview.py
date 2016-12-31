import urllib
import json
import math
import os

from exception import AddressNotFoundException, MetaDataRetrievalException
from panorama import Panorama
from maps import BearingEstimator

class ImageRetriever:
    API_URL = 'https://maps.googleapis.com/maps/api/streetview'
    META_URL = API_URL + '/metadata'
    META_STATUS = {
        'OK': 'OK',
        'ZERO': 'ZERO_RESULTS',
        'NOT_FOUND': 'NOT_FOUND',
        'OVER_LIMIT': 'OVER_QUERY_LIMIT',
        'DENIED': 'REQUEST_DENIED',
        'INVALID': 'INVALID_REQUEST',
        'UNKNOWN': 'UNKNOWN_ERROR'
    }

    # Specified by Google
    MAX_FOV = 120
    DEFAULT_FOV = 90

    # Specified by Google; if the request specifies more it'll just go to this
    # silently
    MAX_SIZE = 640

    def __init__(self, targetDir, apiKey, fov = DEFAULT_FOV,
                 size = {'x': MAX_SIZE, 'y': MAX_SIZE}):
        self.targetDir = targetDir
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

    def image_meta(self, location):
        location = self.string_location(location)
        params = urllib.urlencode({'key': self.apiKey, 'location': location})
        url = self.META_URL + '?' + params

        response = urllib.urlopen(url)
        meta = json.loads(response.read())

        if (meta['status'] == self.META_STATUS['OK']):
            return meta
        elif (meta['status'] == self.META_STATUS['ZERO']
              or meta.status == self.META_STATUS['NOT_FOUND']):
            # Since we're only expecting lat/long pairs and not
            # street addresses, these status values basically
            # mean the same thing
            raise AddressNotFoundException('No imagery available for '
                + location)
        else:
            raise MetaDataRetrievalException('An error occurred retrieving '
                'address metadata. The error was: ' + meta['status'])

    def get_image(self, meta, forwardHeading):
        panID = meta['pano_id']

        urlParams = {'pano': panID, 'fov': self.fov,
                     'size': str(self.size['x']) + 'x' + str(self.size['y']),
                     'key': self.apiKey}
        imgDir = os.path.join(self.targetDir, panID)
        headings = self.calculate_pano_headings(forwardHeading)
        cached = self.get_cached_image(panID, headings)
        cached.set_coords(str(meta['location']['lat']) + ',' +
                          str(meta['location']['lng']))

        return self.get_panorama(cached, urlParams, headings, panID, imgDir)

    def get_panorama(self, cached, params, headings, panID, imgDir):
        cachedFiles = cached.files

        # TODO: Better error handling here
        for heading in headings:
            filename = str(heading) + '.jpg'
            if (filename not in cachedFiles):
                params['heading'] = heading
                url = self.API_URL + '?' + urllib.urlencode(params)
                filename = os.path.join(imgDir, filename)
                urllib.urlretrieve(url, filename)
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

    def string_location(self, location):
        return location if isinstance(location, basestring) \
                        else ','.join(map(str, location))
