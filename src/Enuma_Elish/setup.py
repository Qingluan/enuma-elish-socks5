

from setuptools import setup, find_packages


setup(name='Enuma_Elish',
    version='2.2',
    description='a ord vpn based on socks5 , then change some from ss',
    url='https://github.com/Qingluan/Enuma_Elish.git',
    author='Qing luan',
    author_email='darkhackdevil@gmail.com',
    license='MIT',
    zip_safe=False,
    packages=find_packages(),
    install_requires=['termcolor','simplejson', 'fabric3'],
    entry_points={
    	'console_scripts': ['enuma-elish=Enuma_Elish.cmd:main']
    },

)


