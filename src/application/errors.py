from typing import List

from starlette import status


class BaseError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "An unknown error occurred."

    def __str__(self) -> str:
        return self.message


class BaseErrorGroup(ExceptionGroup[BaseError]):
    def __init__(self, errors: List[BaseError], **_) -> None:
        super().__init__("Some errors occurred", errors)
