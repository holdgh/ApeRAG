import poplib
import os
import tempfile
import time
from email6 import message_from_bytes
from email6.header import decode_header
from bs4 import BeautifulSoup
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.tasks.index import add_index_for_document

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
    message_content = b'\r\n'.join(message_lines)
    message = message_from_bytes(message_content)
    body = ""
    for part in message.walk():
        if part.get_content_maintype() == 'text':
            body += part.get_payload(decode=True).decode('utf-8')
    subject = message.get("Subject", "")
    decoded_subject = ""
    for part, charset in decode_header(subject):
        if charset is not None:
            decoded_part = part.decode(charset)
            decoded_subject += decoded_part
        else:
            decoded_subject += part
    plain_text = extract_plain_text_from_email_body(body)
    if plain_text:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt",)
        temp_file.write(plain_text.encode('utf-8'))
        temp_file.close()
        return temp_file.name, decoded_subject
    return None


def scanning_email_add_index(pop_server, port, email_address, email_password, collection):
    collection.status = CollectionStatus.INACTIVE
    collection.save()
    pop_conn = connect_to_pop3_server(pop_server, port, email_address, email_password)

    try:
        num_messages = len(pop_conn.list()[1])
        for i in range(num_messages):
            temp_file_path, decoded_subject = download_email_body_to_temp_file(pop_conn, i + 1)
            if temp_file_path:
                document_instance = Document(
                    user=collection.user,
                    name=decoded_subject + f".txt",
                    status=DocumentStatus.PENDING,
                    size=os.path.getsize(temp_file_path),
                    collection=collection,
                    metadata=time.ctime(os.path.getmtime(temp_file_path))
                )
                document_instance.save()
                add_index_for_document.delay(document_instance.id, temp_file_path)
    except Exception as e:
        logger.error(f"scanning_email_add_index() error {e}")

    collection.status = CollectionStatus.ACTIVE
    collection.save()
