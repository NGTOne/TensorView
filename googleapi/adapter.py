import urllib
import json

from exception import AddressNotFoundException, MetaDataRetrievalException, \
                      NearestRoadException

class GoogleAdapter:
    def __init__(self, apiKey):
        self.apiKey = apiKey

    def url(self, api, endpoint, params):
        params['key'] = self.apiKey
        return 'https://' + api + '.googleapis.com/' + endpoint + '?' + \
               urllib.urlencode(params)

    def call_json(self, url):
        response = urllib.urlopen(url)
        return json.loads(response.read())

    def call_write_to_fs(self, url, filename):
        urllib.urlretrieve(url, filename)

    def nearest_roads(self, coords):
        stringCoordSet = [string_coords(coord) for coord in coords] \
                           if not isinstance(coords, basestring) else coords
        url = self.url('roads', 'v1/nearestRoads',
                       {'points': '|'.join(stringCoordSet)})
        json = self.call_json(url)

        if 'snappedPoints' in json:
            return json['snappedPoints']
        elif 'error' in json:
            raise NearestRoadException('Unable to retrieve nearest road to ' +
                                       'points ' + str(stringCoordSet) +
                                       ' with error "' +
                                       json['error']['message'] + '"')

        # Specified by Google
        MIN_STREET_VIEW_FOV = 10
        MAX_STREET_VIEW_FOV = 120
    def street_view_image(self, panID, fov, x, y, heading, pitch, filename):
        if (fov < self.MIN_STREET_VIEW_FOV):
            raise ValueError('Field of view (FOV) cannot be less than ' +
                             self.MIN_STREET_VIEW_FOV + ' degrees.')
        elif (fov > self.MAX_STREET_VIEW_FOV):
            raise ValueError('Field of view (FOV) cannot be greater than ' +
                             self.MAX_STREET_VIEW_FOV + ' degrees.')

        url = self.url('maps', 'maps/api/streetview',
                       {'pano': panID, 'fov': fov, 'heading': heading,
                         'size': str(x) + 'x' + str(y), 'pitch': pitch})
        self.call_write_to_fs(url, filename)

    def street_view_image_meta(self, coords):
        coords = string_coords(coords)
        url = self.url('maps', 'maps/api/streetview/metadata',
                       {'location': coords})
        response = urllib.urlopen(url)
        meta = json.loads(response.read())

        if (meta['status'] == 'OK'):
            return meta
        elif (meta['status'] == 'ZERO' or meta['status'] == 'NOT_FOUND'):
            raise AddressNotFoundException('No imagery available for ' +
                coords)
        else:
            raise MetaDataRetrievalException('An error occurred retrieving' +
                'address metadata. The error was: ' + meta['status'])

def string_coords(self, coordPair):
    return coordPair if isinstance(coordPair, basestring) \
                     else ','.join(map(str, coordPair))
