import os,sys,json
from typing import List,Dict,Optional,Union,Any
import random
import time


def   calculate_stuff(x,y,z):
    """this function does stuff"""
    result=x+y*z
    if result>100:
        print("big number!")
        return result
    else:
            print("small number")
            return result


class  BadClass:
    def __init__(self,name,value):
        self.name=name
        self.value=value
    
    def process_data(self,data:List)->Dict:
        """Process some data badly"""
        output={}
        for i in range(len(data)):
            item=data[i]
            if type(item)==str:
                output[i]=item.upper()
            elif type(item)==int:
                output[i]=item*2
            else:
                output[i]=str(item)
        return output
    
    def bad_formatting(self,x,y,z):
        if x>0:a=x*2
        else:a=0
        if y>0:b=y*3
        else:b=0
        if z>0:c=z*4
        else:c=0
        return a+b+c


def unused_imports_example():
    # random and time are imported but not used here
    data=[1,2,3,4,5]
    total=0
    for i in data:
        total+=i
    return total


async def missing_await(data):
    # This async function doesn't await anything
    processed=[]
    for item in data:
        processed.append(item.upper())
    return processed


def type_issues(items:List[str])->int:
    # Type annotation says int but returns string
    result=""
    for item in items:
        result+=item
    return result  # This returns str, not int!


def    spacing_nightmare(    a    ,    b    ,    c    ):
    """Too much spacing"""
    return     a     +     b     +     c


# Missing newline at end of file


def compare_values(x,y):
    """Bad comparison patterns"""
    if x == True:  # Should be: if x:
        print("x is true")
    if y == False:  # Should be: if not y:
        print("y is false")
    if x == None:  # Should be: if x is None:
        print("x is none")
    if type(x) == int:  # Should use isinstance()
        print("x is int")


def mutable_default_arg(items=[]):  # Mutable default argument!
    items.append("new item")
    return items


def inconsistent_returns(value):
    """Inconsistent return statements"""
    if value > 0:
        return value * 2
    elif value < 0:
        return
    # Missing else case - implicit return None


def    bad_exception_handling():
    """Too broad exception handling"""
    try:
        data = json.loads("{invalid json}")
        result = 10 / 0
        file = open("nonexistent.txt")
    except:  # Bare except - catches everything!
        pass  # Silently ignoring errors


def unused_variables():
    """Variables that are assigned but never used"""
    x = 10
    y = 20
    z = x + y  # z is never used
    result = 100
    temp = result * 2  # temp is never used
    return result


def   bad_string_concatenation(items):
    """Inefficient string concatenation"""
    result = ""
    for item in items:
        result = result + str(item) + ", "  # Should use join()
    return result


def global_usage():
    """Bad use of global variables"""
    global some_var  # Using global when not needed
    some_var = 100
    return some_var * 2


lambda_func = lambda x,y: x+y  # Lambda assigned to variable


def nested_nightmare():
    """Too many nested levels"""
    for i in range(10):
        if i > 0:
            for j in range(10):
                if j > 0:
                    for k in range(10):
                        if k > 0:
                            print(i * j * k)


def long_line_example():
    """Line too long"""
    really_long_variable_name = "This is a really long string that goes on and on and on and probably exceeds the recommended line length of 79 or 88 characters depending on your linter configuration"
    return really_long_variable_name


def missing_docstring_params(x, y, z):
    """This docstring doesn't document the parameters or return value"""
    return x + y + z


def     tabs_and_spaces_mix():
	"""Mixed tabs and spaces for indentation"""
	x = 10  # This line uses spaces
	y = 20  # This line uses tab
        z = 30  # This line uses spaces
	return x + y + z


# Multiple imports on same line
import math, statistics, collections


# Wildcard import
from os import *


def trailing_whitespace():    
    """This function has trailing whitespace"""    
    return "done"     


def multiple_statements(): x = 1; y = 2; return x + y  # Multiple statements on one line


