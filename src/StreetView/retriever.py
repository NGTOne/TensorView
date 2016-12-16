import urllib
import json
import math
import os

from exception import AddressNotFoundException, MetaDataRetrievalException
from panorama import Panorama

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

        for loc in locations:
            try:
                meta = self.image_meta(loc['coords']);
                images.append(self.get_image(meta, loc['forward_heading']))
            except AddressNotFoundException:
                # Nothing here, let's move on to the next one
                continue

        return images

    def image_meta(self, location):
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

        cached = self.get_cached_image(panID)

        if (cached):
            return cached

        urlParams = {'pano': panID, 'fov': self.fov,
                     'size': str(self.size['x']) + 'x' + str(self.size['y']),
                     'key': self.apiKey}
        headings = self.calculate_headings(forwardHeading)
        imgDir = os.path.join(self.targetDir, panID)

        return self.get_panorama(urlParams, headings, panID, imgDir)

    def get_panorama(self, params, headings, panID, imgDir):
        pano = Panorama(panID, imgDir)

         # TODO: Better error handling here
        for heading in headings:
            params['heading'] = heading
            url = self.API_URL + '?' + urllib.urlencode(params)
            filename = os.path.join(imgDir, str(heading) + '.jpg')
            urllib.urlretrieve(url, filename)
            pano.addImage(filename)

        return pano

    def get_cached_image(self, panID):
        # TODO: Implement image caching
        return None

    def calculate_headings(self, forwardHeading):
        # The Street View API views heading as 0 = due north = 360
        headings = []
        if (360 % self.fov == 0):
            actualIncrement = self.fov
            numIncrements = 360/self.fov
        else:
            # Instead of having one big overrun on the final image of the
            # panorama, we're going to distribute it between all of them
            numIncrements = math.ceil(360.0/self.fov)
            actualIncrement = 360.0/numIncrements

        for i in range(0, numIncrements):
            headings.append(forwardHeading + i * actualIncrement)

        return headings
