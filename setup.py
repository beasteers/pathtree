import setuptools

setuptools.setup(name='path-tree',
                 version='0.0.13',
                 description='Define named directory structure using placeholders',
                 long_description=open('README.md').read().strip(),
                 long_description_content_type='text/markdown',
                 author='Bea Steers',
                 author_email='bea.steers@gmail.com',
                 url='https://github.com/beasteers/pathtree',
                 packages=setuptools.find_packages(),
                 # py_modules=['packagename'],
                 # package_data={'<PACKAGE>': {'*.yaml'}},
                 # include_package_data=True,
                 install_requires=['parse', 'pformat'],
                 license='MIT License',
                 zip_safe=False,
                 keywords='path directory tree structure partial format')