# No space after comma
numbers=[1,2,3,4,5,6,7,8,9,10]


def wrong_quotes():
    """Inconsistent quote usage"""
    a = "double quotes"
    b = 'single quotes'
    c = "mixed quotes'
    return a + b


def shadow_builtins():
    """Shadowing built-in names"""
    list = [1, 2, 3]  # Shadowing built-in list
    dict = {"a": 1}   # Shadowing built-in dict
    str = "hello"     # Shadowing built-in str
    sum = 0           # Shadowing built-in sum
    for i in list:
        sum += i
    return sum


def unpythonic_loops():
    """Non-pythonic loop patterns"""
    items = ['a', 'b', 'c', 'd']
    # Using range(len()) instead of enumerate
    for i in range(len(items)):
        print(f"{i}: {items[i]}")
    
    # Manual index tracking
    index = 0
    for item in items:
        print(f"{index}: {item}")
        index += 1
    
    # While loop that should be a for loop
    i = 0
    while i < len(items):
        print(items[i])
        i += 1


def dangerous_eval():
    """Using eval and exec - security risk"""
    user_input = "2 + 2"
    result = eval(user_input)  # Dangerous!
    
    code = "print('hello')"
    exec(code)  # Also dangerous!
    
    # Using eval for dict creation
    dict_str = "{'a': 1, 'b': 2}"
    my_dict = eval(dict_str)  # Should use json.loads or ast.literal_eval
    
    return result


def bad_comprehensions():
    """Overly complex or poorly written comprehensions"""
    # Nested comprehension that's hard to read
    matrix = [[i*j for j in range(10) if j > 5] for i in range(10) if i % 2 == 0]
    
    # Side effects in comprehension
    results = []
    [results.append(x*2) for x in range(10)]  # Using comprehension for side effects
    
    # Should use generator expression
    sum_of_squares = sum([x**2 for x in range(1000000)])  # Creates full list in memory
    
    return matrix


def magic_numbers_everywhere():
    """Magic numbers without constants"""
    def calculate_price(quantity):
        if quantity > 100:  # What does 100 mean?
            return quantity * 9.99  # What's 9.99?
        elif quantity > 50:  # What's 50?
            return quantity * 12.99  # What's 12.99?
        else:
            return quantity * 15.99  # What's 15.99?
    
    def check_status(code):
        if code == 200:  # Should use constant
            return "OK"
        elif code == 404:  # Should use constant
            return "Not Found"
        elif code == 500:  # Should use constant
            return "Server Error"
    
    return calculate_price(75)


def poor_class_design():
    """Class with poor design patterns"""
    class DataManager:
        def __init__(self):
            self.data = []
            self._private = []  # Single underscore
            self.__secret = []  # Name mangling
            self.Public = []    # Capital letter
        
        def processData(self):  # camelCase in Python
            pass
        
        def Process_Data(self):  # Inconsistent naming
            pass
        
        def PROCESS_DATA(self):  # All caps for method
            pass
        
        # Property without setter
        @property
        def items(self):
            return self.data
        
        # Modifying mutable attribute directly
        def add_item_wrong(self, item):
            self.items.append(item)  # Modifying property directly


def assertion_misuse():
    """Using assertions for validation"""
    def divide(a, b):
        assert b != 0, "Cannot divide by zero"  # Assertions can be disabled!
        return a / b
    
    def validate_age(age):
        assert age >= 0, "Age must be positive"  # Should use proper validation
        assert isinstance(age, int), "Age must be integer"
        return True


def circular_import_risk():
    """Function that could cause circular imports"""
    # Importing inside function (sometimes necessary but often bad)
    def get_user_data():
        from user_service import UserService  # Import inside function
        return UserService().get_data()
    
    def get_api_data():
        import api_handler  # Another internal import
        return api_handler.fetch()


