import setuptools

setuptools.setup(
  name='sickle-pdk',
  version="4.1.1",
  author="Milton Valencia (wetw0rk)",
  description="Payload Development Kit",
  url="https://github.com/wetw0rk/sickle-pdk",
  entry_points={
    'console_scripts': [
      'sickle-pdk = sickle.__main__:entry'
    ]
  },

  classifiers=[
    "Operating System :: OS Independent",
  ],
)
