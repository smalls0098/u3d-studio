from ..streams import EndianBinaryReader


class RefInt:
    v: int

    def __init__(self, value):
        self._value = value

    def __add__(self, other):
        return self._value + other

    def __sub__(self, other):
        self._value -= other
        return self._value

    def __int__(self):
        return self._value

    def __getattr__(self, item):
        return self._value

    def __getitem__(self, item):
        return self._value

    def __setattr__(self, key, value):
        self.__dict__["_value"] = value

    def __setitem__(self, key, value):
        self._value = value

    def __mod__(self, other):
        return self._value % other

    def __ge__(self, other):
        return self._value >= other

    def __gt__(self, other):
        return self._value > other

    def __le__(self, other):
        return self._value <= other

    def __lt__(self, other):
        return self._value < other

    def __eq__(self, other):
        return self._value == other


def getMembers(members: list, level: int, index: int) -> list:
    member2 = [members[0]]
    for i in range(index + 1, len(members)):
        member = members[i]
        if member.level <= level:
            return member2
        member2.append(member)
    return member2


class TypeTreeUtils:
    def __init__(self, reader: EndianBinaryReader):
        self.reader = reader
        self.READ = {
            "SInt8": self.reader.readByte,
            "UInt8": self.reader.readUByte,
            "short": self.reader.readShort,
            "SInt16": self.reader.readShort,
            "unsigned short": self.reader.readUShort,
            "UInt16": self.reader.readUShort,
            "int": self.reader.readInt,
            "SInt32": self.reader.readInt,
            "unsigned int": self.reader.readUInt,
            "UInt32": self.reader.readUInt,
            "Type*": self.reader.readUInt,
            "long long": self.reader.readLong,
            "SInt64": self.reader.readLong,
            "unsigned long long": self.reader.readULong,
            "UInt64": self.reader.readULong,
            "float": self.reader.readFloat,
            "double": self.reader.readDouble,
            "bool": self.reader.readBoolean,
        }

        self.READ2 = {
            "string": self.readString,
            "map": self.readMap,
            "TypelessData": self.readTypelessData,
        }

    def readUType(self, members: list) -> dict:
        i = RefInt(0)
        obj = {}
        while i.v < len(members):
            member = members[i.v]
            obj[member.name] = self.readValue(members, i)
            i.v += 1
        return obj

    def readString(self, i, align, *args):
        value = self.reader.readAlignedString()
        i.v += 3
        return value, align

    def readMap(self, i, align, members, level):
        if (members[i + 1].meta_flag & 0x4000) != 0:
            align = True
        size = self.reader.readInt()
        map_ = getMembers(members, level, i)[4:]
        i.v += len(map_) + 3
        first = getMembers(map_, map_[0].level, 0)
        second = map_[len(first):]
        value = {}
        for j in range(size):
            tmp1 = RefInt(0)
            tmp2 = RefInt(0)
            v1 = self.readValue(
                first, tmp1
            )  # python reads the value first and then the key, so it has to be this way
            if isinstance(v1, dict):
                value[first] = tmp1
                value["values"] = self.readValue(second, tmp2)
            else:
                value[v1] = self.readValue(second, tmp2)
        return value, align

    def readTypelessData(self, i, align, *args):
        size = self.reader.readInt()
        value = self.reader.readBytes(size)
        i.v += 2
        return value, align

    def readValue(self, members: list, i) -> object:
        if type(i) != RefInt:
            i = RefInt(i)
        member = members[i.v]
        level = member.level
        var_type_str = member.type
        align = (member.meta_flag & 0x4000) != 0

        value = self.READ.get(var_type_str)
        if value:
            value = value()
        else:
            value = self.READ2.get(var_type_str)
            if value:
                value, align = value(i, align, members, level)
            else:
                if i != len(members) and members[i.v + 1].type == "Array":
                    if (members[i.v + 1].meta_flag & 0x4000) != 0:
                        align = True
                    size = self.reader.readInt()
                    vector = getMembers(members, level, i)[3:]
                    i.v += len(vector) + 2
                    value = [self.readValue(vector, 0) for j in range(size)]
                else:
                    eclass = getMembers(members, level, i)
                    eclass.pop(0)
                    i.v += len(eclass)
                    j = RefInt(0)
                    value = {}
                    while j < len(eclass):
                        classmember = eclass[j.v]
                        name = classmember.name
                        value[name] = self.readValue(eclass, j)
                        j.v += 1
        if align:
            self.reader.alignStream()
        return value

    def readTypeString(self, sb: list, members: list):
        i = RefInt(0)
        while i < len(members):
            self.readStringValue(sb, members, i)
            i.v += 1
        return sb

    def readStringValue(self, sb: list, members, i: RefInt):
        if type(i) != RefInt:
            i = RefInt(i)
        member = members[i.v]
        level = member.level
        var_type_str = member.type
        var_name_str = member.name
        append = True
        align = (member.meta_flag & 0x4000) != 0
        value = self.READ.get(var_type_str)
        if value:
            value = value()

        elif var_type_str == "string":
            append = False
            string = self.reader.readAlignedString()
            sb.append(
                '{0}{1} {2} = "{3}"\r\n'.format(
                    "\t" * level, var_type_str, var_name_str, string
                )
            )
            i.v += 3

        elif var_type_str == "vector":
            if (members[i + 1].meta_flag & 0x4000) != 0:
                align = True
            append = False
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
            size = self.reader.readInt()
            sb.append(
                "{0}{1} {2} = {3}\r\n".format("\t" * (level + 1), "int", "size", size)
            )
            vector = getMembers(members, level, i.v)[3:]
            i.v += len(vector) + 2
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                tmp = RefInt(0)
                self.readStringValue(sb, vector, tmp)

        elif var_type_str == "map":
            if (members[i + 1].meta_flag & 0x4000) != 0:
                align = True
            append = False
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
            size = self.reader.readInt()
            sb.append(
                "{0}{1} {2} = {3}\r\n".format("\t" * (level + 1), "int", "size", size)
            )
            map_ = getMembers(members, level, i.v)[4:]
            i.v += len(map_) + 3
            first = getMembers(map_, map_[0].level, 0)
            second = map_[len(first):]
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                sb.append("{0}{1} {2}\r\n".format("\t" * (level + 2), "pair", "data"))
                tmp1 = RefInt(0)
                tmp2 = RefInt(0)
                self.readStringValue(sb, first, tmp1)
                self.readStringValue(sb, second, tmp2)

        elif var_type_str == "TypelessData":
            append = False
            size = self.reader.readInt()
            value = self.reader.readBytes(size)
            i.v += 2
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2} = {3}\r\n".format("\t" * level, "int", "size", size))

        else:
            if i != len(members) and members[i + 1].type == "Array":
                if (members[i + 1].meta_flag & 0x4000) != 0:
                    align = True
                append = False
                sb.append(
                    "{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str)
                )
                sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
                size = self.reader.readInt()
                sb.append(
                    "{0}{1} {2} = {3}\r\n".format(
                        "\t" * (level + 1), "int", "size", size
                    )
                )
                vector = getMembers(members, level, i.v)
                i.v += len(vector) - 1
                vector = vector[3:]  # vector.RemoveRange(0, 3)
                for j in range(size):
                    sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                    tmp = RefInt(0)
                    self.readStringValue(sb, vector, tmp)
            else:
                append = False
                sb.append(
                    "{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str)
                )
                eclass = getMembers(members, level, i.v)
                eclass.pop(0)  # .RemoveAt(0)
                i.v += len(eclass)
                j = RefInt(0)
                while j < len(eclass):
                    self.readStringValue(sb, eclass, j)
                    j.v += 1

        if append:
            sb.append(
                "{0}{1} {2} = {3}\r\n".format(
                    "\t" * level, var_type_str, var_name_str, value
                )
            )
        if align:
            self.reader.alignStream()

        return sb
