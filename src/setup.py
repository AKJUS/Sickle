import setuptools

setuptools.setup(
  name='sickle',
  version="4.1.0",
  author="Milton Valencia (wetw0rk)",
  description="Payload Development Kit",
  url="https://github.com/wetw0rk/Sickle",
  entry_points={
    'console_scripts': [
      'sickle = sickle.__main__:entry'
    ]
  },

  classifiers=[
    "Operating System :: OS Independent",
  ],
)
