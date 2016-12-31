from math import sin, cos, radians, degrees, atan2

from haversine import haversine
from adapter import GoogleAdapter

# I HOPE HOPE HOPE this class can go away at some point
# All it does is make network calls to blindly guess which way a street is
# going
class BearingEstimator:
    # Some magic numbers here; chosen by trial and error
    DEFAULT_NUM_TESTS = 20
    DEFAULT_TEST_DISTANCE = 3

    def __init__(self, apiKey, numTests = DEFAULT_NUM_TESTS,
                 testDistance = DEFAULT_TEST_DISTANCE):
        self.adapter = GoogleAdapter(apiKey)
        self.numTests = numTests
        self.testDistance = testDistance

    def check_bearing(self, coords):
        # We're interested in co-ordinates along the nearest road
        nearestRoad = self.nearest_road([coords])
        placeID = nearestRoad[0]['placeId']
        roadCoords = (nearestRoad[0]['location']['latitude'],
                      nearestRoad[0]['location']['longitude'])

        testCoords = self.calculate_test_coords(roadCoords)
        testRoads = self.nearest_road(testCoords)
        # Different placeID means we're on a different part of the road
        # polyline, potentially with a different bearing, or on a different
        # road altogether
        testRoads = self.filter_roads(testRoads, placeID)

        # If there's no matching roads (it can happen, especially at large
        # intersections), there's no real way to determine the bearing
        if len(testRoads) == 0:
            return 0

        # We want the furthest-away location that's still on the same road
        # segment because it should give us the most accurate bearing
        distances = [{'coords': testRoad['coords'],
                      'distance': haversine(roadCoords, testRoad['coords'])}
                     for testRoad in testRoads]
        furthestPoint = max(distances, key=lambda x:x['distance'])
        return self.calculate_initial_bearing(roadCoords,
                                              furthestPoint['coords'])

    def filter_roads(self, roads, targetPlaceID):
        filtered = []
        for road in roads:
            if road['placeId'] == targetPlaceID:
                # While we're at it, turn the location into a (lat, long) tuple
                road['coords'] = (road['location']['latitude'],
                                    road['location']['longitude'])
                filtered.append(road)
        return filtered
                

    def nearest_road(self, coord_set):
        return self.adapter.nearest_roads(coord_set)

    # Since the distances involved are so small, we can just use standard
    # trig formulae here and not worry about the geosphere
    def calculate_test_coords(self, coords):
        testCoords = []
        angles = [radians(360.0/self.numTests * i)
                  for i in range(0, self.numTests)]
        for angle in angles:
            xDist = sin(angle) * self.testDistance
            yDist = cos(angle) * self.testDistance
            # Quick and dirty hack for short distances
            # 1 degree latitude is approx. 111111 metres
            # 1 degree longitude is approx. 111111 * cos(latitude) meters
            # At small distances of a few meters the error is so
            # inconsequential as to be irrelevant
            newLong = coords[0] + xDist/(111111.0 * cos(radians(coords[1])))
            testCoords.append((newLong, coords[1] + yDist/111111.0))
        return testCoords

    # Since all our points are really close together, we only care about the
    # initial bearing because it's the same as our final
    def calculate_initial_bearing(self, first, second):
        first = map(radians, first)
        second = map(radians, second)
        deltaLong = second[1] - first[1]

        # Formula for calculating bearing borrowed from
        # igismap.com/formula-to-find-bearing-or-heading-angle-between-two-
        # points-latitude-longitude
        return degrees(atan2(cos(second[0]) * sin(deltaLong),
                             cos(first[0]) * sin(second[0]) -
                                 sin(first[0]) * cos(second[0]) *
                                 cos(deltaLong)))

    def string_coords(self, coords):
        return coords if isinstance(coords, basestring) \
                      else ','.join(map(str, coords))
