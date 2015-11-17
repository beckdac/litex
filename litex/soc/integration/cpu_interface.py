from litex.gen import *

from litex.soc.interconnect.csr import CSRStatus


def get_cpu_mak(cpu):
    if cpu == "lm32":
        triple = "lm32-elf"
        cpuflags = "-mbarrel-shift-enabled -mmultiply-enabled -mdivide-enabled -msign-extend-enabled"
        clang = ""
    elif cpu == "or1k":
        triple = "or1k-linux"
        cpuflags = "-mhard-mul -mhard-div -mror -mffl1 -maddc"
        clang = "1"
    else:
        raise ValueError("Unsupported CPU type: "+cpu)
    return [
        ("TRIPLE", triple),
        ("CPU", cpu),
        ("CPUFLAGS", cpuflags),
        ("CLANG", clang)
    ]


def get_linker_output_format(cpu_type):
    return "OUTPUT_FORMAT(\"elf32-{}\")\n".format(cpu_type)


def get_linker_regions(regions):
    r = "MEMORY {\n"
    for name, origin, length in regions:
        r += "\t{} : ORIGIN = 0x{:08x}, LENGTH = 0x{:08x}\n".format(name, origin, length)
    r += "}\n"
    return r


def get_mem_header(regions, flash_boot_address):
    r = "#ifndef __GENERATED_MEM_H\n#define __GENERATED_MEM_H\n\n"
    for name, base, size in regions:
        r += "#define {name}_BASE 0x{base:08x}\n#define {name}_SIZE 0x{size:08x}\n\n".format(name=name.upper(), base=base, size=size)
    if flash_boot_address is not None:
        r += "#define FLASH_BOOT_ADDRESS 0x{:08x}\n\n".format(flash_boot_address)
    r += "#endif\n"
    return r


def _get_rw_functions(reg_name, reg_base, nwords, busword, read_only, with_access_functions):
    r = ""

    r += "#define CSR_"+reg_name.upper()+"_ADDR "+hex(reg_base)+"\n"
    r += "#define CSR_"+reg_name.upper()+"_SIZE "+str(nwords)+"\n"

    size = nwords*busword
    if size > 64:
        return r
    elif size > 32:
        ctype = "unsigned long long int"
    elif size > 16:
        ctype = "unsigned int"
    elif size > 8:
        ctype = "unsigned short int"
    else:
        ctype = "unsigned char"

    if with_access_functions:
        r += "static inline "+ctype+" "+reg_name+"_read(void) {\n"
        if size > 1:
            r += "\t"+ctype+" r = MMPTR("+hex(reg_base)+");\n"
            for byte in range(1, nwords):
                r += "\tr <<= "+str(busword)+";\n\tr |= MMPTR("+hex(reg_base+4*byte)+");\n"
            r += "\treturn r;\n}\n"
        else:
            r += "\treturn MMPTR("+hex(reg_base)+");\n}\n"

        if not read_only:
            r += "static inline void "+reg_name+"_write("+ctype+" value) {\n"
            for word in range(nwords):
                shift = (nwords-word-1)*busword
                if shift:
                    value_shifted = "value >> "+str(shift)
                else:
                    value_shifted = "value"
                r += "\tMMPTR("+hex(reg_base+4*word)+") = "+value_shifted+";\n"
            r += "}\n"
    return r


def get_csr_header(regions, constants, with_access_functions=True):
    r = "#ifndef __GENERATED_CSR_H\n#define __GENERATED_CSR_H\n"
    if with_access_functions:
        r += "#include <hw/common.h>\n"
    for name, origin, busword, obj in regions:
        if isinstance(obj, Memory):
            r += "#define CSR_"+name.upper()+"_BASE "+hex(origin)+"\n"
        else:
            r += "\n/* "+name+" */\n"
            r += "#define CSR_"+name.upper()+"_BASE "+hex(origin)+"\n"
            for csr in obj:
                nr = (csr.size + busword - 1)//busword
                r += _get_rw_functions(name + "_" + csr.name, origin, nr, busword, isinstance(csr, CSRStatus), with_access_functions)
                origin += 4*nr

    r += "\n/* constants */\n"
    for name, value in constants:
        r += "#define " + name
        if value is not None:
            if isinstance(value, str):
                r +=  " \"" + value + "\""
            else:
                r += " " + str(value)
        r += "\n"

    r += "\n#endif\n"
    return r


def get_csr_csv(csr_regions=None, constants=None, memory_regions=None):
    r = ""

    if csr_regions is not None:
        for name, origin, busword, obj in csr_regions:
            r += "csr_base,{},0x{:08x},,\n".format(name, origin)

        for name, origin, busword, obj in csr_regions:
            if not isinstance(obj, Memory):
                for csr in obj:
                    nr = (csr.size + busword - 1)//busword
                    r += "csr_register,{}_{},0x{:08x},{},{}\n".format(name, csr.name, origin, nr, "ro" if isinstance(csr, CSRStatus) else "rw")
                    origin += 4*nr

    if constants is not None:
        for name, value in constants:
            r += "constant,{},{},,\n".format(name.lower(), value)

    if memory_regions is not None:
        for name, origin, length in memory_regions:
            r += "memory_region,{},0x{:08x},{:d},\n".format(name.lower(), origin, length)

    return r