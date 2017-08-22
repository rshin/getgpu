from setuptools import setup, find_packages

setup(
    name='getgpu',
    version='0.0.3',
    description='Return the ID of a free GPU.',
    url='https://github.com/rshin/getgpu',
    install_requires=['nvidia-ml-py~=7.352.0'],
    extras_require={'dev': ['flake8 ~= 3.4.1', 'pre-commit ~= 0.16.3']},
    scripts=['getgpu'], )
