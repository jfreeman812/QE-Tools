from setuptools import setup

setup(name='tableread',
      version='1.0.3',
      description='Table reader for simple reStructredText tables',
      url='https://github.rackspace.com/QualityEngineering/QE-Tools',
      author='RBA QE',
      author_email='rba-qe@rackspace.com',
      license='MIT',
      packages=['tableread'],
      install_requires=[
          'attrs>=16.0.0'
      ],
      zip_safe=False)
