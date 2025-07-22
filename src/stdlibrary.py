import re
import errors

class Function:
	def __init__(self, name, args):
		self.name = name
		self.args = args
			
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
        super().__init__("printf", args)
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

stdlibrary={}
stdlibrary['printf'] = printf
stdlibrary['format'] = format
