class CTEmulatorException(Exception):
    pass

class EmulatorSnapshot:
    instructions_to_cycles = {
            "nop": 4,
            "mov": 4,
            "movm": 6,
            "movl": 4,
            "movh": 4,
            "push": 7,
            "pop": 6,
            "add": 6,
            "sub": 6,
            "or": 6,
            "and": 6,
            "xor": 6,
            "cmp": 5,
            "not": 2,
            "inc": 2,
            "dec": 2,
            "neg": 2,
            "jmpreg": 4,
            "jmp": 6,
            "br": 6
            }

    def __init__(self, registers, memory, instructions):
        self.registers = registers.copy()
        self.memory = memory.copy()
        self.instructions = [instruction for instruction in instructions]

    def get_cycles(self):
        s = 0
        for instruction in self.instructions:
            if "mov" in instruction and "[" in instruction:
                instruction = "movm"
            if "jmp" in instruction and "r" in instruction:
                instruction = "jmpreg"
            if "br" in instruction:
                instruction = "br"

            head = instruction.split(" ")[0]
            s += EmulatorSnapshot.instructions_to_cycles[head]

        return s

class RegisterArray:
    def __init__(self, n_registers, w_size):
        self.registers = [0] * n_registers
        self.size = 2**w_size

    def copy(self):
        new = RegisterArray(len(self.registers), self.size**.5)
        for index, val in enumerate(self.registers):
            new.set(index, val)

        return new

    def set(self, register, value):
        if not self.register_value_valid(value):
            raise CTEmulatorException(f"Value outside range {value}")
        if not self.register_address_valid(register):
            raise CTEmulatorException(f"Tried to acess nonexistent register {register}")

        self.registers[register] = value

    def get(self, register):
        if not self.register_address_valid(register):
            raise CTEmulatorException("Tried to acess nonexistent register")
        
        return self.registers[register]

    def register_value_valid(self, value):
        return value >= 0 and value <= self.size
    
    def register_address_valid(self, address):
        return address >= 0 and address < len(self.registers)

class Memory:
    def __init__(self, n_slots, w_size):
        self.max_address = n_slots - 1
        self.size = 2**w_size
        self.mem = {}

    def copy(self):
        new = Memory(self.max_address + 1, self.size**.5)
        new.mem = self.mem.copy()

    def set(self, address, value):
        if not self.value_valid(value):
            raise CTEmulatorException("Tried to get in memory a value too large")
        if not self.address_valid(address):
            raise CTEmulatorException("Tried to access outside memory")

        self.mem[address] = value

    def get(self, address):
        if not self.address_valid(address):
            raise CTEmulatorException("Tried to access outside memory")

        if address in self.mem:
            return self.mem[address]
        else: return 0

    def address_valid(self, address):
        return address >= 0 and address < self.max_address

    def value_valid(self, value):
        return value >= 0 and value <= self.size

