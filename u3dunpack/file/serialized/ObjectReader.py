from ... import engine
from ...enums import ClassIDType
from ..serialized import SerializedFile
from .SerializedType import SerializedType
from ...streams import EndianBinaryReader, EndianBinaryWriter


class ObjectReader:
    byteStart: int
    byteSize: int
    typeId: int
    classId: ClassIDType
    pathId: int
    serializedFile: SerializedFile
    reader: EndianBinaryReader
    data: bytes

    def __init__(self, reader: EndianBinaryReader, serializedFile: SerializedFile):
        self.serializedFile = serializedFile
        self.reader = reader
        self.data = b""
        self.version = serializedFile.version
        self.version2 = serializedFile.serializedHeader.version
        self.platform = serializedFile.targetPlatform
        self.buildType = serializedFile.buildType

        header = serializedFile.serializedHeader

        types = serializedFile.types

        if header.version < 14:
            self.pathId = reader.readInt()
        else:
            reader.alignStream()
            self.pathId = reader.readLong()

        self.byteStart = reader.readUInt()
        self.byteStart += header.dataOffset
        self.byteSize = reader.readUInt()
        self.typeId = reader.readInt()
        if header.version < 16:
            self.classId = reader.readUShort()
            if types:
                self.serializedType = [x for x in types if x.classId == self.typeId][0]
            else:
                self.serializedType = SerializedType
            self.isDestroyed = reader.readUShort()
        else:
            typ = types[self.typeId]
            self.serializedType = typ
            self.classId = typ.classId

        self.type = ClassIDType(self.classId)

        if header.version == 15 or header.version == 16:
            self.stripped = reader.readByte()

    def write(self, header, writer, dataWriter):
        self.save()
        # 写出数据
        # validated
        if header.version < 14:
            writer.writeInt(self.pathId)
        else:
            writer.alignStream()
            writer.writeLong(self.pathId)
        if self.data:
            data = self.data
        else:
            self.reset()
            data = self.reader.read(self.byteSize)
        writer.writeUInt(dataWriter.position)
        writer.writeUInt(len(data))
        dataWriter.write(data)

        writer.writeInt(self.typeId)

        if header.version < 16:
            # 警告-如果未知，经典类型可能会更改数字
            writer.writeUShort(self.classId)
            writer.writeUShort(self.isDestroyed)

        if header.version == 15 or header.version == 16:
            writer.writeByte(self.stripped)

    @property
    def container(self):
        return (
            self.serializedFile._container[self.pathId]
            if self.pathId in self.serializedFile._container
            else None
        )

    def reset(self):
        self.reader.position = self.byteStart

    def read(self):
        self.engineObject = getattr(engine, self.type.name, engine.Object)(self)
        return self.engineObject

    def save(self):
        if int(self.classId) == 28:
            if self.engineObject:
                writer = EndianBinaryWriter(b"", '<')
                self.engineObject.save(writer)
                self.data = writer.bytes
                writer.dispose()

    def __getattr__(self, item: str):
        if hasattr(self.reader, item):
            return getattr(self.reader, item)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.type.name)
