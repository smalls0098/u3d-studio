import io
import struct


class EndianBinaryWriter:
    # 大小端：也就是字节序->从左或者右读取
    endian: str
    # 流长度
    length: int
    # 流位置
    position: int
    # 数据流
    stream: io.BufferedReader

    def __init__(self, data=b"", endian=">"):
        if isinstance(data, (bytes, bytearray)):
            self.stream = io.BytesIO(data)
            self.stream.seek(0, 2)
        else:
            raise ValueError("Invalid input type - %s." % type(data))
        self.endian = endian
        self.position = self.stream.tell()

    @property
    def bytes(self):
        self.stream.seek(0)
        return self.stream.read()

    @property
    def Length(self) -> int:
        pos = self.stream.tell()
        self.stream.seek(0, 2)
        l = self.stream.tell()
        self.stream.seek(pos)
        return l

    def dispose(self):
        self.stream.close()

    def write(self, *args):
        if self.position != self.stream.tell():
            self.stream.seek(self.position)
        res = self.stream.write(*args)
        self.position = self.stream.tell()
        return res

    def writeByte(self, value: int):
        self.write(struct.pack(self.endian + "b", value))

    def writeUByte(self, value: int):
        self.write(struct.pack(self.endian + "B", value))

    def writeBytes(self, value: bytes):
        return self.write(value)

    def writeShort(self, value: int):
        self.write(struct.pack(self.endian + "h", value))

    def writeInt(self, value: int):
        self.write(struct.pack(self.endian + "i", value))

    def writeLong(self, value: int):
        self.write(struct.pack(self.endian + "q", value))

    def writeUShort(self, value: int):
        self.write(struct.pack(self.endian + "H", value))

    def writeUInt(self, value: int):
        self.write(struct.pack(self.endian + "I", value))

    def writeULong(self, value: int):
        self.write(struct.pack(self.endian + "Q", value))

    def writeFloat(self, value: float):
        self.write(struct.pack(self.endian + "f", value))

    def writeDouble(self, value: float):
        self.write(struct.pack(self.endian + "d", value))

    def writeBoolean(self, value: bool):
        self.write(struct.pack(self.endian + "?", value))

    def writeStringToNull(self, value: str):
        self.write(value.encode("utf8"))
        self.write(b"\0")

    def writeAlignedString(self, value: str):
        self.writeInt(len(value))
        self.write(value.encode("utf8", "backslashreplace"))
        self.alignStream(4)

    def alignStream(self, alignment=4):
        pos = self.stream.tell()
        mod = pos % alignment
        if mod != 0:
            self.write(b"\0" * (alignment - mod))

    def write_array(self, command, value: list, write_length: bool = True):
        if write_length:
            self.writeInt(len(value))
        for val in value:
            command(val)
