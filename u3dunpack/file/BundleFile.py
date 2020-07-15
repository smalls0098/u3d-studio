from ..enums import UnityType, FileType
from .BlockInfo import BlockInfo
from .ResourcesFile import ResourcesFile
from .serialized import SerializedFile
from ..streams import EndianBinaryReader, EndianBinaryWriter
from .. import AssetsManager
from ..utils import UnityUtils, LzmaUtils, Lz4Utils


class BundleFile(ResourcesFile):
    """
    unity3d 格式
    format=6：UnityFS
    5.x.x
    """
    format: int
    """
    unity3d version number 版本号
    5.x.x
    """
    versionPlayer: str
    """
    unity3d engine version 引擎版本
    2017.4.17f1
    """
    versionEngine: str
    """
    用于记录循环的数据信息
    2017.4.17f1
    """
    blockInfos: []

    def __init__(self, reader: EndianBinaryReader, assetsManager: AssetsManager):
        self.files = {}
        self.signature = reader.readStringToNull()
        self.format = reader.readInt()
        self.versionPlayer = reader.readStringToNull()
        self.versionEngine = reader.readStringToNull()
        if self.format == 6:
            self.readFormatFS(reader, self.signature == UnityType.UnityFS.name)
        else:
            raise ValueError('暂时不支持其他格式的资源包')
        self.load(assetsManager)

    def load(self, assetsManager: AssetsManager):
        for name, streams in self.files.items():
            # 检查序列化文件
            if name.endswith((".resS", ".resource", ".config", ".xml", ".dat")):
                assetsManager.resources[name] = streams
            else:
                typeFile, _ = UnityUtils.checkFileType(streams)
                if typeFile == FileType.AssetsFile:
                    streams.position = 0
                    sf = SerializedFile(streams, assetsManager, self)
                    sf.flag = streams.flag
                    self.files[name] = sf
                    assetsManager.assets[name] = sf
                else:
                    assetsManager.resources[name] = streams

    def readFormatFS(self, reader: EndianBinaryReader, isFS: bool):
        # 文件大小
        bundleSize = reader.readLong()
        # 文件头位置压缩大小
        compressedSize = reader.readInt()
        # 文件头位置解压大小
        uncompressedSize = reader.readInt()
        # 检查文件是否压缩过
        flag = reader.readInt()

        if isFS is not True:
            reader.readByte()

        if (flag & 0x80) != 0:
            position = reader.position
            reader.position = reader.length - compressedSize
            blockInfoBytes = reader.readBytes(uncompressedSize)
            reader.position = position
        else:
            blockInfoBytes = reader.readBytes(compressedSize)

        switch = flag & 0x3F

        if switch == 1:
            # LZMA
            headerBlockData = LzmaUtils.compress(blockInfoBytes)
        elif switch in [2, 3]:
            # LZ4, LZ4HC
            headerBlockData = Lz4Utils.decompress(blockInfoBytes, uncompressedSize)
        else:  # 未压缩
            headerBlockData = blockInfoBytes

        headerBlockReader = EndianBinaryReader(headerBlockData)
        headerBlockReader.position = 0x10
        blockCount = headerBlockReader.readInt()
        self.blockInfos = [BlockInfo(headerBlockReader) for _ in range(blockCount)]
        data = []
        for blockInfo in self.blockInfos:
            switch = blockInfo.flag & 0x3F
            if switch == 1:
                # LZMA
                data.append(LzmaUtils.decompress(reader.read(blockInfo.compressedSize)))
            elif switch in [2, 3]:
                # LZ4, LZ4HC
                data.append(Lz4Utils.decompress(reader.read(blockInfo.compressedSize), blockInfo.uncompressedSize))
            else:  # 未压缩
                data.append(reader.read(blockInfo.compressedSize))

        reductionStream = EndianBinaryReader(b"".join(data))
        entryInfoCount = headerBlockReader.readInt()
        for _ in range(entryInfoCount):
            offset = headerBlockReader.readLong()
            size = headerBlockReader.readLong()
            flag = headerBlockReader.readInt()
            name = headerBlockReader.readStringToNull()
            reductionStream.position = offset
            item = EndianBinaryReader(reductionStream.read(size))
            item.flag = flag
            self.files[name] = item

    def save(self, isCompress: bool = True) -> bytes:
        writer = EndianBinaryWriter()

        writer.writeStringToNull(self.signature)
        writer.writeInt(self.format)
        writer.writeStringToNull(self.versionPlayer)
        writer.writeStringToNull(self.versionEngine)
        if self.format == 6:  # WORKS
            self.saveFormat6(writer, self.signature != "UnityFS", isCompress)
        else:  # WIP
            raise NotImplementedError("Not Implemented")

        return writer.bytes

    def saveFormat6(self, writer: EndianBinaryWriter, padding=False, isCompress=True):
        if isCompress:
            # 40 - uncompressed
            # 43 - lz4
            blockInfoFlag = 0x43
            # 0/64 - uncompressed
            # 1 - lzma
            # 2 - lz4
            # 3 - lz4hc - not implemented
            # 4 - lzham - not implemented
            dataFlag = 0x43
        else:
            blockInfoFlag = 0x40
            dataFlag = 0x40

        # file list & file data
        dataWriter = EndianBinaryWriter()
        files = [
            (
                name,
                f.flag,
                dataWriter.writeBytes(
                    f.bytes if isinstance(f, EndianBinaryReader) else f.save()
                ),
            )
            for name, f in self.files.items()
        ]
        #  压缩的数据
        compressData = EndianBinaryReader(dataWriter.bytes)
        # 每个模块的数据
        data = []
        # 生成头模块的数据格式
        headerBlockData = b""
        # compress block the data
        for blockInfo in self.blockInfos:
            switch = dataFlag & 0x3F
            if switch in [1, 2, 3]:
                # LZ4, LZ4HC
                compressBlockByte = compressData.read(blockInfo.uncompressedSize)
                result = Lz4Utils.compress(compressBlockByte)
                blockInfo.compressedSize = len(result)
                blockInfo.uncompressedSize = len(compressBlockByte)
                blockInfo.flag = 3
                data.append(result)
            else:  # 未压缩
                data.append(compressData.read(blockInfo.uncompressedSize))
                blockInfo.compressedSize = blockInfo.uncompressedSize
                blockInfo.flag = 0
            headerBlockData += blockInfo.blockByte()
        compressStream = EndianBinaryReader(b"".join(data))

        fileData = compressStream.bytes

        dataWriter.dispose()
        compressData.dispose()

        compressedDataSize = len(fileData)

        # write the block_info
        blockWriter = EndianBinaryWriter(b"\x00" * 0x10)
        # data block info
        # # flag
        # blockWriter.writeShort(dataFlag)
        # file block count
        # file block info
        # file count
        blockWriter.writeInt(len(self.blockInfos))
        blockWriter.write(headerBlockData)
        blockWriter.writeInt(len(files))

        offset = 0
        for fileName, fileFlag, fileLen in files:
            # offset
            blockWriter.writeLong(offset)
            # size
            blockWriter.writeLong(fileLen)
            offset += fileLen
            # flag
            blockWriter.writeInt(fileFlag)
            # name
            blockWriter.writeStringToNull(fileName)

        # compress the block data
        blockData = blockWriter.bytes
        blockWriter.dispose()

        uncompressedBlockDataSize = len(blockData)

        switch = blockInfoFlag & 0x3F
        if switch == 1:  # LZMA
            blockData = LzmaUtils.compress(blockData)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            blockData = Lz4Utils.compress(blockData)
        elif switch == 4:  # LZHAM
            raise NotImplementedError
        compressedBlockDataSize = len(blockData)

        # 写头信息
        writer.writeLong(
            writer.Length
            + 8
            + 4
            + 4
            + 4
            + (1 if padding else 0)
            + compressedBlockDataSize
            + compressedDataSize
        )
        writer.writeInt(compressedBlockDataSize)
        writer.writeInt(uncompressedBlockDataSize)
        writer.writeInt(blockInfoFlag)
        if padding:
            writer.writeBoolean(padding)
        if (blockInfoFlag & 0x80) != 0:  # at end of file
            writer.write(fileData)
            writer.write(blockData)
        else:
            writer.write(blockData)
            writer.write(fileData)
