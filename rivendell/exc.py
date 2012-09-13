class Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class LogExists(Error):
    """Log already exists"""
    pass

class CartError(Error):
    """Cart is invalid"""
    pass

class CartNotInDatabase(CartError):
    '''Cart does not exist in database'''
    pass

class CutNotOnDisk(CartError):
    '''Cart does not exist on disk storage'''
    pass

class CutInvalid(CartError):
    '''Cut is not valid (bad file format?)'''
    pass

class ToolMissing(Error):
    '''Some external tool or command is missing'''
    pass
