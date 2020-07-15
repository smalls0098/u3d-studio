class ResourcesFile(object):
    name: str
    files: dict
    # 签名头，也就是文件头信息
    signature: str
    compression: str

    def keys(self):
        return self.files.keys()

    def items(self):
        return self.files.items()

    def values(self):
        return self.files.values()

    def __getitem__(self, item):
        return self.files[item]

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