class CTEmulator:
    def __init__(self, n_registers=8, w_size=16, mem_size=2**16):
        self.registers = RegisterArray(n_registers, w_size)
        self.memory = Memory(mem_size, w_size)
        self.instructions = []
        self.ZCOS = {"z": 0, "c": 0, "o": 0, "s": 0}
        self.to_skip = 0

    def get_register_number(self, reg):
        if "[" in reg:
            return int(reg[2:-1])
        else:
            return int(reg[1:])
    
    def separate_instruction(self, instruction):
        name, *regs = instruction.split(" ")
        args = [a.replace(",", "").strip() for a in regs]
        return name, *args

    def get_snapshot(self):
        return EmulatorSnapshot(self.registers, self.memory, self.instructions)

    def execute_instruction(self, instruction):
        if self.to_skip > 0:
            self.to_skip -= 1
            return
        
        name = instruction.split(" ")[0].lower()
        if "br" in name:
            instruction = self.convert_br(instruction)
            name = instruction.split(" ")[0].lower()
        self.instructions.append(instruction)
        print(instruction)

        if name == "nop": return
        elif name in ["mov", "movl", "movh"]: self.mov_instruction(instruction)
        elif name == "add": self.add_instruction(instruction)
        elif name == "sub": self.sub_instruction(instruction)
        elif name == "cmp": self.cmp_instruction(instruction)
        elif name == "or": self.or_instruction(instruction)
        elif name == "and": self.and_instruction(instruction)
        elif name == "xor": self.xor_instruction(instruction)
        elif name == "push": self.push_instruction(instruction)
        elif name == "pop": self.pop_instruction(instruction)
        elif name == "not": self.not_instruction(instruction)
        elif name == "inc": self.inc_instruction(instruction)
        elif name == "dec": self.dec_instruction(instruction)
        elif name == "neg": self.neg_instruction(instruction)
        elif name == "jmp": self.jmp_instruction(instruction)
        elif name.startswith("br"): self.br_instruction(instruction)
        else:
            raise CTEmulatorException(f"Invalid instruction {instruction}")

    def pop_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        val = self.registers.get(r1)
        r7_val = self.registers.get(7)
        r7_val += 1
        self.memory.set(r7_val, val)

    def push_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        r7_val = self.registers.get(7)
        val = self.memory.get(r7_val)
        r7_val += 1
        self.registers.set(r1, val)

    def br_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        self.do_jump(r1)

    def convert_br(self, instruction):
        name, r1 = self.separate_instruction(instruction) 
        subcond = name.replace("br", "")
        print(self.ZCOS)
        if subcond == "c" and self.ZCOS["c"] or \
           subcond == "nc" and not self.ZCOS["c"] or \
           subcond == "z" and self.ZCOS["z"] or \
           subcond == "nz" and not self.ZCOS["z"] or \
           subcond == "o" and self.ZCOS["o"] or \
           subcond == "no" and not self.ZCOS["o"] or \
           subcond == "s" and self.ZCOS["s"] or \
           subcond == "ns" and not self.ZCOS["s"]: return instruction
        return "nop"

    def jmp_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        self.do_jump(r1)

    def do_jump(self, val):
        if "r" in val:
            r1 = self.get_register_number(val)
            mov = self.registers.get(r1)
        else:
            mov = int(val[:-1],16)
            if bin(mov)[3] == "1":
                mov = -((1<<16) - mov)

        if mov < 0:
            to_repeat = self.instructions[mov:]
            for instruction in to_repeat:
                self.execute_instruction(instruction)
        else:
            self.to_skip = mov

    def neg_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        a = self.registers.get(r1)
        a = (~a & (1<<17 - 1)) + 1

    def dec_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        a = self.registers.get(r1)
        self.registers.set(r1, a - 1)
        
    def inc_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        a = self.registers.get(r1)
        self.registers.set(r1, a + 1)

    def not_instruction(self, instruction):
        _, r1 = self.separate_instruction(instruction) 
        r1 = self.get_register_number(r1)
        a = self.registers.get(r1)
        a = ~a & (1<<17 - 1)
        self.registers.set(r1, a)

    def xor_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2, r3 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r2)
        b = self.registers.get(r3)
        res = a ^ b
        self.registers.set(r1, res)

    def and_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2, r3 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r2)
        b = self.registers.get(r3)
        res = a & b
        self.registers.set(r1, res)

    def or_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2, r3 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r2)
        b = self.registers.get(r3)
        res = a | b
        self.registers.set(r1, res)

    def cmp_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r1)
        b = self.registers.get(r2)

        if a < b:
            self.ZCOS["c"] = 1
        else:
            self.ZCOS["c"] = 0

        if a - b == 0:
            self.ZCOS["z"] = 1
        else:
            self.ZCOS["z"] = 0

        if bin(a - b)[0] == '1':
            self.ZCOS["s"] == 1
        else:
            self.ZCOS["s"] = 0

    def sub_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2, r3 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r2)
        b = self.registers.get(r3)
        self.registers.set(r1, a - b)

        if a < b:
            self.ZCOS["c"] = 1
        if a - b == 0:
            self.ZCOS["z"] = 1
        if bin(a - b)[0] == '1':
            self.ZCOS["s"] == 1

    def add_instruction(self, instruction):
        _, *regs = self.separate_instruction(instruction) 
        r1, r2, r3 = (self.get_register_number(r) for r in regs)
        a = self.registers.get(r2)
        b = self.registers.get(r3)
        self.registers.set(r1, a + b)

        if bin(a + b)[0] == '1':
            self.ZCOS["s"] == 1

    def mov_instruction(self, instruction):
        name, r1, r2 = self.separate_instruction(instruction)
        r1_address = self.get_register_number(r1)

        if name == "movl":
            val = int(r2[:-1], 16)
            self.registers.set(r1_address, val)
        elif name == "movh":
            val = int(r2[:-1], 16)
            prev = self.registers.get(r1_address)
            self.registers.set(r1_address, val*16**2 + prev)
        else:
            r2_address = self.get_register_number(r2)
            if "[" in r1 and "[" in r2:
                raise CTEmulatorException(f"Invalid instruction {instruction}")
            if "[" in r1:
                address = self.registers.get(r1_address)
                val = self.registers.get(r2_address)
                self.memory.set(address, val)
            elif "[" in r2:
                address = self.registers.get(r2_address)
                val = self.memory.get(address)
                self.registers.set(r1_address, val)
            else:
                val = self.registers.get(r2_address)
                self.registers.set(r1_address, val)