def inefficient_operations():
    """Inefficient string and list operations"""
    # String concatenation in loop
    def build_string(items):
        result = ""
        for item in items:
            result += str(item)  # Creates new string each time
        return result
    
    # Repeated list concatenation
    def build_list(items):
        result = []
        for item in items:
            result = result + [item]  # Creates new list each time
        return result
    
    # Checking membership in list instead of set
    def check_items(items, lookups):
        found = []
        for lookup in lookups:
            if lookup in items:  # O(n) operation if items is list
                found.append(lookup)
        return found


def  more_spacing_issues(  ):
    """Functions with weird spacing"""
    x  =  10
    y=20
    z =30
    return  x+  y  +z


class   BadlyFormattedClass  (  object  ):
    """Class with bad formatting"""
    def    __init__  (  self  ,  value  ):
        self.value=value
    def  get_value  ( self ):
        return  self.value


def assignment_in_condition():
    """Assignment in conditions - confusing"""
    x = 10
    # This is valid Python but confusing
    if (y := x * 2) > 15:
        return y
    # Multiple assignments
    if (a := 5) and (b := 10) and (c := a + b):
        return c


def redundant_code():
    """Redundant and unnecessary code"""
    # Redundant parentheses
    result = ((10 + 20))
    # Redundant comparison
    if result == True:
        x = 10
    else:
        x = 10  # Same assignment in both branches
    
    # Unnecessary else after return
    if x > 5:
        return True
    else:
        return False  # Could just be: return x > 5
    
    # Redundant variable
    temp = x * 2
    return temp  # Could just return x * 2


def bad_boolean_logic():
    """Poor boolean logic patterns"""
    x = True
    y = False
    
    # Comparing boolean to True/False
    if x == True and y == False:
        pass
    
    # Not using De Morgan's laws
    if not (x and y):  # Could be: if not x or not y
        pass
    
    # Complex boolean that could be simplified
    if x == True or x == False:  # This is always True!
        pass
    
    # Redundant boolean conversion
    return bool(x == True)  # Just return x


def inconsistent_naming():
    """Mix of naming conventions"""
    myVariable = 10  # camelCase
    my_other_variable = 20  # snake_case
    MyThirdVariable = 30  # PascalCase
    REGULAR_VARIABLE = 40  # Should be constant only
    
    def myFunction():  # camelCase function
        pass
    
    def MyOtherFunction():  # PascalCase function
        pass
    
    class my_class:  # lowercase class
        pass
    
    class myOtherClass:  # camelCase class
        pass


def hardcoded_values():
    """Hardcoded values everywhere"""
    # Hardcoded file paths
    with open("/Users/john/Documents/data.txt") as f:
        data = f.read()
    
    # Hardcoded URLs
    api_url = "http://localhost:3000/api/v1/users"
    
    # Hardcoded credentials (NEVER DO THIS!)
    username = "admin"
    password = "password123"
    
    # Hardcoded configuration
    max_retries = 3
    timeout = 30
    buffer_size = 1024


def no_error_messages():
    """Poor error handling without messages"""
    try:
        # Some operation
        result = 10 / 0
    except ZeroDivisionError:
        pass  # No error message or logging
    
    try:
        # Another operation
        data = json.loads("{}")
    except:
        return None  # Returning None without explanation


def deep_nesting_horror():
    """Deeply nested code"""
    data = {"a": {"b": {"c": {"d": {"e": {"f": 10}}}}}}
    
    # Accessing deeply nested data without safety
    result = data["a"]["b"]["c"]["d"]["e"]["f"]
    
    # Deeply nested if statements
    if data:
        if "a" in data:
            if data["a"]:
                if "b" in data["a"]:
                    if data["a"]["b"]:
                        if "c" in data["a"]["b"]:
                            return data["a"]["b"]["c"]


def sql_injection_risk(user_input):
    """SQL injection vulnerability"""
    # NEVER DO THIS - SQL injection risk
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    # Should use parameterized queries
    return query


