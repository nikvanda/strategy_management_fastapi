class BaseUserException(Exception):
    pass


class UserNotExists(BaseUserException):
    def __init__(self, username: str, message=None, errors=None):
        message = f'User {username} does not exist.'

        super().__init__(message)
        self.errors = errors

class IncorrectPasswordError(BaseUserException):
    def __init__(self, message=None, errors=None):
        message = 'Incorrect password'
        super().__init__(message)

        self.errors = errors

class UsernameIsDoubleError(BaseUserException):
    def __init__(self, message=None, errors=None):
        message = "Username has already taken."
        super().__init__(message)

        self.errors = errors

class JWTError(BaseUserException):
    def __init__(self, message, errors=None):
        super().__init__(message)

        self.errors = errors
