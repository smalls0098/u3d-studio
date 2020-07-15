import io
import struct


class EndianBinaryReader:
    # 大小端：也就是字节序->从左或者右读取
    endian: str
    # 流长度
    length: int
    # 流位置
    position: int
    # 数据流
    stream: io.BufferedReader

    def __init__(self, data, endian='>'):
        if data is None:
            raise Exception("data数据不能为空")
        if isinstance(data, (bytes, bytearray)):
            self.stream = io.BytesIO(data)
        elif isinstance(data, (io.BytesIO, io.BufferedReader)):
            self.stream = data
        else:
            raise Exception("data未知类型" + type(data))
        # 初始化数据
        self.endian = endian
        self.length = self.stream.seek(0, 2)
        self.position = 0

    def getPosition(self):
        return self.stream.tell()

    def setPosition(self, value):
        self.stream.seek(value)

    position = property(getPosition, setPosition)

    @property
    def bytes(self):
        lastPos = self.position
        self.position = 0
        res = self.read()
        self.position = lastPos
        return res

    def read(self, *args):
        return self.stream.read(*args)

    def dispose(self):
        self.stream.close()

    def readByte(self) -> int:
        return struct.unpack(self.endian + "b", self.read(1))[0]

    def readUByte(self) -> int:
        return struct.unpack(self.endian + "B", self.read(1))[0]

    def readBytes(self, num) -> bytes:
        return self.read(num)

    def readShort(self) -> int:
        return struct.unpack(self.endian + "h", self.read(2))[0]

    def readInt(self) -> int:
        return struct.unpack(self.endian + "i", self.read(4))[0]

    def readLong(self) -> int:
        return struct.unpack(self.endian + "q", self.read(8))[0]

    def readUShort(self) -> int:
        return struct.unpack(self.endian + "H", self.read(2))[0]

    def readUInt(self) -> int:
        return struct.unpack(self.endian + "I", self.read(4))[0]

    def readULong(self) -> int:
        return struct.unpack(self.endian + "Q", self.read(8))[0]

    def readFloat(self) -> float:
        return struct.unpack(self.endian + "f", self.read(4))[0]

    def readDouble(self) -> float:
        return struct.unpack(self.endian + "d", self.read(8))[0]

    def readBoolean(self) -> bool:
        return bool(struct.unpack(self.endian + "?", self.read(1))[0])

    def readString(self, size=None, encoding="utf-8") -> str:
        if size is None:
            res = self.readStringToNull()
        else:
            res = struct.unpack(f"{self.endian}{size}is", self.read(size))[0]
        try:
            return res.decode(encoding)
        except UnicodeDecodeError:
            return res

    def readStringToNull(self, max_length=32767) -> str:
        ret = []
        c = b""
        while c != b"\0" and len(ret) < max_length and self.position != self.length:
            ret.append(c)
            c = self.read(1)
            if not c:
                raise ValueError("Unterminated string: %r" % ret)
        return b"".join(ret).decode("utf8", "replace")

    def readAlignedString(self):
        length = self.readInt()
        if 0 < length <= self.length - self.position:
            data = self.readBytes(length)
            result = data.decode("utf8", "backslashreplace")
            self.alignStream(4)
            return result
        return ""

    def alignStream(self, alignment=4):
        pos = self.position
        mod = pos % alignment
        if mod != 0:
            self.position += alignment - mod

    @staticmethod
    def readArray(command, length: int):
        return [command() for i in range(length)]
