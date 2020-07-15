## Installation

**需要Python 3.6.0或更高版本**

```
pip install u3d-studio
```

或下载/克隆git并使用

```
python setup.py install
```

## 使用说明

来一个简单的示例

```python
import os

from u3dunpack import AssetsManager

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
KTX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ktx")


def testTexture2d():
    for f in os.listdir(SAMPLES):
        am = AssetsManager(os.path.join(SAMPLES, f))
        for asset in am.assets.values():
            for obj in asset.objects.values():
                if obj.type == "Texture2D":
                    # 解析对象数据
                    data = obj.read()
                    # 确保扩展名正确
                    # 您可能只想使用图像/纹理
                    dest, ext = os.path.splitext(data.name)
                    destImg = dest + ".png"
                    destImg = os.path.join(IMG, destImg)
                    img = data.image.save(destImg)

                    destKtx = os.path.join(KTX, dest) + ".ktx"
                    if os.path.exists(destKtx):
                        os.remove(destKtx)
                    with open(destKtx, mode='wb') as w:
                        w.write(data.saveKtx)

                    with open(destKtx, mode='rb') as r:
                        ktxData = r.read()
                    data.writeData(ktxData)
            with open("assets/test", mode='wb') as w:
                data = asset.bundleFile.save()
                w.write(data)


if __name__ == '__main__':
    testTexture2d()
```
