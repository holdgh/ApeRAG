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
    ftp.cwd(path)  # Switch to the specified path
    files = ftp.nlst()  # Get the list of files in the current path
    temp_files = []
    for file in files:
        file_path = os.path.join(path, file)  # Build the full file path
        try:
            ftp.cwd(file_path)  # Try to switch to the specified path (if it's a folder)
            deal_the_path(ftp, collection, file_path)  # Recursively process the subdirectory
        except error_perm:  # If it's not a folder, process the file
            if os.path.splitext(file)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
                print(file_path)
                temp_file = download_file(ftp, file_path)  # Download the file
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
        logger.error(f"Temporary file deleted: {temp_file}")


def scanning_dir_add_index_from_ftp(dir, ftp_host, ftp_user, ftp_password, collection):
    collection.status = CollectionStatus.INACTIVE
    collection.save()

    # Connect to the FTP server
    try:
        ftp = FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)
    except Exception as e:
        logger.error(f"scanning_dir_add_index_from_ftp() ftp connect error {e}")

    try:
        deal_the_path(ftp, collection, dir)
    except Exception as e:
        logger.error(f"scanning_dir_add_index() error {e}")

    # Close the FTP connection
    ftp.quit()
    # Update the collection status
    collection.status = CollectionStatus.ACTIVE
    collection.save()

    # Add the collection to the cron job list
    cron_collection_metadata.append({"user": collection.user, "id": collection.id})