def path_traversal_risk(filename):
    """Path traversal vulnerability"""
    # NEVER DO THIS - path traversal risk
    with open("data/" + filename) as f:
        return f.read()
    # Should validate/sanitize filename


def weak_random():
    """Using weak random for security"""
    # Don't use random for security purposes
    token = random.randint(1000, 9999)
    # Should use secrets module
    return token


def resource_leaks():
    """Not properly closing resources"""
    # File not closed properly
    f = open("data.txt")
    data = f.read()
    # Missing f.close()
    
    # Not using context manager
    file = open("output.txt", "w")
    file.write("data")
    # Missing file.close()


def type_confusion():
    """Type confusion and coercion issues"""
    # Implicit type conversion
    result = "5" + str(10)  # String concatenation, not addition
    
    # Comparing different types
    if "10" > 5:  # Comparing string to int
        pass
    
    # Using is for value comparison
    if x is 10:  # Should use == for value comparison
        pass


def list_modification_while_iterating():
    """Modifying list while iterating"""
    items = [1, 2, 3, 4, 5]
    # Don't modify list while iterating
    for item in items:
        if item % 2 == 0:
            items.remove(item)  # Dangerous!
    return items


def print_debugging():
    """Using print for debugging instead of logging"""
    def process_data(data):
        print("Starting process")  # Should use logging
        print(f"Data: {data}")     # Should use logging
        result = data * 2
        print(f"Result: {result}") # Should use logging
        return result


def single_letter_names():
    """Single letter variable names"""
    def f(x, y, z):
        a = x + y
        b = y + z
        c = a * b
        d = c / 2
        e = d ** 2
        return e


def commented_out_code():
    """Leaving commented out code"""
    def calculate():
        result = 10
        # result = 20  # Old implementation
        # result = result * 2
        # print(result)
        # return result + 10
        return result * 3


# Missing if __name__ == "__main__" guard
print("This will run when imported!")
result = calculate_stuff(1, 2, 3)
print(f"Result: {result}")


# Class at module level doing work
class AutoExecute:
    print("This runs at import time!")  # Side effect at import
    data = [1, 2, 3]
    processed = [x * 2 for x in data]
    print(f"Processed: {processed}")


# Multiple classes in one file with inconsistent style
class  FirstClass :pass
class second_class: pass
class THIRD_CLASS:pass


# Bare raise without context
def bare_raise():
    try:
        raise
    except:
        pass


# Using sys.exit in library code
def emergency_exit():
    if some_condition:
        sys.exit(1)  # Should raise exception instead


# Overly broad imports at end of file (should be at top)
from datetime import *
from collections import *


# No trailing newline


# Too many blank lines above




def function_with_no_return_type_hint(param1, param2):
    """Missing type hints completely"""
    return param1 + param2


def function_with_partial_hints(x: int, y):
    """Partial type hints - inconsistent"""
    return x + y


class   VeryBadClass(object):
    """Old-style class declaration"""
    
    def __init__(self):
        # Public attributes that should be private
        self.internal_state = []
        self.temp_data = {}
        self.cache = None
    
    def __str__(self):
        # Not returning string from __str__
        print("This is wrong!")
    
    def __repr__(self):
        # Returning different type from __repr__
        return 123


def dangerous_default_mutable(data={}):
    """Another mutable default argument"""
    data['count'] = data.get('count', 0) + 1
    return data


def wrong_indentation_levels():
 """Inconsistent indentation"""
 x = 10
  y = 20  # Extra space
 z = 30
    return x + y + z  # Too many spaces


# Using print instead of proper returns
def calculate_value(x, y):
    result = x * y
    print(result)  # Should return, not print


# Pointless string statements
def pointless_strings():
    "This string does nothing"
    x = 10
    'Another pointless string'
    """Even a docstring in the middle"""
    return x


# Using eval for math
def unsafe_math(expression):
    return eval(expression)  # NEVER do this!


