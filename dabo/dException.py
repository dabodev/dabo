class dException(StandardError):
	"""	Base class in the framework for passing exceptions."""
	

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
	

class FeatureNotImplementedException(dException):
	pass
	

class FeatureNotSupportedException(dException):
	pass


class MissingPKException(dException):
	pass

class ConnectionLostException(dException):
	pass

class FieldNotFoundException(dException):
	pass

class DataBaseException(dException):
	pass

class DBNoAccessException(DataBaseException):
	pass
	
class DBNoDBOnHostException(DataBaseException):
	pass


class DBQueryException(DataBaseException):
	def __init__(self, err, sql):
		self.sql = sql
		self.err_desc = str(err)
		
	def __str__(self):
		return self.err_desc + '\nSQL: ' + self.sql

