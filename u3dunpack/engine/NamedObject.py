from .EditorExtension import EditorExtension
from ..streams import EndianBinaryWriter


class NamedObject(EditorExtension):
    # 这里是获取模块名，也就是文件名
    name: str

    def __init__(self, reader):
        super().__init__(reader=reader)
        self.reader.reset()
        self.name = self.reader.readAlignedString()

    def save(self, writer: EndianBinaryWriter, **kwargs):
        super().save(writer, )
        writer.writeAlignedString(self.name)
