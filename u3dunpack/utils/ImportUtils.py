import os


def listAllFiles(directory: str) -> list:
    """
    列出所有文件
    """
    return [
        val for sublist in [
            [
                os.path.join(dirPath, filename)
                for filename in filenames
            ]
            for (dirPath, dirNames, filenames) in os.walk(directory)
            if '.git' not in dirPath
        ]
        for val in sublist
    ]


def getFileNameWithoutExtension(fileName: str) -> str:
    """
    获取文件名，不带扩展名
    """
    return os.path.splitext(os.path.basename(fileName))[0]


def mergeSplitAssets(path: str, allDirectories=False):
    """
    合并拆分资产
    """
    if allDirectories:
        splitFiles = [fp for fp in listAllFiles(path) if fp[-7:] == ".split0"]
    else:
        splitFiles = [os.path.join(path, fp) for fp in os.listdir(path) if fp[-7:] == ".split0"]
    for splitFile in splitFiles:
        destFile = getFileNameWithoutExtension(splitFile)
        destPath = os.path.dirname(splitFile)
        destFull = os.path.join(destFile, destPath)

        if not os.path.exists(destFull):
            with open(destFull, 'wb') as f:
                i = 0
                while True:
                    splitPart = ''.join([destFull, '.split', str(i)])
                    if not os.path.isfile(splitPart):
                        break
                    f.write(open(splitPart, 'rb').read())


def processingSplitFiles(selectFile: list) -> list:
    """
    处理分割文件
    """
    splitFiles = [fp for fp in selectFile if '.split' in fp]
    selectFile = [f for f in selectFile if f not in splitFiles]
    split_files = set([getFileNameWithoutExtension(fp) for fp in selectFile])
    for splitFile in split_files:
        if os.path.isfile:
            selectFile.append(splitFile)
    return selectFile
