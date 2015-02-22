from setuptools import setup

setup(
    name='systest',
    version='0.1',
    author='Dan Kilman',
    author_email='dankilman@gmail.com',
    packages=['systest_manager'],
    description='Manages cloudify system tests configurations',
    zip_safe=False,
    install_requires=[
        'requests',
        'argh',
        'sh',
        'path.py',
    ],
    entry_points={
        'console_scripts': [
            'systest = systest_manager.systest:main',
        ],
    }
)
