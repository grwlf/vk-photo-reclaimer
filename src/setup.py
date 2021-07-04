from setuptools import setup, find_packages
from distutils.spawn import find_executable


setup(
  name="vk_photo_reclaimer",
  version="1.0.0",
  # https://mypy.readthedocs.io/en/latest/installed_packages.html
  zip_safe=False,
  scripts=['vk_photo_reclaimer.py'],
  python_requires='>=3.7',
  install_requires = ['vk_api>=11.9.4', 'requests', 'httplib2'],
)
