from u3dunpack.streams import EndianBinaryWriter


class PPtr:
    def __init__(self, reader):
        self.index = -2
        self.fileId = reader.readInt()
        self.pathId = reader.readInt() if reader.version2 < 14 else reader.readLong()
        self.serializedFile = reader.serializedFile


    def __getattr__(self, key):
        # get manager
        manager = None
        if self.fileId == 0:
            manager = self.assetsFile

        elif self.fileId > 0 and self.fileId - 1 < len(self.assetsFile.externals):
            if self.index == -2:
                externalName = self.assetsFile.externals[self.fileId - 1].name

                files = self.assetsFile.parent.files
                if externalName not in files:
                    externalName = externalName.upper()
                manager = self.assets_file.parent.files[externalName]

        if manager and self.pathId in manager.objects:
            self = manager.objects[self.pathId]
            return getattr(self, key)

        raise NotImplementedError("PPtr")

    def __repr__(self):
        return self.__class__.__name__

    def __bool__(self):
        return False


def savePtr(obj, writer: EndianBinaryWriter):
    if isinstance(obj, PPtr):
        writer.writeInt(obj.fileId)
        writer.writeInt(obj.pathId)
    else:
        writer.writeInt(0)  # it's usually 0......
        writer.writeInt(obj.pathId)
