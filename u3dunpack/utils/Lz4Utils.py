# LZ4M/LZ4HC
import lz4 as lz4
from lz4.block._block import LZ4BlockError


def decompress(data: bytes, uncompressedSize: int) -> bytes:
    try:
        return lz4.block.decompress(data, uncompressedSize)
    except LZ4BlockError:
        print("uncompress failed")


# LZ4M/LZ4HC
def compress(data: bytes) -> bytes:
    try:
        byte = lz4.block.compress(data, mode="high_compression", compression=9)
        return byte[4:]
    except LZ4BlockError:
        print("compress failed")
