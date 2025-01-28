from setuptools import setup, find_packages
import sys

# Regular PyPI dependencies
install_requires = [
    'attrs',
    'beautifulsoup4>=4.11.1',
    'colorama>=0.4.4',
    'Pillow==10.4.0',
    'argparse>=1.4.0',
    'platformdirs>=4.3.6',
    'regex>=2022.9.13',
    'readchar>=4.2.0',
    'requests>=2.32.3',
    'stringcase==1.2.0',
    'webvtt-py',
    'PyYAML>=6.0.1',
    'jsonschema>=3.2.0',
    'watchdog==6.0.0',
    'rich',
    'tiktoken',
    'aisuite==0.1.7',
    'openai==1.54.4',
    'httpx==0.27.2'
]

# Add importlib-metadata for Python < 3.8
if sys.version_info < (3, 8):
    install_requires.append('importlib-metadata>=1.0')

# Git dependencies
dependency_links = [
    'git+https://github.com/therealjuanmartinez/rich.git@master#egg=rich-13.9.4'
]

setup(
    name="clisa",
    version="0.1.2",
    packages=find_packages(),
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points={
        'console_scripts': [
            'clisa=clisa.ai:main',
        ],
    },
    python_requires='>=3.6',
    author="Juan",
    description="A CLI AI assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
