import urllib
import json
import os

from exception import AddressNotFoundException, MetaDataRetrievalException

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

    def nearest_roads(self, coords):
        string_coord_set = [self.string_coords(coord) for coord in coords] \
                           if not isinstance(coords, basestring) else coords
        url = self.url('roads', 'v1/nearestRoads',
                       {'points': '|'.join(string_coord_set)})
        return self.call_json(url)['snappedPoints']

    def string_coords(self, coordPair):
        return coordPair if isinstance(coordPair, basestring) \
                      else ','.join(map(str, coordPair))
