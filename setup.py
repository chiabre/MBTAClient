from setuptools import setup, find_packages

setup(
    name="MBTAclient",  # Replace with your package's name
    version="0.1.0",  # Initial release version
    author="Luca Chiabrera",  # Replace with your name
    author_email="luca.chiabrera@gmail.com",  # Replace with your email
    description="A Python client for interacting with the MBTA API",  # Short description of your package
    long_description=open("README.md").read(),  # Long description read from the README file
    long_description_content_type="text/markdown",  # Content type of long description
    url="https://github.com/chiabre/MBTAclient",  # URL to the repository or project homepage
    packages=find_packages(),  # Automatically find and include all packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # License type
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Minimum Python version requirement
    include_package_data=True,  # Include files listed in MANIFEST.in
)