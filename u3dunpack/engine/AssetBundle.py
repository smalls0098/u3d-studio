from .NamedObject import NamedObject
from .PPtr import PPtr


class AssetInfo:
    def __init__(self, reader):
        self.preloadIndex = reader.readInt()
        self.preloadSize = reader.readInt()
        self.asset = PPtr(reader)


class AssetBundle(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        preloadTableSize = reader.readInt()
        self.preloadTable = [PPtr(reader) for _ in range(preloadTableSize)]
        containerSize = reader.readInt()
        self.container = {}
        for i in range(containerSize):
            key = reader.readAlignedString()
            self.container[key] = AssetInfo(reader)
