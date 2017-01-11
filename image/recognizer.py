# This one's just meant to act as a wrapper around TensorFlow and any other
# image-recognition stuff, so it's pretty minimal

from tf import TFImageRecognizer
from exception import InvalidCategoryError

class ImageRecognizer:
    DEFAULT_TOP_N = 5 # Cribbed from the TensorFlow image-recognition example

    def __init__(self, interestingCategories, modelFile, labelFile, threshold,
                 topN = 5):
        self.model = TFImageRecognizer(modelFile, labelFile)
        self.interestingCategories = interestingCategories
        self.threshold = threshold
        self.topN = topN

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
        for guess in bestGuesses:
            intersect = [cat for cat in self.interestingCategories
                            if cat == guess[0]]
            if (intersect and guess[1] >= self.threshold):
                return (intersect, guess[1])
        return False
