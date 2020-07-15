from ...streams import EndianBinaryReader


class SerializedFileHeader:

    metadataSize: int
    fileSize: int
    version: int
    dataOffset: int
    endian: bytes
    reserved: bytes

    def __init__(self, reader: EndianBinaryReader):
        self.metadataSize = reader.readUInt()
        self.fileSize = reader.readUInt()
        self.version = reader.readUInt()
        self.dataOffset = reader.readUInt()
