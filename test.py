#def add(n1,n2):
#	return n1 + n2
#
#def divide(n1,n2):
#	return n1 / n2

#def outer_function():3	print('im outer')

#	def nested_function():
#		print("im inner")

#	return nested_function

#iiner = outer_function()
#iiner()

from functools import wraps
def my_decorator(func):
	@wraps(func)
	def wrapper(*args,**kwargs):
		print("some happing before func called")
		result = func(*args,**kwargs)
		print("some happing after the func called")
		return result
	return wrapper


@my_decorator
def add_numbers(a,b):
	return a + b


print(add_numbers.__name__)
print(add_numbers.__doc__)