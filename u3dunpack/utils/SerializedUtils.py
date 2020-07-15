from ..enums.CommonString import COMMON_STRING
from ..streams import EndianBinaryReader


def readString(stringBufferReader: EndianBinaryReader, value: int) -> str:
    is_offset = (value & 0x80000000) == 0
    if is_offset:
        stringBufferReader.Position = value
        return stringBufferReader.readStringToNull()

    offset = value & 0x7FFFFFFF
    if offset in COMMON_STRING:
        return COMMON_STRING[offset]

    return str(offset)
