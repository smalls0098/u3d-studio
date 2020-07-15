import struct

from ..streams import EndianBinaryReader
from ..utils.ResourceReader import getResourceData
from ..writer import ResourceConverter
from .Texture import Texture
from .GLTextureSettings import GLTextureSettings
from .StreamingInfo import StreamingInfo
from ..enums import TextureFormat
from ..export import Texture2DConverter, KtxConverter
from ..streams import EndianBinaryWriter


class Texture2D(Texture):
    # 宽度
    m_Width: int
    # 高度
    m_Height: int
    m_CompleteImageSize: int
    m_TextureFormat: TextureFormat
    m_IsReadable: bool
    m_ReadAllowed: bool
    m_ImageCount: int
    m_TextureDimension: int
    m_TextureSettings: GLTextureSettings

    imageData: bytes

    @property
    def image(self):
        return Texture2DConverter.getImageFromTexture2d(self)

    @property
    def saveKtx(self):
        return KtxConverter.makeKtx(self)

    def writeData(self, ktxData):
        ResourceConverter.makeNewImageData(self, ktxData)

    @image.setter
    def image(self, img):
        # img is PIL.Image
        # 用RGB（A）图像数据覆盖原始图像数据并设置正确的新格式
        # 暂时不可用
        writer = EndianBinaryWriter()
        for pix in img.getdata():
            for val in pix:
                writer.writeUByte(val)
        self.imageData = writer.bytes
        self.m_TextureFormat = (TextureFormat.RGBA32 if len(pix) == 4 else TextureFormat.RGB24)

    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        version = self.version
        self.m_Width = reader.readInt()
        self.m_Height = reader.readInt()
        self.m_CompleteImageSize = reader.readInt()
        self.m_TextureFormat = TextureFormat(reader.readInt())
        if version[0] < 5 or (version[0] == 5 and version[1] < 2):  # 5.2 down
            self.m_MipMap = reader.readBoolean()
        else:
            self.m_MipCount = reader.readInt()
        self.m_IsReadable = reader.readBoolean()  # 2.6.0 and up
        self.m_ReadAllowed = reader.readBoolean()  # 3.0.0 - 5.4
        # bool m_StreamingMipmaps 2018.2 and up
        reader.alignStream()
        if version[0] > 2018 or (
                version[0] == 2018 and version[1] >= 2
        ):  # 2018.2 and up
            self.m_StreamingMipmapsPriority = reader.readInt()
        self.m_ImageCount = reader.readInt()
        self.m_TextureDimension = reader.readInt()
        self.m_TextureSettings = GLTextureSettings(reader, version)
        if version[0] >= 3:  # 3.0 and up
            self.m_LightmapFormat = reader.readInt()
        if version[0] > 3 or (version[0] == 3 and version[1] >= 5):  # 3.5.0 and up
            self.m_ColorSpace = reader.readInt()

        imageDataSize = reader.readInt()
        self.imageData = b""
        if imageDataSize == 0 and (
                (version[0] == 5 and version[1] >= 3) or version[0] > 5
        ):  # 5.3.0 and up
            m_StreamData = StreamingInfo(reader)

            self.imageData = getResourceData(
                m_StreamData.path,
                self.assets_file,
                m_StreamData.offset,
                m_StreamData.size,
            )
        else:
            self.imageData = reader.readBytes(imageDataSize)

    def save(self, writer: EndianBinaryWriter = None, **kwargs):
        if writer is None:
            writer = EndianBinaryWriter()
        super().save(writer, )
        version = self.version
        writer.writeInt(self.m_Width)
        writer.writeInt(self.m_Height)
        writer.writeInt(self.m_CompleteImageSize)
        writer.write(struct.pack("<i", int(self.m_TextureFormat)))
        if version[0] < 5 or (version[0] == 5 and version[1] < 2):  # 5.2 down
            writer.writeBoolean(self.m_MipMap)
        else:
            writer.writeInt(self.m_MipCount)
        writer.writeBoolean(self.m_IsReadable)  # 2.6.0 and up
        writer.writeBoolean(self.m_ReadAllowed)  # 3.0.0 - 5.4
        # bool m_StreamingMipmaps 2018.2 and up
        writer.alignStream()
        if version[0] > 2018 or (
                version[0] == 2018 and version[1] >= 2
        ):  # 2018.2 and up
            writer.writeInt(self.m_StreamingMipmapsPriority)
        writer.writeInt(self.m_ImageCount)
        writer.writeInt(self.m_TextureDimension)
        self.m_TextureSettings.save(writer, version)
        if version[0] >= 3:  # 3.0 and up
            writer.writeInt(self.m_LightmapFormat)
        if version[0] > 3 or (version[0] == 3 and version[1] >= 5):  # 3.5.0 and up
            writer.writeInt(self.m_ColorSpace)
        writer.writeInt(len(self.imageData))
        writer.writeBytes(self.imageData)
        writer.writeLong(0)
        writer.writeInt(0)
