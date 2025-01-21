from setuptools import setup, find_packages

setup(
    name="clisa",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        'console_scripts': [
            'clisa=clisa.ai:main',
        ],
    },
    python_requires='>=3.6',
    author="therealjuanmartinez",
    description="A CLI AI assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
