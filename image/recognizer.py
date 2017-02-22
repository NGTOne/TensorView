# This one's just meant to act as a wrapper around TensorFlow and any other
# image-recognition stuff, so it's pretty minimal

from tf import TFImageRecognizer
from exception import InvalidCategoryError, InvalidModeError

class ImageRecognizer:
    DEFAULT_TOP_N = 5 # Cribbed from the TensorFlow image-recognition example
    MODES = ['individual', 'summing']

    def __init__(self, interestingCategories, modelFile, labelFile, threshold,
                 **kwargs):
        self.model = TFImageRecognizer(modelFile, labelFile)
        self.interestingCategories = interestingCategories
        self.threshold = threshold
        self.topN = kwargs.get('topN', self.DEFAULT_TOP_N)

        mode = kwargs.get('mode', 'individual')
        if mode not in self.MODES:
            raise InvalidModeError('Invalid thresholding mode. Valid modes are '
                                   + str(self.MODES))
        self.mode = mode

        invalidCategories = [cat for cat in interestingCategories
                                 if cat not in self.model.lookup]
        if invalidCategories:
            raise InvalidCategoryError('Categories ' + str(invalidCategories) +
                                       ' do not exist in the model! If '
                                       'somebody else provided you with this '
                                       'model, have them provide you with a '
                                       'list of the categories they used.')

    def find_interesting_panoramas(self, panos):
        interesting = [(pano, self.find_interesting_headings(pano))
                          for pano in panos]
        return [coords for coords in interesting if coords[1] is not None]

    def find_interesting_headings(self, pano):
        headings = zip(pano.headings(), pano.full_slice_names())
        interesting = []
        for heading in headings:
            isItInteresting = self.is_image_interesting(heading[1])
            if (isItInteresting):
                interesting.append((heading[0], isItInteresting))
        return interesting or None

    def is_image_interesting(self, filename):
        bestGuesses = self.model.top_n(filename, self.topN)
        certainty = self.calculate_certainty(bestGuesses)
        if (certainty >= self.threshold):
            intersect = [guess for guess in bestGuesses
                         if guess[0] in self.interestingCategories]
            return (intersect, certainty)
        return False

    def calculate_certainty(self, bestGuesses):
        # TODO: Refactor this
        certainties = [guess[1] for guess in bestGuesses
                       if guess[0] in self.interestingCategories]
        if (self.mode == 'individual'):
            return max(certainties) if certainties else 0
        elif (self.mode == 'summing'):
            return sum(certainties) if certainties else 0
