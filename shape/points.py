import fiona
import pyproj

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
        return self.convert_to_WGS84(contents,
                                     fiona.crs.to_string(contents.crs))

    def retrieve_from_unreferenced_shapefile(self, shapefile, epsg):
        return self.convert_to_WGS84(fiona.open(shapefile, 'r'),
                                     '+init=EPSG:' + str(epsg))

    def convert_to_WGS84(self, contents, proj4String):
        inputProj = pyproj.Proj(proj4String)
        self.latLong = [
            {'coords': pyproj.transform(inputProj, self.WGS84,
                                        point['geometry']['coordinates'][0],
                                        point['geometry']['coordinates'][1])
                       [::-1], # Reverse it because pyproj returns (long, lat)
             'forward_heading': 0} # TODO: Grab this if it exists
        for point in contents]
        return self
