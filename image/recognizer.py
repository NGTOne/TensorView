# This one's just meant to act as a wrapper around TensorFlow and any other
# image-recognition stuff, so it's pretty minimal

from tf import TFImageRecognizer

class ImageRecognizer:
    DEFAULT_TOP_N = 5 # Cribbed from the TensorFlow image-recognition example

    def __init__(self, interestingCategories, modelFile, threshold, topN = 5):
        self.interestingCategories = interestingCategories
        self.model = TFImageRecognizer(modelFile)
        self.threshold = threshold
        self.topN = topN

    def find_interesting_panoramas(self, panos):
        interesting = [(pano.coords, self.find_interesting_headings(pano))
                          for pano in panos]
        return [coords for coords in interesting if coords[1] is not None]

    def find_interesting_headings(self, pano):
        headings = zip(pano.headings(), pano.full_slice_names())
        return [heading[0] for heading in headings
                   if self.is_image_interesting(heading[1])] or None

    def is_image_interesting(self, filename):
        bestGuesses = self.model.top_n(filename, self.topN)
        for guess in bestGuesses:
            intersect = [cat for cat in self.interestingCategories
                            if cat in guess[0]]
            if (intersect and guess[1] >= self.threshold):
                return True
        return False
