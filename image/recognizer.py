class ImageRecognizer:
    def __init__(self, interestingCategories):
        self.interestingCategories = interestingCategories

    def find_interesting_panoramas(self, panos):
        interesting = [(pano.coords, self.find_interesting_headings(pano))
                      for pano in panos]
        return [coords for coords in interesting if coords[1] is not None]

    def find_interesting_headings(self, pano):
        headings = zip(pano.headings(), pano.full_filenames())
        return [heading[0] for heading in headings
                if self.is_image_interesting(heading[1])] or None
