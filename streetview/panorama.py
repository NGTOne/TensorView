import os

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
                if os.path.isfile(os.path.join(self.imgDir, f))]

    def addImage(self, filename):
        self.files.append(filename)

    def fileCount(self):
        return len(self.files)

    def clearCache(self):
        # We don't want to delete the directory because we'll likely be writing
        # to it again soon anyways
        for f in self.files:
            os.remove(os.path.join(self.imgDir, f))
            self.files.remove(f)
