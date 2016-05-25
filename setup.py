from setuptools import find_packages
from setuptools import setup


setup(
    name='backend-server',
    version='0.0.1',
    include_package_data=True,
    author='team-tree',
    description='Backend for filesharing server.',
    packages=find_packages(),
    install_requires=[
        'tornado',
        'syringe',
        'bcrypt',
        'pymongo',
    ],
    zip_safe=True)
