import os
import re

from ..enums import FileType
from ..streams import EndianBinaryReader


def checkFileType(data) -> (FileType, EndianBinaryReader):
    if isinstance(data, str) and os.path.isfile(data):
        with open(data, 'rb') as f:
            reader = EndianBinaryReader(f.read())
    elif isinstance(data, EndianBinaryReader):
        reader = data
    else:
        reader = EndianBinaryReader(data)

    signature = reader.readStringToNull(10)
    reader.position = 0

    if signature in ['UnityFS']:
        return FileType.BundleFile, reader
    else:
        # 检查AssetsFile
        oldEndian = reader.endian
        assetsFile = True
        # 就像资产文件一样阅读并检查版本
        reader.position = 0
        metadataSize = reader.readUInt()
        fileSize = reader.readUInt()
        version = reader.readUInt()
        dataOffset = reader.readUInt()

        if (version < 0 or version > 100 or any([
            x < 0 or x > reader.length
            for x in [metadataSize, version, dataOffset]
        ])):
            return FileType.ResourceFile, reader

        if version >= 9:
            endian = ">" if reader.readBoolean() else "<"
            reserved = reader.readBytes(3)
        else:
            reader.position = fileSize - metadataSize
            endian = ">" if reader.readBoolean() else "<"

        reader.endian = endian

        if version >= 7:
            unityVersion = reader.readStringToNull()
            if len([x for x in re.split(r"\D", unityVersion) if x != ""]) != 4:
                assetsFile = False
            # check end
            reader.endian = oldEndian
            reader.position = 0
            if assetsFile:
                return FileType.AssetsFile, reader
            else:
                return FileType.ResourceFile, reader