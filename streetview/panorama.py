import os
import re

class Panorama:
    def __init__(self, panID, imgDir):
        self.panID = panID
        self.imgDir = imgDir

        if (not os.path.isdir(imgDir)):
            try:
                os.makedirs(imgDir)
            except OSError:
                raise OSError('Could not create directory for panorama images.')

        self.files = self.findFiles()

    def findFiles(self):
        return [f for f in os.listdir(self.imgDir)
                if (os.path.isfile(os.path.join(self.imgDir, f))
                    and re.match('^\d+\.\d+\.jpg$', f, re.IGNORECASE))]
                    # Regex only matches files that are named after headings

    def addImage(self, filename):
        self.files.append(filename)

    def fileCount(self):
        return len(self.files)

    def clearCache(self, headings):
        # We don't want to delete the directory because we'll likely be writing
        # to it again soon anyways
        safeImages = []
        if (len(headings) == self.fileCount()):
           images = [str(heading) + '.jpg' for heading in headings]
           safeImages = [image for image in images if image in self.files]

        for f in self.files:
            if f not in safeImages:
                os.remove(os.path.join(self.imgDir, f))
        self.files = [f for f in self.files if f in safeImages]
