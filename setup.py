from setuptools import setup

setup(
    name='systest',
    version='0.1',
    author='Dan Kilman',
    author_email='dankilman@gmail.com',
    packages=['systest_manager'],
    description='Manages cloudify system tests configurations',
    zip_safe=False,
    package_data={
        'systest_manager': ['resources/tmuxp.template.yaml'],
    },
    install_requires=[
        'requests',
        'argh',
        'sh',
        'path.py',
        'tmuxp',
        'Jinja2',
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'systest = systest_manager.systest:main',
        ],
    }
)
