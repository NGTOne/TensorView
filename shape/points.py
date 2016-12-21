import fiona
import pyproj
from fiona.crs import from_epsg, to_string

from exception import MissingReferenceException

class PointSet:
    # WGS84 projection used by GPS and Google Earth
    WGS84 = pyproj.Proj('+init=EPSG:4326')

    def __init__(self):
        pass

    def retrieve_from_shapefile(self, shapefile):
        contents = fiona.open(shapefile, 'r')
        if not contents.crs:
            raise MissingReferenceException('Provided shapefile has no '
                                            'reference data.')
        return self.convert_to_WGS84(contents, to_string(contents.crs))

    def retrieve_from_unreferenced_shapefile(self, shapefile, epsg):
        return self.convert_to_WGS84(fiona.open(shapefile, 'r'),
                                     to_string(from_epsg(epsg)))

    def convert_to_WGS84(self, contents, proj4String):
        inputProj = pyproj.Proj(proj4String)
        self.latLong = [
            {'coords': pyproj.transform(inputProj, self.WGS84,
                                        point['geometry']['coordinates'][0],
                                        point['geometry']['coordinates'][1])
                       [::-1]} # Reverse it because pyproj returns (long, lat)
        for point in contents]
        return self
