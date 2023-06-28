from http import HTTPStatus


def get_user(request):
    return request.META.get("X-USER-ID", "")


def success(data):
    return {
        "code": HTTPStatus.OK,
        "data": data,
    }


def fail(code, message):
    return {
        "code": code,
        "message": message,
    }

