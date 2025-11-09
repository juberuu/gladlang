import sys
from runtime import SymbolTable, Context
from values import Number, BuiltInFunction
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("INPUT", BuiltInFunction("INPUT"))
global_symbol_table.set("STR", BuiltInFunction("STR"))
global_symbol_table.set("INT", BuiltInFunction("INT"))
global_symbol_table.set("FLOAT", BuiltInFunction("FLOAT"))
global_symbol_table.set("BOOL", BuiltInFunction("BOOL")) 

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    
    if result.should_return:
        return result.return_value, result.error

    return result.value, result.error

if __name__ == '__main__':
    
    GLADLANG_VERSION = "0.1.0"
    GLADLANG_HELP = f"""
Usage: gladlang [command] [filename]

Commands:
  <no arguments>    Start the interactive GladLang shell.
  [filename.glad]   Execute a GladLang script file.
  --help            Show this help message and exit.
  --version         Show the interpreter version and exit.
"""

    if len(sys.argv) == 1:
        print(f"Welcome to GladLang (v{GLADLANG_VERSION})") 
        print("Type 'exit' or 'quit' to close the shell.")
        print("--------------------------------------------------")

        full_text = ""
        while True:
            try:
                if not full_text:
                    line = input('GladLang > ') 
                    if line.strip().lower() in ('exit', 'quit'):
                        break
                else:
                    line = input('...       > ')
                
                strip_line = line.strip()
                if strip_line.startswith('DEF ') or strip_line.startswith('CLASS ') or strip_line.startswith('IF ') or strip_line.startswith('WHILE ') or strip_line.startswith('FOR '):
                    full_text += line + "\n"
                    continue
                
                if full_text:
                    if strip_line == 'ENDEF' or strip_line == 'ENDCLASS' or strip_line == 'ENDIF' or strip_line == 'ENDWHILE' or strip_line == 'ENDFOR':
                        full_text += line + "\n"
                        result, error = run('<stdin>', full_text)
                        full_text = ""
                        
                        if error:
                            print(error.as_string())
                        
                        continue
                    else:
                        full_text += line + "\n"
                        continue
                
                if strip_line == '':
                    continue
                    
                result, error = run('<stdin>', line)

                if error:
                    print(error.as_string())
                
            except EOFError:
                print("\nExiting.")
                break
            except KeyboardInterrupt:
                print("\nExiting.")
                break
                
    elif len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg == '--help':
            print(GLADLANG_HELP)
            
        elif arg == '--version':
            print(f"GladLang v{GLADLANG_VERSION}")
            
        else:
            try:
                filename = arg
                with open(filename, 'r') as f:
                    text = f.read()
                
                result, error = run(filename, text)

                if error:
                    print(error.as_string(), file=sys.stderr)
            
            except FileNotFoundError:
                print(f"File not found: '{filename}'", file=sys.stderr)
            except Exception as e:
                print(f"An unexpected error occurred: {e}", file=sys.stderr)
    
    else:
        print("Error: Too many arguments.")
        print("Usage: gladlang [filename.glad] or gladlang --help")