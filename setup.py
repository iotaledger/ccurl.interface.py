from setuptools import setup, find_packages

setup(
    name='pow',
    version='1.0',
    packages=['pow'],
    package_dir={'pow': 'pow'},
    package_data={'pow': ['libccurl.so']},
    )