# Sickle Documentation

Currently the API used by modules is not documented. The source code is the official source of truth in terms of documentation. Since I'm actively working on new modules, the API is subject to change. Ultimately, the goal is to create official documentation for core API functions and make API as easy to use as possible.

# Table of Contents

- [Linux Installation](#linux-installation)
- [Windows Installation](#windows-installation)
- [Supported Distributions](#supported-distributions)

# Linux Installation

After Python has been installed, simply clone the Sickle repository.

```
$ git clone https://github.com/wetw0rk/sickle-pdk.git
```

Once cloned, enter the `sickle-pdk/src` directory and install the requirements using `pip3`. 

```
$ sudo pip3 install -r requirements.txt
```

If you encounter any issues installing from requirements.txt you may need to install cmake as it is used by the Keystone Engine (`sudo apt install cmake -y`). Once dependencies have been installed simply run `setup.py` as shown below.

```
$ sudo python3 setup.py install
```

And you should be good to go!

```
$ sickle-pdk -h
usage: sickle-pdk [-h] [-r READ] [-p PAYLOAD] [-f FORMAT] [-m MODULE] [-a ARCH] [-b BADCHARS] [-v VARNAME] [-i] [-l [LIST]]

Sickle - Payload Development Kit

options:
  -h, --help               Show this help message and exit
  -r, --read READ          Read bytes from binary file (use - for stdin)
  -p, --payload PAYLOAD    Shellcode to use
  -f, --format FORMAT      Output format (--list for more info)
  -m, --module MODULE      Development module
  -a, --arch ARCH          Select architecture for disassembly
  -b, --badchars BADCHARS  Bad characters to avoid in shellcode
  -v, --varname VARNAME    Alternative variable name
  -i, --info               Print detailed info for module or payload
  -l, --list [LIST]        List available formats, payloads, or modules
```

# Windows Installation

After Python has been installed, Windows installation is just as easy as installion on Linux. First clone the repository.

```
C:\>git clone https://github.com/wetw0rk/sickle-pdk.git
```

Once cloned, enter the `sickle-pdk/src` directory and install the requirements using `pip3`.

```
C:\sickle-pdk\src>pip3 install -r requirements.txt
```

Once dependencies have been installed simply run `setup.py` as shown below.

```
C:\sickle-pdk\src>python setup.py install
```

The last step is to enable ANSI colors. To do this simply double click the enable-ansi.reg located in the documentation folder within the repository. Upon completion, if everything went well, you should be able to run sickle from anywhere.

```
C:\sickle-pdk\src>sickle-pdk -h
usage: sickle-pdk [-h] [-r READ] [-p PAYLOAD] [-f FORMAT] [-m MODULE] [-a ARCH] [-b BADCHARS] [-v VARNAME] [-i]
                  [-l [LIST]]

Sickle - Payload Development Kit

options:
  -h, --help               Show this help message and exit
  -r, --read READ          Read bytes from binary file (use - for stdin)
  -p, --payload PAYLOAD    Shellcode to use
  -f, --format FORMAT      Output format (--list for more info)
  -m, --module MODULE      Development module
  -a, --arch ARCH          Select architecture for disassembly
  -b, --badchars BADCHARS  Bad characters to avoid in shellcode
  -v, --varname VARNAME    Alternative variable name
  -i, --info               Print detailed info for module or payload
  -l, --list [LIST]        List available formats, payloads, or modules
```

# Supported Distributions

Sickle is also currently supported by `Kali Linux` and `Black Arch Linux` and can be installed via `apt`.
