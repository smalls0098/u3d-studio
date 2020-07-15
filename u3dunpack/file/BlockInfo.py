import struct

from ..streams import EndianBinaryReader


class BlockInfo:
    """
    每个压缩块的信息
    """
    compressedSize: int
    uncompressedSize: int
    flag: int

    def __init__(self, reader: EndianBinaryReader):
        self.uncompressedSize = reader.readUInt()
        self.compressedSize = reader.readUInt()
        self.flag = reader.readShort()

    def blockByte(self) -> bytes:
        return struct.pack(">i", self.uncompressedSize) + struct.pack(">i", self.compressedSize) + struct.pack(">h",
                                                                                                               self.flag)
