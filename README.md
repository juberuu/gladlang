# GladLang

**GladLang is a dynamic, interpreted, object-oriented programming language.** This is a full interpreter built from scratch in Python, complete with a lexer, parser, and runtime environment. It supports modern programming features like closures, classes, inheritance, and robust error handling.

![Lines of code](https://sloc.xyz/github/gladw-in/gladlang)

This is the full overview of the GladLang language, its features, and how to run the interpreter.

## Table of Contents

- [About The Language](#about-the-language)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
    - [Running a Script](#running-a-script)
    - [Using the Interactive Shell](#using-the-interactive-shell)
    - [Building the Executable](#building-the-executable)
- [Language Tour (Syntax Reference)](#language-tour-syntax-reference)
    - [1. Comments](#1-comments)
    - [2. Variables and Data Types](#2-variables-and-data-types)
        - [Variables](#variables)
        - [Numbers](#numbers)
        - [Strings](#strings)
        - [Lists](#lists)
        - [Booleans](#booleans)
        - [Null](#null)
    - [3. Operators](#3-operators)
        - [Arithmetic & Precedence](#arithmetic--precedence)
        - [Comparison & Logical](#comparison--logical)
        - [Increment / Decrement](#increment--decrement)
    - [4. Control Flow](#4-control-flow)
        - [IF Statements](#if-statements)
        - [WHILE Loops](#while-loops)
        - [FOR Loops](#for-loops)
    - [5. Functions](#5-functions)
        - [Named Functions](#named-functions)
        - [Anonymous Functions](#anonymous-functions)
        - [Closures](#closures)
        - [Recursion](#recursion)
    - [6. Object-Oriented Programming (OOP)](#6-object-oriented-programming-oop)
        - [Classes and Instantiation](#classes-and-instantiation)
        - [The `SELF` Keyword](#the-self-keyword)
        - [Inheritance](#inheritance)
        - [Polymorphism](#polymorphism)
    - [7. Built-in Functions](#7-built-in-functions)
- [Error Handling](#error-handling)
- [Running Tests](#running-tests)
- [License](#license)

-----

## About The Language

GladLang is an interpreter for a custom scripting language. It was built as a complete system, demonstrating the core components of a programming language:

  * **Lexer (`lexer.py`):** A tokenizer that scans source code and converts it into a stream of tokens (e.g., `NUMBER`, `STRING`, `IDENTIFIER`, `KEYWORD`, `PLUS`).
  * **Parser (`parser.py`):** A parser that takes the token stream and builds an Abstract Syntax Tree (AST), representing the code's structure.
  * **AST Nodes (`nodes.py`):** A comprehensive set of nodes that define every syntactic structure in the language (e.g., `BinOpNode`, `IfNode`, `FunDefNode`, `ClassNode`).
  * **Runtime (`runtime.py`):** Defines the `Context` and `SymbolTable` for managing variable scope, context (for tracebacks), and closures.
  * **Values (`values.py`):** Defines the language's internal data types (`Number`, `String`, `List`, `Function`, `Class`, `Instance`).
  * **Interpreter (`interpreter.py`):** The core engine that walks the AST and executes the program by visiting each node.
  * **Entry Point (`gladlang.py`):** The main file that ties everything together. It handles command-line arguments, runs files, and starts the interactive shell.

-----

## Key Features

GladLang supports a rich, modern feature set:

  * **Data Types:** Numbers (int/float), Strings, Lists, Booleans, and Null.
  * **Variables:** Dynamic variable assignment with the `LET` keyword.
  * **Operators:** Full set of arithmetic (`+`, `-`, `*`, `/`, `^`), comparison (`==`, `!=`, `<`, `>`), and logical (`AND`, `OR`, `NOT`) operators.
  * **Control Flow:** `IF...THEN...ENDIF`, `WHILE...ENDWHILE`, and `FOR...IN...ENDFOR` loops.
  * **Flow Control:** `BREAK` and `CONTINUE` keywords for loops.
  * **Functions:**
      * First-class citizens (can be passed as arguments and stored in variables).
      * Support for named and anonymous functions.
      * **Closures:** Functions capture their parent's scope.
      * Recursive function calls.
  * **Object-Oriented Programming:**
      * `CLASS...ENDCLASS` syntax.
      * `NEW` keyword for instantiation.
      * `SELF` keyword for instance context.
      * `INHERITS` keyword for class inheritance.
      * Method overriding and polymorphism.
  * **Advanced Operators:** Pre- and post-increment/decrement (`++i`, `i--`).
  * **List Manipulation:** Index access (`my_list[0]`), index assignment (`my_list[0] = 10`), and concatenation (`list1 + list2`).
  * **Built-ins:** `PRINT`, `INPUT`, `STR`, `INT`, `FLOAT`, and `BOOL`.
  * **Error Handling:** Robust, user-friendly runtime error reporting with full tracebacks.

-----

## Getting Started

### Running a Script

You can execute any `.glad` file by passing it as an argument to `gladlang.py`.

```bash
python gladlang.py "test.glad"
```

**Output:**

```
--- OOP & Inheritance Tester ---
--- Creating a Pet ---
A new pet is born!
Sammy makes a generic pet sound.
--- Creating a Dog ---
A new pet is born!
Buddy says: Woof!
Buddy wags its tail.
```

### Using the Interactive Shell

Run the interpreter without any arguments to start the interactive Read-Eval-Print Loop (REPL) shell.

```bash
python gladlang.py
```

**Shell:**

```
Welcome to GladLang (v0.1.0)
Type 'exit' or 'quit' to close the shell.
--------------------------------------------------
GladLang > PRINT "Hello, " + "World!"
Hello, World!
0
GladLang > LET a = 10 * (2 + 3)
0
GladLang > PRINT a
50
0
GladLang > exit
```

## Building the Executable

You can build a **standalone executable** using **PyInstaller**:

```bash
pyinstaller gladlang.py -F --icon=favicon.ico
```

This will create a single-file executable at `dist/gladlang`.

-----

### Adding to System PATH for Global Use

You can then add it to your system **PATH** so it can be run globally as "**gladlang**" from anywhere.

#### Windows:

1.  **Move or copy** the executable to a folder of your choice, for example:
    ```bash
    move dist\gladlang.exe "C:\Programs\GladLang"
    ```
2.  **Add that folder to your system PATH:**
      * Press **Win + R**, type `sysdm.cpl`, press **Enter**.
      * Go to **Advanced** $\rightarrow$ **Environment Variables**.
      * Under **System variables**, select **Path** $\rightarrow$ **Edit** $\rightarrow$ **New**.
      * Add the full path (e.g., `C:\Programs\GladLang`).
3.  **Open a new terminal and test:**
    ```bash
    gladlang "test_recursion.glad"
    ```

#### macOS / Linux:

1.  **Move** the executable to `/usr/local/bin` (or another directory in your PATH):
    ```bash
    sudo mv dist/gladlang /usr/local/bin/
    ```
2.  **Make sure it's executable:**
    ```bash
    sudo chmod +x /usr/local/bin/gladlang
    ```
3.  **Test it anywhere:**
    ```bash
    gladlang "test_recursion.glad"
    ```

Now you can run GladLang from any folder without prefixing `./dist/`.

-----

## Language Tour (Syntax Reference)

Here is a guide to the GladLang syntax, with examples from the `tests/` directory.

### 1\. Comments

Comments start with `#` and last for the entire line.

```glad
# This is a comment.
LET a = 10 # This is an inline comment
```

### 2\. Variables and Data Types

#### Variables

Variables are assigned using the `LET` keyword.

```glad
LET a = 10
LET b = "Hello"
LET my_list = [a, b, 123]
```

#### Numbers

Numbers can be integers or floats. All standard arithmetic operations are supported.

```glad
LET math_result = (1 + 2) * 3 # 9
LET float_result = 10 / 4     # 2.5
```

#### Strings

Strings are defined with double quotes and support escape characters. They can be concatenated with `+`.

```glad
LET newline = "Hello\nWorld"
LET quoted = "She said, \"This is cool!\""
PRINT "Hello, " + "GladLang"
```

#### Lists

Lists are ordered collections of any type. They support indexing, assignment, and concatenation.

```glad
LET my_list = [1, "hello", 2 * 3, TRUE]

PRINT my_list[1] # Access: "hello"

LET my_list[1] = "world" # Assign
PRINT my_list[1] # "world"

LET other_list = my_list + [FALSE, 100]
```

#### Booleans

Booleans are `TRUE` and `FALSE`. They are the result of comparisons and logical operations.

```glad
LET t = TRUE
LET f = FALSE
PRINT t AND f # 0 (False)
PRINT t OR f  # 1 (True)
PRINT NOT t   # 0 (False)
```

**Truthiness:** `0`, `0.0`, `""`, `NULL`, and `FALSE` are "falsy." All other values (including non-empty strings, non-zero numbers, lists, functions, and classes) are "truthy."

#### Null

The `NULL` keyword represents a null or "nothing" value. It is falsy and prints as `0`. Functions with no `RETURN` statement implicitly return `NULL`.

-----

### 3\. Operators

#### Arithmetic & Precedence

`^` (power), `*`, `/` (division), `+`, `-`. Standard operator precedence is respected.

```glad
PRINT 1 + 2 * 3   # 7
PRINT (1 + 2) * 3 # 9
```

#### Comparison & Logical

  * **Comparison:** `==`, `!=`, `<`, `>`, `<=`, `>=`
  * **Logical:** `AND`, `OR`, `NOT`

<!-- end list -->

```glad
PRINT (10 < 20) AND (10 != 5) # 1 (True)
```

#### Increment / Decrement

Supports C-style pre- and post-increment/decrement operators on variables and list elements.

```glad
LET i = 5
PRINT i++ # 5
PRINT i   # 6
PRINT ++i # 7
PRINT i   # 7

LET my_list = [10, 20]
PRINT my_list[1]++ # 20
PRINT my_list[1]   # 21
```

-----

### 4\. Control Flow

#### IF Statements

Uses `IF...THEN...ENDIF` syntax.

```glad
LET num = -5
IF num < 0 THEN
  PRINT "It is negative."
ENDIF
```

#### WHILE Loops

Loops while a condition is `TRUE`.

```glad
LET i = 3
WHILE i > 0
  PRINT "i = " + i
  LET i = i - 1
ENDWHILE

# Prints:
# i = 3
# i = 2
# i = 1
```

#### FOR Loops

Iterates over the elements of a list.

```glad
LET my_list = ["apple", "banana", "cherry"]
FOR item IN my_list
  PRINT "Item: " + item
ENDFOR
```

**`BREAK` and `CONTINUE`** are supported in both `WHILE` and `FOR` loops.

-----

### 5\. Functions

#### Named Functions

Defined with `DEF...ENDEF`. Arguments are passed by value. `RETURN` sends a value back.

```glad
DEF add(a, b)
  RETURN a + b
ENDEF

LET sum = add(10, 5)
PRINT sum # 15
```

#### Anonymous Functions

Functions can be defined without a name, perfect for assigning to variables.

```glad
LET double = DEF(x)
  RETURN x * 2
ENDEF

PRINT double(5) # 10
```

#### Closures

Functions capture variables from their parent scope.

```glad
DEF create_greeter(greeting)
  DEF greeter_func(name)
    # 'greeting' is "closed over" from the parent
    RETURN greeting + ", " + name + "!"
  ENDEF
  RETURN greeter_func
ENDEF

LET say_hello = create_greeter("Hello")
PRINT say_hello("Alex") # "Hello, Alex!"
```

#### Recursion

Functions can call themselves.

```glad
DEF fib(n)
  IF n <= 1 THEN
    RETURN n
  ENDIF
  RETURN fib(n - 1) + fib(n - 2)
ENDEF

PRINT fib(7) # 13
```

-----

### 6\. Object-Oriented Programming (OOP)

#### Classes and Instantiation

Use `CLASS...ENDCLASS` to define classes and `NEW` to create instances. The constructor is `init`.

```glad
CLASS Counter
  DEF init(self)
    SELF.count = 0 # 'SELF' is the instance
  ENDEF
  
  DEF increment(self)
    SELF.count = SELF.count + 1
  ENDEF
  
  DEF get_count(self)
    RETURN SELF.count
  ENDEF
ENDCLASS
```

#### The `SELF` Keyword

`SELF` is the mandatory first argument for all methods and is used to access instance attributes and methods.

```glad
LET c = NEW Counter()
c.increment()
PRINT c.get_count() # 1
```

#### Inheritance

Use the `INHERITS` keyword. Methods can be overridden by the child class.

```glad
CLASS Pet
  DEF init(self, name)
    SELF.name = name
  ENDEF
  
  DEF speak(self)
    PRINT SELF.name + " makes a generic pet sound."
  ENDEF
ENDCLASS

CLASS Dog INHERITS Pet
  # Override the 'speak' method
  DEF speak(self)
    PRINT SELF.name + " says: Woof!"
  ENDEF
ENDCLASS

LET my_dog = NEW Dog("Buddy")
my_dog.speak() # "Buddy says: Woof!"
```

#### Polymorphism

When a base class method calls another method on `SELF`, it will correctly use the **child's overridden version**.

```glad
CLASS Pet
  DEF introduce(self)
    PRINT "I am a pet and I say:"
    SELF.speak() # This will call the child's 'speak'
  ENDEF
  
  DEF speak(self)
    PRINT "(Generic pet sound)"
  ENDEF
ENDCLASS

CLASS Cat INHERITS Pet
  DEF speak(self)
    PRINT "Meow!"
  ENDEF
ENDCLASS

LET my_cat = NEW Cat("Whiskers")
my_cat.introduce()
# Prints:
# I am a pet and I say:
# Meow!
```

-----

### 7\. Built-in Functions

  * `PRINT(value)`: Prints a value to the console.
  * `INPUT()`: Reads a line of text from the user as a String.
  * `STR(value)`: Casts a value to a String.
  * `INT(value)`: Casts a String or Float to an Integer.
  * `FLOAT(value)`: Casts a String or Integer to a Float.
  * `BOOL(value)`: Casts a value to its Boolean representation (`TRUE` or `FALSE`).

-----

## Error Handling

GladLang features detailed error handling and prints full tracebacks for runtime errors, making debugging easy.

**Example: Name Error** (`test_name_error.glad`)

```
Traceback (most recent call last):
  File test_name_error.glad, line 6, in <program>
Runtime Error: 'b' is not defined
```

**Example: Type Error** (`test_type_error.glad` with input "5")

```
Traceback (most recent call last):
  File test_type_error.glad, line 6, in <program>
Runtime Error: Illegal operation
```

**Example: Argument Error** (`test_arg_error.glad`)

```
Traceback (most recent call last):
  File test_arg_error.glad, line 7, in <program>
  File test_arg_error.glad, line 4, in add
Runtime Error: Incorrect argument count for 'add'. Expected 2, got 3
```

-----

## Running Tests

The `tests/` directory contains a comprehensive suite of `.glad` files to test every feature of the language. You can run any test by executing it with the interpreter:

```bash
python gladlang.py "test_closures.glad"
python gladlang.py "test_lists.glad"
python gladlang.py "test_polymorphism.glad"

```

or 

```bash
gladlang "test_closures.glad"
gladlang "test_lists.glad"
gladlang "test_polymorphism.glad"
```

## License

You can use this under the MIT License. See [LICENSE](LICENSE) for more details.