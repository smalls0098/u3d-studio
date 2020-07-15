from u3dunpack.streams import EndianBinaryReader


def makeNewImageData(Texture2D, ktxData):
    if not ktxData[0:12] == b"\xAB\x4B\x54\x58\x20\x31\x31\xBB\x0D\x0A\x1A\x0A":
        print("ktx header data not the same")

    if str(ktxData[68:82]).lower() == "b'ktxorientation'":
        data = ktxData[96:]
        dataReader = EndianBinaryReader(data, '<')
        i = 1
        byte = b""
        while i <= Texture2D.m_MipCount:
            size = dataReader.readInt()
            byte += dataReader.readBytes(size)
            i += 1
        dataReader.dispose()
        data = byte
    else:
        data = ktxData[68:]

    if len(data) != len(Texture2D.imageData):
        print("ktx body data not the same")
        return
    Texture2D.imageData = data