# Inconsistent indentation with tabs
def mixed_indents():
	x = 10  # tab
        y = 20  # spaces
	z = 30  # tab
        return x + y + z  # spaces


# Chained comparisons done wrong
def bad_comparisons(x, y, z):
    # Should use chained comparison
    if x < y and y < z:
        return True
    # Wrong operator precedence assumption
    if x & y == 0:  # Probably meant (x & y) == 0
        return False


# Not using context managers
def manual_file_handling():
    f = open('test.txt', 'w')
    f.write('data')
    f.close()  # What if write fails?


# Empty except blocks everywhere
def suppressing_all_errors():
    try:
        dangerous_operation()
    except:
        pass
    
    try:
        another_operation()
    except:
        pass
    
    try:
        final_operation()
    except:
        pass


# Line continuation issues
def long_function_signature(parameter_one, parameter_two, parameter_three, \
                          parameter_four, parameter_five, parameter_six):
    return sum([parameter_one, parameter_two, parameter_three, \
               parameter_four, parameter_five, parameter_six])


# Comparison with None using ==
if some_value == None:  # Should use 'is None'
    pass


# Empty class definitions
class EmptyClass:
    pass

class AnotherEmpty:
    ...

class YetAnotherEmpty:
    '''Empty'''


# Duplicate function names
def duplicate_name():
    return 1

def duplicate_name():  # Overwrites previous
    return 2


# Using id as variable name
id = 12345  # Shadows builtin
type = "string"  # Shadows builtin
help = "no help"  # Shadows builtin


# Semicolons everywhere
x = 10;
y = 20;
z = x + y;


# Wrong docstring placement
def wrong_docstring():
    x = 10
    """This docstring is in the wrong place"""
    return x


# Using lists for membership testing
def slow_membership_test(item):
    valid_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Should be set
    return item in valid_items


# Redefining builtins in comprehension
data = [sum for sum in range(10)]  # sum is builtin!


# Complex lambda
complex_lambda = lambda x, y, z: x + y if x > 0 else y + z if y > 0 else z


# Using dict() instead of {}
empty_dict = dict()  # Should use {}
empty_list = list()  # Should use []


# Concatenating with + in a loop
def inefficient_concat(items):
    s = ""
    for item in items:
        s = s + str(item) + " "  # Should use join
    return s


# Class with everything public
class NoEncapsulation:
    def __init__(self):
        self.private_key = "secret"  # Should be private
        self.internal_state = []     # Should be private
        self.temp_buffer = None      # Should be private


# Using assertions for control flow
def control_with_assert(value):
    assert value > 0  # Assertions can be disabled!
    return value * 2


# Nested ternary operators
result = "positive" if x > 0 else "negative" if x < 0 else "zero"


# Not using enumerate
items = ['a', 'b', 'c']
for i in range(len(items)):
    print(i, items[i])  # Should use enumerate


# Using map/filter with lambda when comprehension is clearer
numbers = [1, 2, 3, 4, 5]
squares = map(lambda x: x**2, numbers)  # Could be comprehension
evens = filter(lambda x: x % 2 == 0, numbers)  # Could be comprehension


# Multiple returns with different types
def inconsistent_return_types(value):
    if value > 0:
        return value  # int
    elif value < 0:
        return str(value)  # str
    else:
        return None  # None


# Using while True without break condition at top
def infinite_loop():
    while True:
        x = get_value()
        if x == -1:
            break
        process(x)


# Catching too specific exception when broader would be appropriate
def too_specific_catch():
    try:
        process_data()
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
    except OSError:
        pass
    # Could catch OSError which covers both FileNotFoundError and PermissionError


# Overuse of single underscore
class _InternalClass:
    def __init__(self):
        self._var1 = 1
        self._var2 = 2
        self._var3 = 3
    
    def _method1(self):
        pass
    
    def _method2(self):
        pass


