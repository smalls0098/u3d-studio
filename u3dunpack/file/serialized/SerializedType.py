from ...enums import ClassIDType


class SerializedType:
    classId: ClassIDType
    isStrippedType: bool
    scriptTypeIndex = -1
    nodes: list = []  # TypeTreeNode
    scriptId: bytes  # Hash128
    oldTypeHash: bytes  # Hash128}
    stringData: bytes
