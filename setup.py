from setuptools import setup

requirements_file = [line.strip()
                     for line in open('requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]
requirements = requirements_file

setup(
    name = 'nslib',
    packages = ['nslib'],
    version = '0.0.2',
    description = 'Full-featured library for the dutch railways (NS).',
    author = 'boltgolt',
    author_email = 'boltgolt@gmail.com',
    license='MIT',
    url = 'https://github.com/Boltgolt/nslib',
    download_url = 'https://github.com/Boltgolt/nslib/archive/0.0.2.tar.gz',
    keywords = ['transport', 'api'],
    install_requires=requirements,
    classifiers = []
)
