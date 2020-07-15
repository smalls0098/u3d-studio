from ..enums import BuildTarget
from ..streams import EndianBinaryWriter
from ..utils import TypeTreeUtils


class Object:
    typeTree: dict

    def __init__(self, reader):
        self.reader = reader
        self.serializedFile = reader.serializedFile
        self.type = reader.type
        self.pathId = reader.pathId
        self.version = reader.version
        self.buildType = reader.buildType
        self.platform = reader.platform
        self.serializedType = reader.serializedType
        self.byteSize = reader.byteSize
        self.assetsManager = reader.serializedFile.assetsManager

        if self.platform == BuildTarget.NoTarget:
            self._objectHideFlags = reader.readUInt()

        self.container = (
            self.serializedFile._container[self.pathId]
            if self.pathId in self.serializedFile._container
            else None
        )

        self.reader.reset()
        if type(self) == Object:
            self.__dict__.update(self.readTypeTree())

    def hasStructMember(self, name: str) -> bool:
        return self.serializedType.m_Nodes and any([x.name == name for x in self.serializedType.m_Nodes])

    def dump(self) -> str:
        self.reader.reset()
        if getattr(self.serializedType, "nodes", None):
            sb = []
            TypeTreeUtils(self.reader).readTypeString(sb, self.serializedType.nodes)
            return "".join(sb)
        return ""

    def readTypeTree(self) -> dict:
        self.reader.reset()
        if self.serializedType.nodes:
            self.typeTree = TypeTreeUtils(self.reader).readValue(self.serializedType.nodes, 0)
        else:
            self.typeTree = {}
        return self.typeTree

    def getRawData(self) -> bytes:
        self.reader.reset()
        return self.reader.readBytes(self.byteSize)

    def save(self, writer: EndianBinaryWriter, internCall=False):
        if internCall:
            if self.platform == BuildTarget.NoTarget:
                writer.writeUInt(self._objectHideFlags)

    def _save(self, writer):
        # 读者实际上是一个ObjectReader
        # 数据值被写回到资产中
        self.reader.data = writer.bytes

    def __getattr__(self, item):
        """
        如果在__dict__中找不到项目，请阅读type_tree并检查它是否在其中。
        """
        self.readTypeTree()
        if item in self.typeTree:
            return self.typeTree[item]

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)
