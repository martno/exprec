import setuptools

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'Flask>=0.12.2',
    'attrs>=17.4.0',
    'plotly>=2.5.1',
    'yattag>=1.10.0',
    'humanize>=0.5.1',
]

setuptools.setup(
    name="exprec",
    version="0.1.0",
    url="https://github.com/martno/exprec",

    author="Martin Nordstrom",
    author_email="martin.nordstrom87@gmail.com",

    description="Exprec records your execution runs so you can compare different experiments and more easily reproduce results.",
    long_description=readme,

    packages=setuptools.find_packages(include=['exprec']),
    package_dir={'exprec': 'exprec'},
    package_data={
        'exprec': [
            'index.html',
            'js/*',
            'css/*',
        ],
    },

    install_requires=requirements,
    license="MIT license",

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    scripts=[
        'bin/exprec',
    ],
)
