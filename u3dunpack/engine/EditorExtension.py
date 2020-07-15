from .Object import Object
from .PPtr import PPtr
from ..engine.PPtr import savePtr

from ..enums import BuildTarget
from ..streams import EndianBinaryReader, EndianBinaryWriter


class EditorExtension(Object):
    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        if self.platform == BuildTarget.NoTarget:
            self.prefabParentObject = PPtr(reader)
            self.prefabInternal = PPtr(reader)

    def save(self, writer: EndianBinaryWriter, **kwargs):
        super().save(writer, internCall=True)
        if self.platform == BuildTarget.NoTarget:
            savePtr(self.prefabParentObject)
            savePtr(self.prefabInternal)
