class ErrorWithCode(Exception):
    errors = []

    def __init__(self, errors=None, error=None):
        Exception.__init__(self)
        self.errors = []
        if type(errors) is list:
            self.errors = errors
        if error:
            self.errors.append(error)

    @staticmethod
    def from_error(code:str, message:str="", source:str="", details:dict={}):
        return ErrorWithCode(error={
            "code": code,
            "source": source,
            "message": message,
            "details": details
        })
