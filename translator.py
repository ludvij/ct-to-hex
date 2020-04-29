from os import getenv
from sys import argv
import re
import ct_emulator

regex = []
regex_path = r".\dependancies\re"
env_path = r".\dependancies\instructions.env"
is_valid = False

hex_symbols=["a","b","c","d","e","f","A","B","C","D","E","F","h"]

def does_this_fucking_work():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
        from dotenv import load_dotenv
        load_dotenv(env_path)

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
    validated_instruction = check.group(1)

    if validated_instruction == "mov":
        if "[" in check.group(2):
            return "mov1"
        elif "[" in check.group(3):
            return "mov2"
        else:
            return "mov0"
    elif validated_instruction == "jmp":
        if "r" in check.group(2):
            return "jmp1"
        else:
            return "jmp0"
    elif validated_instruction == "call":
        if "r" in check.group(2):
            return "call1"
        else:
            return "call0"
    else:
        return str(validated_instruction)

# transforms registers to their bin value
def get_register_bin(check, element):
    register = check.group(element)
    register = int(register.replace("[","").replace("]","")[1:])

    if register > 7 :
        handle_error(f"the register [r{register}] is not valid")

    register = bin(register)[2:]

    return f"{register:0>3}"


def to_hex(val, n):
    return hex((val + (1 << n)) % (1 << n))

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

        if -128 > inm8 or 127 < inm8:
            handle_error(f"{inm8} is not a 8 bit number")

        inm8 = to_bin(inm8)[2:]

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

def to_bin(val):
    return bin((val) %  (1 << 8))

# transfomr the binary instructions to hexadecimal
def set_hex(instruction_bin):
    return f"{hex((int(instruction_bin, 2) + (1 << 16)) % (1 << 16))}"


def clock_instruction(check):
    instruction = get_instruction(check)
    clk_instruction = "clk_" + instruction

    return int(getenv(clk_instruction))


def set_to_ct(check):
    instruction = get_instruction(check)

    instruction_bin = set_bin(instruction, check)
    res = set_hex(instruction_bin)[2:].upper()

    return res

def handle_error(msg, close=False):
    print(msg)

    if (close): exit()

    global is_valid; is_valid = False


# operates the current expression
# if clock is enabled, gets the clock cycles that it takes
def operate(expression, clock, text = []):
    global is_valid; is_valid = False
    output = ""
    cycles = 0

    for r in regex:
        check = check_input(r, expression)

        if check != None:
            is_valid = True
            ct_expression = set_to_ct(check)
            output = f'{expression} --> {ct_expression}h'
            text.append(ct_expression)

            if (clock): 
                cycles = clock_instruction(check)

    return output, cycles

# transalates the instruciotns in a given file
def operate_file(clock):
    text = []
    total_cycles = 0
    with open("input.txt", "r") as f:
        for counter, line in enumerate(f.readlines()):

            line = line.replace('\n', '')
            
            output, cycles = operate(line, clock, text)
            if (clock): 
                output += f" takes {cycles} clock cycles"
                total_cycles += cycles

            if (not is_valid):
                handle_error(f"The instruction [{line}] introduced at line [{counter}] is not valid", True)

            print(output)

    return text, total_cycles

#translates via input
def operate_input(clock=False):
    total_cycles = 0
    expression = input("input preffered expression, exit to close\n")

    while (expression != "exit"):
        output, cycles = operate(expression, clock)

        if clock:
            output += f" takes {cycles} clock cycles"
            total_cycles += cycles

        if (is_valid): print(output)
        else: handle_error(f"the instruction [{expression}] is not valid")

        expression = input()

    return total_cycles

#uses the command line, kinda gimmicky
def operate_command_line(clock=False):
    expression = " ".join(argv[2:])

    output, cycles = operate(expression, clock)

    if clock:
        output += f" takes {cycles} clock cycles"
    
    if (not is_valid):
        handle_error(f"The instruction [{expression}] is not valid", True)
    
    print(output)


def file_stuff(clock=False):
    text, cycles = operate_file(clock)

    with open("output.mem", "w") as f:
        f.write("\n".join(text))
    if cycles != 0:
        print(f'{cycles} total clock cycles')

def main():
    does_this_fucking_work()
    load_regex()
    enable_clock = False

    if "-clk" in argv:
        enable_clock = True 

    if len(argv) == 1 or '-f' in argv:   
        file_stuff(enable_clock)

    elif "-i" in argv:                   
        operate_input(enable_clock)

    elif argv[1] == "-c" or argv[1] == "-clk":                   
        operate_command_line(enable_clock)

    else: 
        handle_error("invalid command line argument\nValid ones are: -c -i -clk", True)



if __name__ == "__main__":
    main()