from dotenv import load_dotenv
from os import getenv
import re

load_dotenv(r"C:\Users\luisv\Desktop\translator\instructions.env")

# gets the regex for all expressions
def get_reg():
    reg = []
    with open("re.txt", "r") as f:
        for l in f.readlines():
            l = l.replace("\n","")
            reg.append(l)
    return reg

def check_input(r, l):
    check = re.match(r, l)
    return check


# gets the title of the instruction in instructions.env
def get_instruction(check):
    print(check.group(0))
    group1 = check.group(1)

    if group1 == "mov":
        if "[" in check.group(2):
            return "mov1"
        elif "[" in check.group(3):
            return "mov2"
        else:
            return "mov0"
    elif group1 == "jmp":
        if "r" in check.group(2):
            return "jmp1"
        else:
            return "jmp0"
    elif group1 == "call":
        if "r" in check.group(2):
            return "call1"
        else:
            return "call0"
    else:
        return str(group1)

# transforms registers to their bin value
def get_register_bin(check, groupN):
    g = check.group(groupN)
    g = g.replace("[","").replace("]","")
    g = bin(int(g[1]))[2:]
    return f"{g:0>3}"

# transfomrs hex values to bin for convenience
def get_inm8_bin(check, groupN):
    g = bin(int(check.group(groupN), 16))[2:]
    g = f"{g:0>8}"
    return g


# gets the instruction template from instructions.env
# and transfomrs them to binary
def set_bin(instruction, check):
    i_bin = getenv(instruction)
    i_bin = i_bin.split('_')
    
    if len(i_bin) == 1:
        pass

    elif len(i_bin) == 2:
        i_bin[1] = get_inm8_bin(check, 2)

    elif len(i_bin) == 3:
        i_bin[1] = get_register_bin(check, 2)
        if ("inm8" in i_bin[2]):
            i_bin[2] = get_inm8_bin(check, 3)

    elif len(i_bin) == 4:
        i_bin[1] = get_register_bin(check, 2)
        i_bin[2] = get_register_bin(check, 3)

    elif len(i_bin) == 5:
        i_bin[1] = get_register_bin(check, 2)
        i_bin[2] = get_register_bin(check, 3)
        i_bin[3] = get_register_bin(check, 4)

    return "".join(i_bin)


# transfomr the binary instructions to hexadecimal
def set_hex(i_bin):
    i_hex = hex(int(i_bin, 2))[2:]

    return f"{i_hex:0>4}"

def main():
    reg = get_reg()

    with open("output.mem", "w") as o:
        with open("input.txt", "r") as i:
            for l in i.readlines():
                l = l.replace("\n", "")
                for r in reg:
                    check = check_input(r, l)
                    if check != None:
                        instruction = get_instruction(check)
                        i_bin = set_bin(instruction, check)
                        i_hex = set_hex(i_bin)
                        o.write(f"{i_hex.upper()}\n")



if __name__ == "__main__":
    main()