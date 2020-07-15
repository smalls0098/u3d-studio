from .NamedObject import NamedObject
from ..streams import EndianBinaryWriter


class Texture(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        if self.version[0] > 2017 or (
                self.version[0] == 2017 and self.version[1] >= 3
        ):  # 2017.3 and up
            self.forcedFallbackFormat = reader.readInt()
            self.downscaleFallback = reader.readBoolean()
            reader.alignStream()

    def save(self, writer: EndianBinaryWriter, **kwargs):
        super().save(writer, )
        if self.version[0] > 2017 or (
                self.version[0] == 2017 and self.version[1] >= 3
        ):  # 2017.3 and up
            writer.writeInt(self.forcedFallbackFormat)
            writer.writeBoolean(self.downscaleFallback)
            writer.alignStream()
