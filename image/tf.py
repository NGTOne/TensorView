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
    def __init__(self, modelFile, labelFile):
        super(TFImageRecognizer, self).__init__(modelFile)
        self.load_lookup(labelFile)

    def load_lookup(self, labelFile):
        with open(labelFile, 'r') as f:
            self.lookup = f.readlines()

    def top_n(self, imgFilename, n):
        if not tf.gfile.Exists(imgFilename):
            raise IOError('Image file ' + imgFilename + ' does not exist!')
        img = tf.gfile.FastGFile(imgFilename, 'rb').read()

        with self.session() as sess:
            outputLayer = sess.graph.get_tensor_by_name('final_result:0')
            predictions = sess.run(outputLayer, {'DecodeJpeg/contents:0': img})

            predictions = np.squeeze(predictions)
            top = predictions.argsort()[-n:][::-1]
            return [(self.lookup_node_ID(nodeID), predictions[nodeID])
                   for nodeID in top]

    def lookup_node_ID(self, ID):
        return self.lookup[ID]
