from threading import RLock
from kfconf import cfg


class Singleton(object):
	"""
	A simple example implementing the singleton design pattern in
	python
	"""
	# we need two class attributes (which translate to static attributes in java)
	__lock = RLock() # a lock for thread safety
	__instance = None # and to remember the one instance

	# first of all: make pythons usual way of creating objects
	# unusable because we cannot just hide them as one would in java 	# or C++
	def __new__(cls, *args, **kwargs):
		pass

	def __init__(self):
		pass

	@classmethod
	def getInstance(cls, *args, **kwargs):
		"""
		The famous getInstance method which resturns the one instance of 	our
		class.
		params:
		cls - reference to the class
		*args - the tuple of arguments paassed by position
		**kwargs - the dictionary of arguments passed by keyword
		"""
		#enter critical section
		cls.__lock.acquire()
		try:
			if cls.__instance is None:
				# use the superclasses __new__ for creation
				cls.__instance = object.__new__(cls, *args, **kwargs)

				# place initialisation code (everything which
				# would usually happen in __init__) here
				# cls.__instance.SomeInt = 1

		finally:
			# leave critical section
			cls.__lock.release()

		return cls.__instance
