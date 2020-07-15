from .SerializedFileHeader import SerializedFileHeader
from ...streams import EndianBinaryReader, EndianBinaryWriter


class LocalSerializedObjectIdentifier:  # script type
    localSerializedFileIndex: int
    localIdentifierInFile: int

    def __init__(self, header: SerializedFileHeader, reader: EndianBinaryReader):
        self.localSerializedFileIndex = reader.readInt()
        if header.version < 14:
            self.localIdentifierInFile = reader.readInt()
        else:
            reader.alignStream()
            self.localIdentifierInFile = reader.readLong()

    def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter):
        writer.writeInt(self.localSerializedFileIndex)
        if header.version < 14:
            writer.writeInt(self.localIdentifierInFile)
        else:
            writer.alignStream()
            writer.writeLong(self.localIdentifierInFile)
