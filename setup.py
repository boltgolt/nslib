from setuptools import setup

requirements_file = [line.strip()
                     for line in open('requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]
requirements = requirements_file

version = '0.0.2'

setup(
    name = 'nslib',
    packages = ['nslib'],
    version = version,
    description = 'Full-featured library for the dutch railways (NS).',
    author = 'boltgolt',
    author_email = 'boltgolt@gmail.com',
    license='MIT',
    url = 'https://github.com/Boltgolt/nslib',
    download_url = 'https://github.com/Boltgolt/nslib/archive/{}.tar.gz'.format(version),
    keywords = ['transport', 'api'],
    install_requires = requirements,
    classifiers = []
)
