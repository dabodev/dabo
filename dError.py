
class dError(StandardError):
    """
    Base class in the framework for passing exceptions.
    """
    pass

    
class BeginningOfFileError(dError):
    pass
    

class EndOfFileError(dError):
    pass
    
    
class NoRecordsError(dError):
    pass
    

class QueryError(dError):
    pass

    
class BusinessRuleViolation(dError):
    pass