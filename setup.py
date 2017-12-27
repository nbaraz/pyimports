from setuptools import setup

setup(
    name='vython',
    packages=['vython'],
    package_dir={'vython': 'vython'},
    # I can see at least 2 ironic things about this, help me find more?
    install_requires=['pytoml'],
    entry_points={
        'console_scripts': [
            'vython=vython.vython:main'
        ]
    },
)
