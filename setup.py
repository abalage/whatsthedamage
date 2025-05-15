from setuptools import setup

setup(
    author='Balázs NÉMETH',
    author_email='balagetech@protonmail.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GPLv3',
        'Operating System :: OS Independent',
    ],
    description='A package to process KHBHU CSV files',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    name='whatsthedamage',
    data_files=[('share/doc/whatsthedamage', ['config.yml.default'])],
    python_requires='>=3.9',
    url='https://github.com/abalage/whatsthedamage',
)
