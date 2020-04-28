from dotenv import load_dotenv
from os import getenv
from sys import argv
import re

regex = []
regex_path = r".\dependancies\re"
env_path = r".\dependancies\instructions.env"

hex_symbols=["a","b","c","d","e","f","A","B","C","D","E","F","h"]

# gets the regex for all expressions
def load_regex():
    global regex
    with open(regex_path, "r") as f:
        regex = f.read().split('\n')

def check_input(r, l):
    check = re.match(r, l)
    return check



# gets the title of the instruction in instructions.env
def get_instruction(check):
    print(check.group(0), end=" --> ")
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
def get_register_bin(check, element):
    register = check.group(element)
    register = int(register.replace("[","").replace("]","")[1:])

    if 0 > register or register > 7 :
        handle_error(f"the register [r{register}] is not valid")

    register = bin(register)[2:]

    return f"{register:0>3}"

# transfomrs hex values to bin for convenience
def get_inm8_bin(check, element):
    inm8 = check.group(element)

    if any(ele in inm8 for ele in hex_symbols):
        inm8 = inm8.replace('h','')

        if len(str(inm8)) > 2:
            handle_error(f"{inm8} is not a 8 bit number")

        inm8 = bin(int(inm8, 16))[2:]
        
    else:
        inm8 = int(inm8)

        if 0 > inm8 or 255 < inm8:
            handle_error(f"{inm8} is not a 8 bit number")

        inm8 = bin(inm8)[2:]

    return f"{inm8:0>8}"


# gets the instruction template from instructions.env
# and transfomrs them to binary
def set_bin(instruction, check):
    instruction_bin = getenv(instruction)
    instruction_bin = instruction_bin.split('_')
    
    if len(instruction_bin) == 1:
        pass

    elif len(instruction_bin) == 2:
        instruction_bin[1] = get_inm8_bin(check, 2)

    elif len(instruction_bin) == 3:
        instruction_bin[1] = get_register_bin(check, 2)
        if ("inm8" in instruction_bin[2]):
            instruction_bin[2] = get_inm8_bin(check, 3)

    elif len(instruction_bin) == 4:
        instruction_bin[1] = get_register_bin(check, 2)
        instruction_bin[2] = get_register_bin(check, 3)

    elif len(instruction_bin) == 5:
        instruction_bin[1] = get_register_bin(check, 2)
        instruction_bin[2] = get_register_bin(check, 3)
        instruction_bin[3] = get_register_bin(check, 4)

    return "".join(instruction_bin)


# transfomr the binary instructions to hexadecimal
def set_hex(instruction_bin):
    instruction_hex = hex(int(instruction_bin, 2))[2:]

    return f"{instruction_hex:0>4}"

def set_to_ct(check):
    instruction = get_instruction(check)
    instruction_bin = set_bin(instruction, check)
    res = set_hex(instruction_bin).upper()

    print(res + "h")

    return res

def handle_error(msg):
    print(msg)

    exit()

def operate(expression, text = []):
    is_valid = False

    for r in regex:
        check = check_input(r, expression)

        if check != None:
            ct_expression = set_to_ct(check)
            text.append(ct_expression)
            is_valid = True

    return is_valid

def operate_file():
    text = []
    with open("input.txt", "r") as f:
        for counter, line in enumerate(f.readlines()):

            line = line.replace('\n', '')
            is_valid = operate(line, text)

            if (not is_valid):
                handle_error(f"LEARN HOW TO WRITE GODDAMMIT!!!!\nThe instruction [{line}] introduced at line [{counter}] is not a valid one.")

    with open("output.mem", "w") as f:
        f.write("\n".join(text))

def operate_input():
    expression = input("input preffered expression, exit to close\n")

    while (expression != "exit"):
        operate(expression)
        expression = input()

def operate_command_line():
    expression = " ".join(argv[2:])

    is_valid = operate(expression)
    
    if (not is_valid):
        print("you wot mate?")


def main():

    if len(argv) == 1:
        operate_file()
    elif argv[1] == "-i":
        operate_input()
    elif argv[1] == "-c":
        operate_command_line()
    else:
        print("invalid command")



if __name__ == "__main__":
    load_dotenv(env_path)
    load_regex()
    main()