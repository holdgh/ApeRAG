import io
import logging
import os
import uuid
import zipfile
from http import HTTPStatus
from pathlib import Path

from asgiref.sync import sync_to_async
from django.http import HttpResponse
from ninja import NinjaAPI, UploadedFile, File

from config import settings
from kubechat.auth.validator import GlobalHTTPAuth
from kubechat.models import ssl_temp_file_path, VerifyWay, Chat, DocumentStatus, ChatStatus
from kubechat.utils.db import new_db_client
from kubechat.utils.request import fail, success, get_user
from kubechat.utils.utils import fix_path_name
from kubechat.views import ConnectionInfo

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", auth=GlobalHTTPAuth(), urls_namespace="deprecated", docs_url=None)


@api.post("/collections/ca/upload")
def ssl_file_upload(request, file: UploadedFile = File(...)):
    file_name = uuid.uuid4().hex
    _, file_extension = os.path.splitext(file.name)
    print(file_extension)
    if file_extension not in [".pem", ".key", ".crt", ".csr"]:
        return fail(HTTPStatus.NOT_FOUND, "file extension not found")

    if not os.path.exists(ssl_temp_file_path("")):
        os.makedirs(ssl_temp_file_path(""))

    with open(ssl_temp_file_path(file_name + file_extension), "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return success(file_name + file_extension)


@api.post("/collections/test_connection")
def connection_test(request, connection: ConnectionInfo):
    verify = connection.verify != VerifyWay.PREFERRED
    host = connection.host

    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_db_client(dict(connection))
    if client is None:
        return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")

    if not client.connect(
            False,
            ssl_temp_file_path(connection.ca_cert),
            ssl_temp_file_path(connection.client_key),
            ssl_temp_file_path(connection.client_cert),
    ):
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "can not connect")

    return success("successfully connected")


@api.get("/code/codegenerate/download/{chat_id}")
async def download_code(request, chat_id):
    user = get_user(request)
    chat = await Chat.objects.exclude(status=DocumentStatus.DELETED).aget(
        user=user, pk=chat_id
    )

    @sync_to_async
    def get_collection():
        return chat.collection

    collection = await get_collection()
    if chat.user != user:
        return success("No access to the file")
    if chat.status != ChatStatus.UPLOADED:
        return success("The file is not ready for download")
    base_dir = Path(settings.CODE_STORAGE_DIR)
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    workspace = base_dir / "generated-code" / fix_path_name(user) / fix_path_name(
        collection.title + str(chat_id)) / "workspace"

    for root, dirs, files in os.walk(str(workspace)):
        for file in files:
            zip.write(os.path.join(root, file), arcname=file)
    zip.close()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue())
    response['Content-Disposition'] = f"attachment; filename=\"{collection.title}.zip\""
    response['Content-Type'] = 'application/zip'
    return response
