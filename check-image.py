from image.tf import TFImageRecognizer
import sys

if len(sys.argv) < 5:
    raise ValueError('Usage: python check-image.py <model-file> <label-file> <top-n> <image-file>')

reco = TFImageRecognizer(sys.argv[1], sys.argv[2])
print reco.top_n(sys.argv[4], int(sys.argv[3]))
