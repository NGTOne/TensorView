# Wish more of the image classifier was reusable, but whatever
from tensorflow.models.image.imagenet.classify_image import NodeLookup
import tensorflow as tf
import numpy as np
import os

class TFModel(object):
    def __init__(self, modelFile):
        # These are potentially expensive, and we only need to do them once
        self.load_model(modelFile)

    def load_model(self, modelFile):
        modelF = tf.gfile.FastGFile(modelFile, 'rb')
        gDef = tf.GraphDef()
        gDef.ParseFromString(modelF.read())
        tf.import_graph_def(gDef, name = '')
        self.graph = tf.get_default_graph()

    def session(self):
        return tf.Session(graph = self.graph)

class TFImageRecognizer(TFModel):
    def __init__(self, modelFile):
        super(TFImageRecognizer, self).__init__(modelFile)
        self.load_lookup(modelFile)

    def load_lookup(self, modelFile):
        splitPath = os.path.split(modelFile)
        modelName = splitPath[1]
        baseFilename = modelName.replace('.pb', '')
        # The TF node lookup takes the UID-to-integer mapfile first, then the
        # integer-to-readable-string mapfile
        self.lookup = NodeLookup(os.path.join(splitPath[0],
                                              baseFilename + '.pbtxt'),
                                 os.path.join(splitPath[0],
                                              baseFilename + '.txt'))

    def top_n(self, imgFilename, n):
        if not tf.gfile.Exists(imgFilename):
            raise IOError('Image file ' + imgFilename + ' does not exist!')
        img = tf.gfile.FastGFile(imgFilename, 'rb').read()

        with self.session() as sess:
            softmax = sess.graph.get_tensor_by_name('softmax:0')
            predictions = sess.run(softmax, {'DecodeJpeg/contents:0': img})

            predictions = np.squeeze(predictions)
            top = predictions.argsort()[-n:][::-1]
            return [(self.lookup.id_to_string(nodeID).split(', '),
                     predictions[nodeID])
                   for nodeID in top]
