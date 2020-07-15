from ..utils import KtxUtils


def makeKtx(texture2d):
    return KtxUtils.header(texture2d.m_Width, texture2d.m_Height, texture2d.m_CompleteImageSize) + texture2d.imageData
