# -*- coding: utf-8 -*-
"""
Created on '16/4/4'
@author: 'greatwhole'
"""

import sys
from setuptools import setup, find_packages
__version__ = '1.0.1'


install_requires = [
    'flask',
    'flask-restful',
    'flask-httpauth',
    'elasticsearch==1.5.0',  # amazon 提供的是1.5.2
    'gevent',
    'numpy==1.11.0',
    'pandas==0.18.0',
    'requests',
    'marshmallow',
    'sqlalchemy',
    'ipython',
    'redis',
]

if sys.version_info < (2, 7):
    install_requires += ['argparse==1.2.1']

setup(
    name='dock_hx',
    version=__version__,
    license='Proprietary',
    author='Huang Xiang',
    author_email='greatwhole@greatwhole90.com',
    maintainer='Huang Xiang',
    maintainer_email='greatwhole@greatwhole90.com',
    description='dock by hx',
    long_description=__doc__,
    packages=find_packages('.', exclude=["tests.*", "tests"]),
    packages_dir={'': '.'},
    include_package_data=True,
    packages_data={'': ['*.pig, *.jar']},
    zip_safe=False,
    install_requires=install_requires,
    platforms='any',
    entry_points={
        'console_scripts': []
    },
    classifiers=[]
)
