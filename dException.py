
class dException(StandardError):
	"""
	Base class in the framework for passing exceptions.
	"""
	pass


class BeginningOfFileException(dException):
	pass


class EndOfFileException(dException):
	pass


class NoRecordsException(dException):
	pass


class QueryException(dException):
	pass


class BusinessRuleViolation(dException):
	pass


class MissingPKException(dException):
	pass
