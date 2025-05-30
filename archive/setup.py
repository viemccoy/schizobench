#!/usr/bin/env python3
"""
Setup.py for backwards compatibility
This file is maintained for pip installs, but Poetry is recommended
"""

from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='schizobench',
    version='2.0.0',
    description='Automated benchmark for evaluating LLM propensity to enable magical thinking',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='SchizoBench Team',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'schizobench=schizobench.cli:main',
            'schizobench-v2=run_benchmark_v2:main',
            'verify-schizobench=verify_setup:verify_setup',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)