import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "postgresql_sequence_utils",
    version = '0.1',#remember to manually set this correctly
    description = 'A django app with a management command that fixes sequences in Postgresql',
    packages = find_packages(),
    author = 'Evgeny.Fadeev',
    author_email = 'evgeny.fadeev@gmail.com',
    license = 'MIT',
    keywords = 'postgresql, django, utility',
    include_package_data = True,
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
)