# No space around operators
result=10+20*30/40-50
flag=True&False|True


# Useless pass statements
def useless_pass():
    x = 10
    pass  # Unnecessary
    y = 20
    pass  # Unnecessary
    return x + y
    pass  # Unreachable


# Mixing string formatting styles
def mixed_string_formatting(name, age, city):
    s1 = "Name: %s" % name  # Old style
    s2 = "Age: {}".format(age)  # .format()
    s3 = f"City: {city}"  # f-string
    return s1 + s2 + s3


# Empty if/elif/else blocks
def empty_blocks(x):
    if x > 0:
        pass
    elif x < 0:
        pass  
    else:
        pass


# Using len() for emptiness check
def check_empty(lst):
    if len(lst) == 0:  # Should use 'if not lst:'
        return True
    if len(lst) > 0:   # Should use 'if lst:'
        return False


# Global statement abuse
def modify_globals():
    global x, y, z, a, b, c
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6


# Useless else after loop
def useless_else():
    for i in range(10):
        if i == 5:
            break
    else:
        print("Done")  # This else is confusing


# Deeply nested dictionary access without get()
def unsafe_dict_access(d):
    return d['a']['b']['c']['d']  # What if keys don't exist?


# Using index() without catching ValueError
def unsafe_index(lst, item):
    return lst.index(item)  # Raises ValueError if not found


# Re-importing modules
import os
import sys  
import os  # Duplicate import


# Using __del__ method (often problematic)
class ProblematicClass:
    def __del__(self):
        print("Deleting object")  # __del__ is unpredictable


# Very long variable names
this_is_an_extremely_long_variable_name_that_makes_code_hard_to_read = 10
another_ridiculously_long_name_for_a_simple_variable = 20


# Using copyright and license incorrectly
__copyright__ = "Copyright (c) 2024"  # Missing owner
__license__ = "Licensed"  # Invalid license spec


# Magic methods with wrong signatures  
class WrongMagicMethods:
    def __init__(self, x, y, z):
        pass
    
    def __str__(self, extra):  # __str__ takes no args
        return "string"
    
    def __len__(self, param):  # __len__ takes no args
        return 10


# Using datetime incorrectly
from datetime import datetime
current_time = datetime.now()  # Not timezone aware


# Forgetting to strip() user input
def process_user_input(user_input):
    if user_input == "yes":  # What about "yes " or " yes"?
        return True


# No validation on array indices
def get_element(arr, index):
    return arr[index]  # What if index is out of bounds?


# Using floats for money
def calculate_price(amount):
    tax = amount * 0.08  # Float arithmetic for money!
    return amount + tax


# Returning mutable default values
def get_default_config():
    return []  # Caller might modify this


def get_default_settings():
    return {}  # Caller might modify this


# Not using constants for repeated values
def check_temperature(temp):
    if temp > 100:  # Magic number
        return "too hot"
    elif temp < 32:  # Magic number  
        return "too cold"
    else:
        return "just right"


# Empty docstrings
def empty_docstring():
    """"""
    pass


# Using exec without namespace
exec("x = 10")  # Pollutes local namespace


# Class attributes vs instance attributes confusion
class ConfusedClass:
    items = []  # Shared between all instances!
    
    def add_item(self, item):
        self.items.append(item)  # Modifies class attribute


# No error handling in __enter__/__exit__
class BadContextManager:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Should handle exceptions


# Using range(len()) unnecessarily
for i in range(len(items)):
    process(items[i])  # Should use: for item in items:


# Overly clever code
result = [x for x in (y for y in range(10) if y % 2) if x > 5]


# Not following PEP 8 import order
from third_party import something
import os  # stdlib should come first
from . import local_module
import sys  # stdlib mixed with others


# TODO comments that are years old
# TODO: Fix this - 2019-01-01
# FIXME: Temporary hack - 2018-05-15  
# XXX: Not sure if this works - 2017-12-31


