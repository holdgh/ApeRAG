import poplib
import email6
import os
import tempfile
from bs4 import BeautifulSoup
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.tasks.index import add_index_for_document
from kubechat.tasks.local_directory_task import cron_collection_metadata
from readers.Readers import DEFAULT_FILE_READER_CLS

import logging
logger = logging.getLogger(__name__)

def connect_to_pop3_server(pop_server, port, email_address, email_password):
    pop_conn = poplib.POP3_SSL(pop_server, port)
    pop_conn.user(email_address)
    pop_conn.pass_(email_password)
    return pop_conn

def extract_plain_text_from_email_body(body):
    soup = BeautifulSoup(body, "html.parser")
    for style_tag in soup.find_all('style'):
        style_tag.decompose()
    for script_tag in soup.find_all('meta'):
        script_tag.decompose()
    for meta_tag in soup.find_all('html'):
        meta_tag.decompose()
    return soup.get_text()
def download_email_body_to_temp_file(pop_conn, email_index):
    _, message_lines, _ = pop_conn.retr(email_index)
    message_content = b'\r\n'.join(message_lines).decode('utf-8')
    message = email.message_from_string(message_content)
    body = ""
    for part in message.walk():
        if part.get_content_maintype() == 'text':
            body += part.get_payload()
    plain_text = extract_plain_text_from_email_body(body)
    print(plain_text)
    if plain_text:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(plain_text.encode('utf-8'))
        temp_file.close()
        return temp_file.name
    return None

def scanning_email_add_index(pop_server, port, email_address, email_password, collection):
    collection.status = CollectionStatus.INACTIVE
    collection.save()
    pop_conn = connect_to_pop3_server(pop_server, port, email_address, email_password)

    try:
        num_messages = len(pop_conn.list()[1])
        for i in range(num_messages):
            # 获取邮件正文并下载到本地临时文件中
            temp_file_path = download_email_body_to_temp_file(pop_conn, i+1)
            if temp_file_path:
                document_instance = Document(
                    user=collection.user,
                    name=f"email_body_{i+1}.txt",
                    status=DocumentStatus.PENDING,
                    size=os.path.getsize(temp_file_path),
                    collection=collection,
                    metadata=time.ctime(os.path.getmtime(temp_file_path))
                )
                document_instance.save()
                # 在后台任务中为文档添加索引
                add_index_for_document.delay(document_instance.id, temp_file_path)
    except Exception as e:
        logger.error(f"scanning_email_add_index() error {e}")

    collection.status = CollectionStatus.ACTIVE
    collection.save()

    cron_collection_metadata.append({"user": collection.user, "id": collection.id})