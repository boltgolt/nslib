from setuptools import setup

requirements_file = [line.strip()
                     for line in open('requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]
requirements = requirements_file

setup(
    name = 'nslib',
    packages = ['nslib'], # this must be the same as the name above
    version = '0.0.2',
    description = 'Full-featured library for the dutch railways (NS).',
    author = 'boltgolt',
    author_email = 'boltgolt@gmail.com',
    url = 'https://github.com/Boltgolt/nslib', # use the URL to the github repo
    download_url = 'https://github.com/Boltgolt/nslib/archive/0.0.1.tar.gz', # I'll explain this in a second
    keywords = ['transport', 'api'], # arbitrary keywords
    install_requires=requirements,
    classifiers = []
)
