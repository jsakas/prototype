from setuptools import setup

setup(
	name='prototype',
 	version='1.0.0',
	description='A static site generator.',
	url='http://github.com/jsakas/prototype',
	author='Jon Sakas',
	author_email='jon.sakas@gmail.com',
	license='MIT',
	packages=['prototype'],
	zip_safe=False,
	install_requires=[
		'babel',
		'jinja2',
		'pylibsass',
		'tornado',
	],
	scripts=[
		'bin/prototype',
	],
	include_package_data=True,
    package_data={
        'prototype': [
        	'template/*.*',
        	'template/*/*.*',
        	'template/*/*/*.*',
        	'template/*/*/*/*.*',
        ]
    },
)
