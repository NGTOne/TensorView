import os

class Panorama:
    def __init__(self, panID, imgDir, checkCache = False):
        self.panID = panID
        self.imgDir = imgDir

        if (not os.path.isdir(imgDir)):
            try:
                os.makedirs(imgDir)
            except OSError:
                raise OSError('Could not create directory for panorama images.')

        self.files = self.findFiles() if checkCache else []

    def findFiles(self):
        return None

    def addImage(self, filename):
        self.files.append(filename)
