from setuptools import setup

setup(
    name='launchpad_rpm',
    version='0.1.1',
    packages=['ui', 'treeview', 'package_process'],
    package_dir={'': 'src'},
    url='',
    license='GPLv3',
    author='James Miller',
    author_email='jamesstewartmiller@gmail.com',
    description='QT Gui application to download, convert, and install packages from launchpad.net',
    install_requires=['httplib2', 'requests', 'PyQt5', 'launchpadlib', 'fuzzywuzzy', 'configobj', 'dogpile', 'distro']
)
