import struct
import lzma


def decompress(data: bytes) -> bytes:
    props, dictSize = struct.unpack("<BI", data[:5])
    lc = props % 9
    props = props // 9
    pb = props // 5
    lp = props % 5
    dec = lzma.LZMADecompressor(
        format=lzma.FORMAT_RAW,
        filters=[
            {
                "id": lzma.FILTER_LZMA1,
                "dict_size": dictSize,
                "lc": lc,
                "lp": lp,
                "pb": pb,
            }
        ],
    )
    return dec.decompress(data[5:])


def compress(data: bytes) -> bytes:
    ec = lzma.LZMACompressor(
        format=lzma.FORMAT_RAW,
        filters=[
            {"id": lzma.FILTER_LZMA1, "dict_size": 524288, "lc": 3, "lp": 0, "pb": 2, }
        ],
    )
    ec.compress(data)
    return b"]\x00\x00\x08\x00" + ec.flush()
