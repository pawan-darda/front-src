from setuptools import setup, find_packages


setup(
     name='magellan',
     version='2.0',
     author='Laurent Ploix, Shashank Ashtikar, Pawan Darda',
     author_email='laurent.ploix@sungard.com',
     description = 'Magellan',
     install_requires = [ 'sqlalchemy', 'frontservices', 'django'],
     py_modules = ['__init__', 'manage', 'settings', 'urls'],
     include_package_data = True,
     packages = find_packages(),
     zip_safe = False #The egg is installed as an extracted directory.
     )