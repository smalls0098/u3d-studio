class BuildType:
    buildType: str

    def __init__(self, buildType):
        self.buildType = buildType

    @property
    def isAlpha(self):
        return self.buildType == "a"

    @property
    def isPath(self):
        return self.buildType == "p"
