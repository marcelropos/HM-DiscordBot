from core.error.handler.bad_argument_handler import BadArgumentHandler


class ValueErrorHandler(BadArgumentHandler):
    error: ValueError

    @staticmethod
    def handles_type():
        return ValueError
