from setuptools import setup, find_packages

setup(
    name="artemis-vcs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # Add any dependencies here if needed
    entry_points={
        'console_scripts': [
            'artemis=artemis.main:main',  # Link 'artemis' command to the 'main' function in the 'artemis/main.py' module
        ],
    },
    author="IdrisFallout",
    author_email="business@waithakasam.com",
    description="A simple version control system (VCS) like Git",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/IdrisFallout/artemis-vcs",  # Replace with your actual project URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
