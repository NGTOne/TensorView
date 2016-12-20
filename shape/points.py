import fiona
import utm

class PointSet:
    def __init__(self, shapefile, wgsZone, wgsLetter):
        contents = fiona.open(shapefile, 'r')
        # Since we're not expecting the shapefile to change while we're
        # operating, we'll just cache its contents
        # TODO: Clean this up a little
        # TODO: Work different co-ordinate systems into this
        self.latLong = [
                {'coords': utm.to_latlon(point['geometry']['coordinates'][0],
                                         point['geometry']['coordinates'][1],
                                         wgsZone, wgsLetter),
                 'forward_heading': 0} # TODO: Read this in if it exists
            for point in contents]

    def getPointCoordinates(self):
        return self.latLong
