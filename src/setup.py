from setuptools import setup, find_packages
from distutils.spawn import find_executable


setup(
  name="vk_photo_reclaimer",
  version="1.0.0",
  # https://mypy.readthedocs.io/en/latest/installed_packages.html
  author="grwlf",
  author_email="grrwlf@gmail.com",
  description="Download and remove your photos from VKontakte now!",
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License V3 (GPLV3)",
    "Operating System :: POSIX :: Linux",
    "Topic :: Multimedia :: Graphics",
    "Development Status :: 3 - Alpha",
  ],
  url="https://github.com/grwlf/vk_photo_reclaimer",
  zip_safe=False,
  scripts=['vk_photo_reclaimer.py'],
  python_requires='>=3.7',
  install_requires = ['vk_api>=11.9.4', 'requests', 'httplib2'],
)