# Using lowercase L and uppercase O as variable names
l = [1, 2, 3]  # Looks like 1
O = 0  # Looks like 0


# Not using super() correctly
class Parent:
    def __init__(self):
        pass

class Child(Parent):
    def __init__(self):
        Parent.__init__(self)  # Should use super()


# Variables that differ by only one character
count = 10
counts = 20  # Easy to confuse
value1 = 30
valuel = 40  # Is that a 1 or l?


# Using is for numbers (implementation detail)
if x is 256:  # Works by accident
    pass
if y is 257:  # Might not work
    pass


# Meaningless variable names
data = get_data()
result = process(data)
output = transform(result)
final = finalize(output)


# Class with only static methods (should be module)
class StaticOnly:
    @staticmethod
    def method1():
        pass
    
    @staticmethod
    def method2():
        pass


# Comparing types with ==
if type(x) == type(y):  # Should use isinstance
    pass


# Using dict.keys() unnecessarily  
for key in my_dict.keys():  # Just use: for key in my_dict:
    pass


# Not using with for threading locks
import threading
lock = threading.Lock()
lock.acquire()
# do something
lock.release()  # What if exception occurs?


# Unnecessary list() calls
my_list = list([1, 2, 3])  # Already a list
numbers = list(range(10))  # Often unnecessary


# Using if/else instead of dict lookup
def get_day_name(day_num):
    if day_num == 1:
        return "Monday"
    elif day_num == 2:
        return "Tuesday"
    elif day_num == 3:
        return "Wednesday"
    elif day_num == 4:
        return "Thursday"
    elif day_num == 5:
        return "Friday"
    elif day_num == 6:
        return "Saturday"
    elif day_num == 7:
        return "Sunday"
    else:
        return "Invalid"


# Not using args/kwargs properly
def bad_function(*args, **kwargs):
    print(args[0])  # What if no args?
    print(kwargs['key'])  # What if no 'key'?


# Modifying sys.path hackily
import sys
sys.path.append('/random/path')  # Bad practice
sys.path.insert(0, '../')  # Even worse


# Using XML parsing insecurely
import xml.etree.ElementTree as ET
def parse_xml(xml_string):
    return ET.fromstring(xml_string)  # Vulnerable to XXE


# Not using Decimal for money
price = 19.99  # Float for money
tax_rate = 0.0825  # More floats
total = price * (1 + tax_rate)  # Precision errors


# Empty functions that should be abstract
class BaseClass:
    def method_to_override(self):
        pass  # Should raise NotImplementedError


# Using pickle insecurely
import pickle
def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)  # Dangerous with untrusted data


# Regex without raw strings
import re
pattern = "\d+\.\d+"  # Should be r"\d+\.\d+"


# Not closing database connections
import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
# Never closed!


# Using shell=True with subprocess
import subprocess
def run_command(cmd):
    subprocess.run(cmd, shell=True)  # Security risk!


# Class with too many responsibilities
class DoEverything:
    def connect_to_database(self):
        pass
    
    def send_email(self):
        pass
    
    def process_payment(self):
        pass
    
    def generate_report(self):
        pass
    
    def update_ui(self):
        pass


# Using __all__ incorrectly
__all__ = ['foo', 'bar', 'baz']  # But these don't exist


# Comparing strings with is
if name is "admin":  # Should use ==
    pass


# Not using pathlib
import os
file_path = os.path.join('dir', 'subdir', 'file.txt')  # Use pathlib


# Catching KeyboardInterrupt
try:
    long_running_operation()
except KeyboardInterrupt:
    pass  # Don't silence Ctrl+C


# Using bare except at module level
try:
    import optional_module
except:
    optional_module = None  # Too broad


# Initializing class attributes in method
class BadInit:
    def __init__(self):
        pass
    
    def setup(self):
        self.data = []  # Should be in __init__
        self.config = {}


