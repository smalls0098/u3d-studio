from ..streams import EndianBinaryReader, EndianBinaryWriter


class GLTextureSettings:

    def __init__(self, reader: EndianBinaryReader, version):
        version = version

        self.m_FilterMode = reader.readInt()
        self.m_Aniso = reader.readInt()
        self.m_MipBias = reader.readFloat()
        if version[0] >= 2017:  # 2017.x and up
            self.m_WrapMode = reader.readInt()  # m_WrapU
            self.m_WrapV = reader.readInt()
            self.m_WrapW = reader.readInt()
        else:
            self.m_WrapMode = reader.readInt()

    def save(self, writer: EndianBinaryWriter, version):
        writer.writeInt(self.m_FilterMode)
        writer.writeInt(self.m_Aniso)
        writer.writeFloat(self.m_MipBias)
        if version[0] >= 2017:  # 2017.x and up
            writer.writeInt(self.m_WrapMode)  # m_WrapU
            writer.writeInt(self.m_WrapV)
            writer.writeInt(self.m_WrapW)
        else:
            writer.writeInt(self.m_WrapMode)
