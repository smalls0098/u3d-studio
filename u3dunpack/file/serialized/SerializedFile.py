import re
import sys

from .. import BundleFile
from ..BuildType import BuildType
from ...enums import BuildTarget, ClassIDType
from ...file.ResourcesFile import ResourcesFile
from .FileIdentifier import FileIdentifier
from .LocalSerializedObjectIdentifier import LocalSerializedObjectIdentifier
from .ObjectReader import ObjectReader
from .SerializedFileHeader import SerializedFileHeader
from .SerializedType import SerializedType
from .TypeTreeNode import TypeTreeNode
from ...streams import EndianBinaryReader, EndianBinaryWriter
from ... import AssetsManager
from ...utils.SerializedUtils import readString

RECURSION_LIMIT = sys.getrecursionlimit()


class SerializedFile(ResourcesFile):
    assetsManager: AssetsManager
    bundleFile: BundleFile
    reader: EndianBinaryReader
    targetPlatform: BuildTarget
    unityVersion: str
    version: []
    buildType: BuildType
    serializedHeader: SerializedFileHeader

    types: dict
    container: dict
    _container: dict

    def __init__(self, reader: EndianBinaryReader, assetsManager: AssetsManager, bundleFile: BundleFile):
        self.assetsManager = assetsManager
        self.bundleFile = bundleFile
        self.reader = reader

        self.unityVersion = "2.5.0f5"
        self.version = [0, 0, 0, 0]
        self.buildType = BuildType("")
        self.targetPlatform = BuildTarget.UnknownPlatform

        self.types = []
        self.container = {}
        self._container = {}

        # 用于加快大规模资产提取
        # 一些资产相互参照，因此保持结果
        # 缓存的特定资产提取速度可以大大提高。
        # 由以下用户使用：Sprite（已缓存Texture2D（带有alpha））
        # self._cache = {}

        # ReadHeader
        serializedHeader = SerializedFileHeader(reader)

        self.serializedHeader = serializedHeader

        if serializedHeader.version >= 9:
            serializedHeader.endian = ">" if reader.readBoolean() else "<"
            serializedHeader.reserved = reader.readBytes(3)
        else:
            reader.Position = serializedHeader.fileSize - serializedHeader.metadataSize
            serializedHeader.endian = ">" if reader.readBoolean() else "<"

        reader.endian = serializedHeader.endian

        posStart = reader.position
        if serializedHeader.version >= 7:
            unityVersion = reader.readStringToNull()
            self.setVersion(unityVersion)

        if serializedHeader.version >= 8:
            self._mTargetPlatform = reader.readInt()
            try:
                self._mTargetPlatform = BuildTarget(self._mTargetPlatform)
            except KeyError:
                self._mTargetPlatform = BuildTarget.UnknownPlatform

        if serializedHeader.version >= 13:
            self._enableTypeTree = reader.readBoolean()

        typeCount = reader.readInt()
        self.types = [self.readSerializedType() for _ in range(typeCount)]

        if 7 <= serializedHeader.version < 14:
            self.bigIdEnabled = reader.readInt()

        # ReadObjects
        objectCount = reader.readInt()
        self.objects = {}
        for _ in range(objectCount):
            obj = ObjectReader(reader, self)
            self.objects[obj.pathId] = obj
        # 1
        if serializedHeader.version >= 11:
            scriptCount = reader.readInt()
            self.scriptTypes = [
                LocalSerializedObjectIdentifier(serializedHeader, reader)
                for _ in range(scriptCount)
            ]

            # Read Externals
        externalsCount = reader.readInt()
        self.externals = [
            FileIdentifier(serializedHeader, reader) for _ in range(externalsCount)
        ]

        self.userInformation = reader.readStringToNull()

        # 读取assetBundles以获取容器
        oldPos = reader.position
        reader.position = posStart
        self.metadata = reader.read(oldPos - posStart)
        reader.position = oldPos
        for obj in self.objects.values():
            if obj.type == ClassIDType.AssetBundle:
                data = obj.read()
                for container, assetInfo in data.container.items():
                    asset = assetInfo.asset
                    self.container[container] = asset
                    if hasattr(asset, "pathId"):
                        self._container[asset.pathId] = container
        assetsManager.container = {**self.container}
        reader.position = oldPos

    def setVersion(self, stringVersion: str):
        self.unityVersion = stringVersion
        self.buildType = BuildType(re.findall(r"([^\d.])", stringVersion)[0])
        versionSplit = re.split(r"\D", stringVersion)
        self.version = [int(x) for x in versionSplit]

    def readSerializedType(self):
        typeObj = SerializedType()
        typeObj.classId = self.reader.readInt()

        if self.serializedHeader.version >= 16:
            typeObj.isStrippedType = self.reader.readBoolean()
        if self.serializedHeader.version >= 17:
            typeObj.scriptTypeIndex = self.reader.readShort()

        if self.serializedHeader.version >= 13:
            if (self.serializedHeader.version < 16 and typeObj.classId < 0) or (
                    self.serializedHeader.version >= 16 and typeObj.classId == 114
            ):
                typeObj.scriptId = self.reader.readBytes(16)  # Hash128
            typeObj.oldTypeHash = self.reader.readBytes(16)  # Hash128

        if self._enableTypeTree:
            typeTree = []
            if self.serializedHeader.version >= 12 or self.serializedHeader.version == 10:
                typeObj.stringData = self.readTypeTree5(typeTree)
            else:
                self.readTypeTree(typeTree)
            typeObj.nodes = typeTree
        return typeObj

    def readTypeTree(self, typeTree, level=0):
        if level == RECURSION_LIMIT - 1:
            raise RecursionError

        typeTreeNode = TypeTreeNode()
        typeTree.append(typeTreeNode)
        typeTreeNode.level = level
        typeTreeNode.type = self.reader.readStringToNull()
        typeTreeNode.name = self.reader.readStringToNull()
        typeTreeNode.byteSize = self.reader.readInt()
        if self.serializedHeader.version == 2:
            typeTreeNode.variableCount = self.reader.readInt()

        if self.serializedHeader.version != 3:
            typeTreeNode.index = self.reader.readInt()

        typeTreeNode.isArray = self.reader.readInt()
        typeTreeNode.version = self.reader.readInt()
        if self.serializedHeader.version != 3:
            typeTreeNode.metaFlag = self.reader.readInt()

        childrenCount = self.reader.readInt()
        for i in range(childrenCount):
            self.readTypeTree(typeTree, level + 1)

    def readTypeTree5(self, typeTree):
        numberOfNodes = self.reader.readInt()
        stringBufferSize = self.reader.readInt()

        nodeSize = 24
        if self.serializedHeader.version > 17:
            nodeSize = 32

        self.reader.position += numberOfNodes * nodeSize
        stringBufferReader = EndianBinaryReader(self.reader.read(stringBufferSize))
        self.reader.position -= numberOfNodes * nodeSize + stringBufferSize

        for i in range(numberOfNodes):
            typeTreeNodeObj = TypeTreeNode()
            typeTree.append(typeTreeNodeObj)
            typeTreeNodeObj.version = self.reader.readUShort()
            typeTreeNodeObj.level = self.reader.readByte()
            typeTreeNodeObj.isArray = self.reader.readBoolean()
            typeTreeNodeObj.typeStrOffset = self.reader.readUInt()
            typeTreeNodeObj.nameStrOffset = self.reader.readUInt()
            typeTreeNodeObj.byteSize = self.reader.readInt()
            typeTreeNodeObj.index = self.reader.readInt()
            typeTreeNodeObj.metaFlag = self.reader.readInt()

            if self.serializedHeader.version > 17:
                typeTreeNodeObj.extra = self.reader.read(8)

            typeTreeNodeObj.type = readString(stringBufferReader, typeTreeNodeObj.typeStrOffset)
            typeTreeNodeObj.name = readString(stringBufferReader, typeTreeNodeObj.nameStrOffset)

        self.reader.position += stringBufferSize
        if self.serializedHeader.version >= 21:
            self.reader.position += 4
        return stringBufferReader.bytes

    def save(self) -> bytes:
        # Structure:结构体
        #   1. header 头部
        #       file header 文件头
        #       types 类型
        #       objects 资源对象
        #       scripts 脚本
        #       externals 外部
        #   2. small 0es offset - align stream 小0es偏移量-对齐流
        #   3. objects data 对象数据

        # 调整元数据大小，数据偏移量和文件大小
        header = self.serializedHeader
        types = self.types
        objects = self.objects
        scriptTypes = self.scriptTypes
        externals = self.externals

        # 标头需要数据偏移量，很难计算
        # 因此我们将资产建设分为多个部分
        fileHeaderWriter = EndianBinaryWriter()
        headerWriter = EndianBinaryWriter(endian=header.endian)
        dataWriter = EndianBinaryWriter(endian=header.endian)

        # 1.构建没有文件头的头
        # reader.Position = header.file_size - header.metadata_size
        # header.endian = '>' if reader.read_boolean() else '<'
        if header.version < 9:
            headerWriter.writeBoolean(header.endian == ">")

        if header.version >= 7:
            headerWriter.writeStringToNull(self.unityVersion)

        if header.version >= 8:
            headerWriter.writeInt(self._mTargetPlatform)

        if header.version >= 13:
            headerWriter.writeBoolean(self._enableTypeTree)
        # 类型
        headerWriter.writeInt(len(types))
        for typ in types:
            self.saveSerializedType(typ, header, headerWriter)

        if 7 <= header.version < 14:
            headerWriter.writeInt(self.bigIdEnabled)

        # 对象
        headerWriter.writeInt(len(objects))
        for i, obj in enumerate(objects.values()):
            obj.write(header, headerWriter, dataWriter)
            if i < len(objects) - 1:
                dataWriter.alignStream(8)

        # 脚本
        if header.version >= 11:
            headerWriter.writeInt(len(scriptTypes))
            for scriptType in scriptTypes:
                scriptType.write(header, headerWriter)

        # externals
        headerWriter.writeInt(len(externals))
        for external in externals:
            external.write(header, headerWriter)

        headerWriter.writeStringToNull(self.userInformation)
        if header.version >= 21:
            headerWriter.writeInt(0)

        if header.version >= 9:
            # 文件头
            fileHeaderSize = 4 * 4 + 1 + 3  # 以下+尾数+保留
            metadataSize = headerWriter.Length
            # 元数据大小
            fileHeaderWriter.writeUInt(headerWriter.Length)
            # 在元数据和数据之间对齐
            mod = (fileHeaderSize + metadataSize) % 16
            alignLength = 16 - mod if mod else 0

            # 文件大小
            fileHeaderWriter.writeUInt(
                headerWriter.Length
                + dataWriter.Length
                + fileHeaderSize
                + alignLength
            )

            # 1709264
            # 1708160
            # 1104
            # version
            fileHeaderWriter.writeUInt(header.version)
            # 数据偏移
            fileHeaderWriter.writeUInt(headerWriter.Length + fileHeaderSize + alignLength)

            # endian
            fileHeaderWriter.writeBoolean(header.endian == ">")

            fileHeaderWriter.writeBytes(header.reserved)

            return (
                    fileHeaderWriter.bytes
                    + headerWriter.bytes
                    + b"\x00" * alignLength
                    + dataWriter.bytes
            )
        else:
            # 文件头
            fileHeaderSize = 4 * 4
            metadataSize = headerWriter.Length
            # 元数据大小
            fileHeaderWriter.writeUInt(metadataSize)
            # 文件大小
            fileHeaderWriter.writeUInt(metadataSize + dataWriter.Length + fileHeaderSize)
            # 版本
            fileHeaderWriter.writeUInt(header.version)
            # 数据偏移量-统一似乎可以使流对齐..但是显然没有必要
            fileHeaderWriter.writeUInt(fileHeaderSize)
            return self.bundleFile.save() + fileHeaderWriter.bytes + dataWriter.bytes + headerWriter.bytes

    def saveSerializedType(self, typ: SerializedType, header: SerializedFileHeader, writer: EndianBinaryWriter):

        writer.writeInt(typ.classId)

        if header.version >= 16:
            writer.writeBoolean(typ.isStrippedType)

        if header.version >= 17:
            writer.writeShort(typ.scriptTypeIndex)

        if header.version >= 13:
            if (header.version < 16 and typ.classId < 0) or (
                    header.version >= 16 and typ.classId == 114
            ):
                writer.writeBytes(typ.scriptId)  # Hash128
            writer.writeBytes(typ.oldTypeHash)  # Hash128

        if self._enableTypeTree:
            if header.version >= 12 or header.version == 10:
                self.saveTypeTree5(typ.nodes, writer, typ.stringData)
            else:
                self.saveTypeTree(typ.nodes, writer)

    def saveTypeTree(self, nodes: list, writer: EndianBinaryWriter):
        for i, node in nodes:
            writer.writeStringToNull(node.type)
            writer.writeStringToNull(node.name)
            writer.writeInt(node.byteSize)
            if self.serializedHeader.version == 2:
                writer.writeInt(node.variableCount)

            if self.serializedHeader.version != 3:
                writer.writeInt(node.index)

            writer.writeInt(node.isArray)
            writer.writeInt(node.version)
            if self.serializedHeader.version != 3:
                writer.writeInt(node.metaFlag)

            # 计算 子资源数
            childrenCount = 0
            for node2 in nodes[i + 1:]:
                if node2.level == node.level:
                    break
                if node2.level == node.level - 1:
                    childrenCount += 1
            writer.writeInt(childrenCount)

    def saveTypeTree5(self, nodes: list, writer: EndianBinaryWriter, strData=b""):
        # 节点数
        # 流缓冲区大小
        # 节点数据
        # 字符串缓冲区

        stringBuffer = EndianBinaryWriter()

        stringBuffer.write(strData)
        stringsValues = [
            (node.typeStrOffset, node.nameStrOffset) for node in nodes
        ]

        # 节点数
        writer.writeInt(len(nodes))
        # 字符串缓冲区大小
        writer.writeInt(stringBuffer.Length)

        # nodes
        for i, node in enumerate(nodes):
            # version
            writer.writeUShort(node.version)
            # level
            writer.writeByte(node.level)
            # is array
            writer.writeBoolean(node.isArray)

            writer.writeUInt(stringsValues[i][0])
            writer.writeUInt(stringsValues[i][1])

            writer.writeInt(node.byteSize)
            writer.writeInt(node.index)
            writer.writeInt(node.metaFlag)

            if self.serializedHeader.version > 17:
                writer.write(node.extra)

        # 字符串缓冲区大小
        writer.write(stringBuffer.bytes)

        if self.serializedHeader.version >= 21:
            writer.writeBytes(b"\x00" * 4)
