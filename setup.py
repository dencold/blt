try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

settings = {
    'name': 'blt',
    'version': '0.2.0',
    'description': 'blt - provides simple CLI superpowers.',
    'long_description': open('README.md').read(),
    'author': 'Dennis Coldwell',
    'author_email': 'dennis.coldwell@gmail.com',
    'url': 'https://github.com/dencold/blt/',
    'packages': [
        'blt',
        'blt.test',
        'blt.tools'
    ],
    'install_requires': [
        'clint==0.3.3',
        'mock==1.0.1',
        'pytest==2.5.1'
    ],
    'license': 'BSD',
    'classifiers': (
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ),
    'entry_points': {
        'console_scripts': [
            'blt = blt.main:main'
        ]
    }
}

setup(**settings)
