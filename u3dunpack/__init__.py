from .AssetsManager import AssetsManager


def load(*args):
    return AssetsManager(*args)


manager = AssetsManager
