import logging
import os
from .enums import FileType
from .file import BundleFile
from .file.serialized import SerializedFile
from .streams import EndianBinaryReader
from .utils import UnityUtils, ImportUtils


class AssetsManager:
    # 资产
    assets: dict
    # 容器
    container: dict
    # 文件
    files: dict
    # 文件
    objects: dict
    # 资源 .resS, .resource, .config, .xml, .dat
    resources: dict
    # 导入文件
    importFiles: dict

    def __init__(self, *args):
        self.assets = {}
        self.container = {}
        self.files = {}
        self.objects = {}
        self.resources = {}
        self.importFiles = {}
        self.load(*args)

    def load(self, *args):
        """
        加载函数
        用于加载文件或者文件夹
        """
        if args is not None:
            for arg in args:
                if isinstance(arg, str):
                    if os.path.isfile(arg):
                        self.loadFile(arg)
                    else:
                        self.loadFile(arg)
                elif isinstance(arg, bytes):
                    self.loadFile(arg)
                else:
                    # 这里要使用log打印日志
                    logging.error(f"AssetsManager -> load -> 传递的参数不知什么类型，无法进行接下来的逻辑")

    def loadFile(self, filePath: str = ''):
        fileType, reader = UnityUtils.checkFileType(filePath)
        if fileType == FileType.BundleFile:
            self.loadBundleFile(filePath, reader)
        elif fileType == FileType.AssetsFile:
            self.loadAssetsFile(filePath, reader)
        else:
            logging.error(f"AssetsManager -> loadFile -> 未知类型")

    def loadFolder(self, path: str):
        """
        将给定路径中的所有文件及其子目录加载到AssetsManager中
        """
        ImportUtils.mergeSplitAssets(path, True)
        files = ImportUtils.listAllFiles(path)
        toReadFile = ImportUtils.processingSplitFiles(files)
        self.load(toReadFile)

    def loadBundleFile(self, filePath: str, reader: EndianBinaryReader):
        """
        加载资源文件
        """
        fileName = os.path.basename(filePath)
        logging.info(f"Loading {fileName}")
        try:
            self.files[filePath] = BundleFile(reader, self)
        except Exception as e:
            string = "\n" + str(e)
            logging.error(string, e)
        finally:
            reader.dispose()

    def loadAssetsFile(self, filePath: str, reader: EndianBinaryReader):
        """
           加载资产文件
        """
        fileName = os.path.basename(filePath)
        if fileName not in self.assets:
            logging.info(f"Loading {fileName}")
            try:
                assetsFile = SerializedFile(reader, self)
                self.assets[assetsFile.name] = assetsFile
                for sharedFile in assetsFile.externals:
                    sharedFilePath = os.path.join(os.path.dirname(fileName), sharedFile.name)
                    sharedFileName = sharedFile.name
                    if sharedFileName not in self.importFiles:
                        if not os.path.exists(sharedFilePath):
                            findFiles = [
                                f
                                for f in ImportUtils.listAllFiles(
                                    os.path.dirname(fileName)
                                )
                                if sharedFileName in f
                            ]
                            if findFiles:
                                sharedFilePath = findFiles[0]
                        if os.path.exists(sharedFilePath):
                            self.importFiles[sharedFileName] = sharedFilePath
                return assetsFile
            except Exception as e:
                reader.dispose()
                logging.error(f"无法加载资产文件 {fileName}", e)
        else:
            reader.dispose()
