import re
import errors
from eval import *
			
class printf(Function):
    def __init__(self, fmt, *args):
        super().__init__("printf", args)
        self.format = fmt
        if len(args) == 0:
            self.args=[fmt]
            self.format="%1"

    def _call(self):
        def replacer(match):
            index = int(match.group(1)) - 1
            if index < 0 or index >= len(self.args):
                return f"<arg{index + 1}?>"
            return str(self.args[index])
        
        # Replace %1, %2, ..., %n with the corresponding argument
        pattern = re.compile(r"%(\d+)")
        output = pattern.sub(replacer, self.format)
        print(output, end="")

class format(Function):
    def __init__(self, fmt, *args):
        super().__init__("format", args)
        self.format = fmt

        if len(args) == 0:
            errors.InterpreterError(None, "Runtime Error: Unexpected arguments for format")
        
    def _call(self):
        def replacer(match):
            index = int(match.group(1)) - 1
            if index < 0 or index >= len(self.args):
                return f"<arg{index + 1}?>"
            return str(self.args[index])
        
        # Replace %1, %2, ..., %n with the corresponding argument
        pattern = re.compile(r"%(\d+)")
        output = pattern.sub(replacer, self.format)
        return output
class CreateClass:
    def __init__(self, prototype_table):
        self.prototype_table = prototype_table

    def _call(self):
        new_instance = Table() 
        new_instance.elements.update(self.prototype_table.elements)
        new_instance.elements['$class'] = True 
        return new_instance
