import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="monzo-expenses",
    version="1.0.1",
    author="Sam Dobson",
    author_email="sjd333@gmail.com",
    description="Generate expense reports from Monzo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/samdobson/monzo-expenses",
    install_requires=[
      'weasyprint',
      'jinja2'
    ],
    include_package_data=True,
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': ['monzo-expenses=expenses.command_line:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
