from setuptools import setup, find_packages

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
    # packages=find_packages(),
    data_files=[('share/doc/whatsthedamage', ['config.json.default'])],
    python_requires='>=3.9',
    url='https://github.com/abalage/whatsthedamage',
    version='0.1.0',
)