# Deep copying when not needed
import copy
def process_list(lst):
    new_list = copy.deepcopy(lst)  # Overkill for simple list
    return new_list


# Not using f-strings (Python 3.6+)
name = "World"
greeting = "Hello, " + name + "!"  # Use f-string
message = "Value: {}".format(42)  # Use f-string


# Using mutable class attributes
class MutableClassAttr:
    default_config = {'debug': False}  # Shared mutable state!


# Sleep in a loop
import time
def wait_for_condition():
    while not condition_met():
        time.sleep(0.1)  # Busy waiting


# Not using itertools
def get_combinations(lst):
    result = []
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            result.append((lst[i], lst[j]))
    return result  # Use itertools.combinations


# HTTP requests without timeout
import requests
response = requests.get('http://example.com')  # No timeout!


# Using eval to parse JSON
json_string = '{"key": "value"}'
data = eval(json_string)  # Use json.loads!


# Float equality comparison
if 0.1 + 0.2 == 0.3:  # This is False!
    print("Equal")


# Not using generators for large data
def get_squares(n):
    return [x**2 for x in range(n)]  # Creates full list


# Using print for debugging in production
def production_function():
    print("Debug: entering function")  # Use logging!
    result = complex_calculation()
    print(f"Debug: result = {result}")
    return result


# Shared mutable default across function calls
def add_to_list(item, target_list=[]):
    target_list.append(item)
    return target_list


# Not handling timezone properly
from datetime import datetime
now = datetime.now()  # Naive datetime


# Using __file__ incorrectly
current_dir = __file__  # This is the file, not directory


# Forgetting to encode/decode properly
def write_text(text):
    with open('file.txt', 'wb') as f:
        f.write(text)  # text is str, needs bytes


# Class method that should be static
class Example:
    def utility_method(self):
        return 42  # Doesn't use self


# Not using properties
class NoProperties:
    def get_value(self):
        return self._value
    
    def set_value(self, value):
        self._value = value


# Circular imports at module level
# from module_b import something  # If module_b imports from here


# Using id() for comparison
if id(x) == id(y):  # Should use 'is'
    pass


# Not using builtin functions
def my_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total  # Use builtin sum()


# Unnecessary parentheses everywhere
if ((x > 5) and (y < 10)):
    return ((x + y) * (2))


# Using vars() to access attributes
obj_vars = vars(obj)
value = obj_vars['attribute']  # Use getattr


# Not caching expensive operations
def expensive_calculation(n):
    # Recalculates every time
    return sum(i**2 for i in range(n))


# Using list as queue
queue = []
queue.append(item)  # O(1)
first = queue.pop(0)  # O(n) - use collections.deque


# Not validating input types
def divide(a, b):
    return a / b  # What if b is 0? What if they're not numbers?


# Overusing try/except
def overly_defensive():
    try:
        x = 10
    except:
        x = 0
    
    try:
        y = x * 2
    except:
        y = 0
    
    try:
        return x + y
    except:
        return 0


# Empty modules that shouldn't exist
# This module does nothing useful


# Using Python 2 style code
print "Hello"  # Missing parentheses
xrange(10)  # Should be range


# Not following naming conventions for constants
max_size = 100  # Should be MAX_SIZE
default_timeout = 30  # Should be DEFAULT_TIMEOUT


# Function doing too many things
def do_everything(data):
    # Validate
    if not data:
        return None
    
    # Process
    processed = []
    for item in data:
        processed.append(item.upper())
    
    # Save to file
    with open('output.txt', 'w') as f:
        f.write(str(processed))
    
    # Send email
    send_email("Done processing")
    
    # Update database
    db.update(processed)
    
    # Return
    return processed


# Missing space after comma in function calls
print("hello","world",sep=",",end="\n")
function(arg1,arg2,arg3,keyword=value)


# Wrong quotes in docstring
def wrong_quotes_doc():
    'Using single quotes for docstring'  # Should use triple quotes
    pass


# No blank line at end of file
