import glob
import logging
import os
import tempfile
import time

from ftplib import FTP, error_perm

from kubechat.tasks.index import add_index_for_document
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.tasks.local_directory_task import cron_collection_metadata
from readers.Readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


# download the file with the remote_path
def download_file(ftp, remote_path):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        ftp.retrbinary('RETR ' + remote_path, temp_file.write)
        temp_file_path = temp_file.name
    return temp_file_path


def deal_the_path(ftp, collection, path='/'):
    ftp.cwd(path)  # 切换到指定路径
    files = ftp.nlst()  # 获取当前路径下的文件列表
    print(path)
    temp_files = []
    for file in files:
        file_path = os.path.join(path, file)  # 构建文件的完整路径
        try:
            ftp.cwd(file_path)  # 尝试切换到指定路径
            deal_the_path(ftp, collection, file_path)
        except error_perm:  # 不是文件夹，就处理文件
            print(file_path)
            temp_file = download_file(ftp, file_path)
            temp_files.append(temp_file)
            file_stat = os.stat(file_path)
            document_instance = Document(
                user=collection.user,
                name=file_path,
                status=DocumentStatus.PENDING,
                size=file_stat.st_size,
                collection=collection,
                metadata=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stat.st_mtime))
            )
            document_instance.save()

            add_index_for_document.delay(document_instance.id)

    for temp_file in temp_files:
        os.remove(temp_file)
        print(f"已删除临时文件: {temp_file}")


def scanning_dir_add_index_from_ftp(dir: str, collection):
    ftp_host = collection.ftp_host
    ftp_user = collection.ftp_user
    ftp_password = collection.ftp_password

    collection.status = CollectionStatus.INACTIVE
    collection.save()

    # 连接到FTP服务器
    try:
        ftp = FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)
    except Exception as e:
        logger.error(f"scanning_dir_add_index_from_ftp() ftp connect error {e}")

    try:
        deal_the_path(ftp, collection, dir)
    except Exception as e:
        logger.error(f"scanning_dir_add_index() error {e}")

    # 关闭FTP连接
    ftp.quit()
    # add the
    collection.status = CollectionStatus.ACTIVE
    collection.save()

    # add the collection to cron job list
    cron_collection_metadata.append({"user": collection.user, "id": collection.id})
