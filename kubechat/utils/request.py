from http import HTTPStatus

from kubechat.utils.db import PagedResult


def get_user(request):
    return request.META.get("X-USER-ID", "")


def success(data, pr: PagedResult = None):
    response = {
        "code": "%d" % HTTPStatus.OK,
        "data": data,
    }
    if pr is not None and pr.count > 0:
        response["page_number"] = pr.page_number
        response["page_size"] = pr.page_size
        response["count"] = pr.count
    return response


def fail(code, message):
    return {
        "code": "%d" % code,
        "message": message,
    }
