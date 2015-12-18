from setuptools import setup

setup(
    name='systest',
    version='0.1',
    author='Dan Kilman',
    author_email='dankilman@gmail.com',
    packages=['systest_manager',
              'systest_manager.handlers',
              'systest_manager.resources'],
    description='Manages cloudify system tests configurations',
    zip_safe=False,
    install_requires=[
        'cloudify-system-tests',
        'argh',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'systest = systest_manager.systest:main',
        ],
    }
)
