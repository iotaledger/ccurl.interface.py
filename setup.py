from setuptools import setup, find_packages

with open('README.rst', 'r') as f: # type: StreamReader
  long_description = f.read()

setup(
  name        = 'PyOTA-PoW',
  description = 'Ccurl PoW Interface for PyOTA',
  url         = 'https://github.com/lzpap/ccurl.interface.py',
  version     = '1.0.0',

  long_description = long_description,
  packages=['pow'],
  package_dir={'pow': 'pow'},
  package_data={'pow': ['libccurl.so']},

  install_requires = ['pyota'],

  tests_require = ['nose'],
  test_suite    = 'test',
  test_loader   = 'nose.loader:TestLoader',

  license = 'MIT',

  classifiers = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
  ],

  keywords =
    'iota,tangle,iot,internet of things,api,library,cryptocurrency,'
    'balanced ternary',

  author        = 'Levente Pap',
  author_email  = 'levente.pap@iota.org',
)