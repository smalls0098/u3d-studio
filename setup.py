import setuptools

with open("README.md", "r", encoding='UTF-8') as f:
    desc = f.read()
    if desc == '':
        desc = '一个u3d的资源解包打包工具'

setuptools.setup(
    name="u3d-studio",
    description="a python library for u3d unpacking",
    long_description=desc,
    long_description_content_type="text/markdown",
    version="1.0.16",
    author="smalls",
    author_email='smalls0098@gmail.com',
    packages=setuptools.find_packages(),
    keywords=['u3dpack', 'unitypack', 'u3d-assets-tools', "assetspack"],
    url="https://github.com/smalls0098/u3d-assets-tools",
    download_url="https://github.com/smalls0098/u3d-assets-tools/tarball/master",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Multimedia :: Graphics",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=[
        "lz4",
        "Pillow",
        "tex2img",
    ]
)
