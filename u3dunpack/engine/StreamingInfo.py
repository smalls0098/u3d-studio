from ..streams import EndianBinaryReader


class StreamingInfo:
    offset: int = 0
    size: int = 0
    path: str = ""

    def __init__(self, reader: EndianBinaryReader):
        self.offset = reader.readUInt()
        self.size = reader.readUInt()
        self.path = reader.readAlignedString()
