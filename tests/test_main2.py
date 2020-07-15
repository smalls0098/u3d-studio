import os

import u3dunpack

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
KTX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ktx")


def testTexture2d():
    for f in os.listdir(SAMPLES):
        am = u3dunpack.load(os.path.join(SAMPLES, f))
        for asset in am.assets.values():
            with open("assets/test1", mode='wb') as w:
                data = asset.bundleFile.save(False)
                w.write(data)


if __name__ == '__main__':
    testTexture2d()
