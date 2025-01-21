class LLMOutputNotValidJSONError(Exception):
    def __init__(self, message):
        super().__init__(message)

class LLMRepeatJSONTwiceError(Exception):
    def __init__(self, message):
        super().__init__(message)

class LLMDotMessageError(Exception):
    def __init__(self, message):
        super().__init__(message)

class LLMRepetitiveResponseError(Exception):
    def __init__(self, message):
        super().__init__(message)

class LLMEndConversationError(Exception):
    def __init__(self, message):
        super().__init__(message)

class ExitWithCodeException(Exception):
    def __init__(self, return_code):
        super().__init__(f'Exiting with return code: {return_code}')
        self.return_code = return_code
