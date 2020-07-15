import os


def getResourceData(*args):
    """
    Input:
    Option 1:
        path - file path
        assets_file - SerializedFile
        offset -
        size -
    Option 2:
        reader - EndianBinaryReader
        offset -
        size -
    """
    if len(args) == 4:
        needSearch = True
        path = args[0]
        assetsFile = args[1]
    elif len(args) == 3:
        needSearch = False
        reader = args[0]
        path = ''
        assetsFile = ''
    else:
        raise ValueError("ResourceReader")
    offset = args[-2]
    size = args[-1]

    if needSearch:
        resourceFileName = path

        reader = assetsFile.environment.resources.get(resourceFileName)
        if not reader:
            reader = assetsFile.environment.resources.get(
                os.path.basename(resourceFileName)
            )
        if reader:
            reader.Position = offset
            return reader.read_bytes(size)

        if not assetsFile.environment.path:
            return
        current_directory = os.path.dirname(assetsFile.environment.path)
        resourceFilePath = os.path.join(current_directory, resourceFileName)
        if not os.path.isfile(resourceFilePath):
            findFiles = findAllFiles(current_directory, resourceFileName)
            if findFiles:
                resourceFilePath = findFiles[0]

        if os.path.isfile(resourceFilePath):
            with open(resourceFilePath, "rb") as f:
                f.seek(offset)
                return f.read(size)
        else:
            raise FileNotFoundError(
                f"Can't find the resource file {resourceFileName}"
            )

    else:
        reader.position = offset
        return reader.readBytes(size)


def findAllFiles(directory: str, searchStr: str) -> list:
    return [
        val
        for sublist in [
            [
                os.path.join(dirPath, filename)
                for filename in filenames
                if searchStr in filename
            ]
            for (dirPath, dirNames, filenames) in os.walk(directory)
            if ".git" not in dirPath
        ]
        for val in sublist
    ]
