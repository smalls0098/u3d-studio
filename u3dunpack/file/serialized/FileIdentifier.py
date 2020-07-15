import os

from .SerializedFileHeader import SerializedFileHeader
from ...streams import EndianBinaryReader, EndianBinaryWriter


class FileIdentifier:
    guid: bytes
    type: int
    path: str

    @property
    def name(self):
        return os.path.basename(self.path)

    def __init__(self, header: SerializedFileHeader, reader: EndianBinaryReader):
        if header.version >= 6:
            self.tempEmpty = reader.readStringToNull()
        if header.version >= 5:
            self.guid = reader.readBytes(16)
            self.type = reader.readInt()
        self.path = reader.readStringToNull()

    def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter):
        if header.version >= 6:
            writer.writeStringToNull(self.tempEmpty)
        if header.version >= 5:
            writer.writeBytes(self.guid)
            writer.writeInt(self.type)
        writer.writeStringToNull(self.path)
