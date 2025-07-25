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
