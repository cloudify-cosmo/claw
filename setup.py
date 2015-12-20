from setuptools import setup

setup(
    name='systest',
    version='0.1',
    author='Dan Kilman',
    author_email='dankilman@gmail.com',
    packages=['systest',
              'systest.handlers',
              'systest.resources'],
    description='Manages Cloudify manager environments by leveraging the'
                'system tests framework',
    zip_safe=False,
    install_requires=[
        'cloudify-system-tests',
        'argh',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'systest = systest.main:main',
        ],
    }
)
