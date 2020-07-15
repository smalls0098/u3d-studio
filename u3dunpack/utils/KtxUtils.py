import struct


def header(width, height, size, typ=1, mipmapCount=1):
    # ktx head start
    # ktx head end
    identifier = b"\xAB\x4B\x54\x58\x20\x31\x31\xBB\x0D\x0A\x1A\x0A"
    endianness = b"\x01\x02\x03\x04"
    glType = b"\x00\x00\x00\x00"
    glTypeSize = b"\x01\x00\x00\x00"
    glFormat = b"\x01\x00\x00\x00"
    glInternalFormat = b"\x64\x8D\x00\x00"
    glBaseInternalFormat = b"\x07\x19\x00\x00"
    pixelWidth = struct.pack("<i", width)
    pixelHeight = struct.pack("<i", height)

    pixelDepth = b"\x00\x00\x00\x00"
    numberOfArrayElements = b"\x00\x00\x00\x00"
    numberOfFaces = b"\x00\x00\x00\x00"
    numberOfMipmapLevels = struct.pack("<i", mipmapCount)
    bytesOfKeyValueData = b"\x00\x00\x00\x00"

    KTXOrientation = b""

    bytesOfTextureDataSize = struct.pack("<i", size)

    if typ == 2:
        glFormat = b"\x00\x00\x00\x00"
        numberOfFaces = b"\x01\x00\x00\x00"
        bytesOfKeyValueData = b"\x20\x00\x00\x00"
        KTXOrientation = b"\x1B\x00\x00\x00\x4B\x54\x58\x4F\x72\x69\x65\x6E\x74\x61\x74\x69\x6F\x6E\x00\x53\x3D\x72\x2C\x54\x3D\x75\x2C\x52\x3D\x69\x00\x00"

    return identifier + endianness + glType + glTypeSize + glFormat + glInternalFormat + glBaseInternalFormat + pixelWidth + pixelHeight + pixelDepth + numberOfArrayElements + numberOfFaces + numberOfMipmapLevels + bytesOfKeyValueData + KTXOrientation + bytesOfTextureDataSize
