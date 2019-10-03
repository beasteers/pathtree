import setuptools

setuptools.setup(name='path-tree',
                 version='0.0.8',
                 description='Specify a directory structure using placeholders',
                 # long_description=open('README.md').read().strip(),
                 author='Bea Steers',
                 author_email='bea.steers@gmail.com',
                 # url='http://path-to-my-packagename',
                 packages=setuptools.find_packages(),
                 # py_modules=['packagename'],
                 # package_data={'uoimdb': {'*.yaml'}},
                 # include_package_data=True,
                 install_requires=[
                    'parse',
                 ],
                 license='MIT License',
                 zip_safe=False,
                 keywords='path directory structure format')
