from fastapi import HTTPException, status


class AuthError(HTTPException):
    def __init__(self, detail: str = "Требуется аутентификация"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Недостаточно прав"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Объект не найден"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Конфликт данных"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
