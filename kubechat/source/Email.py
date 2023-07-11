import logging
import os
import poplib
import tempfile
from typing import Dict, Any

from bs4 import BeautifulSoup
from email import message_from_bytes, parser
from email.header import decode_header
import datetime

from kubechat.models import CollectionStatus, Document, DocumentStatus, Collection
from kubechat.source.base import Source

logger = logging.getLogger(__name__)


def download_email_body_to_temp_file(pop_conn, email_index):
    _, message_lines, _ = pop_conn.retr(email_index)
    message_content = b"\r\n".join(message_lines)
    message = message_from_bytes(message_content)
    body = ""
    for part in message.walk():
        if part.get_content_maintype() == "text":
            body += part.get_payload(decode=True).decode("utf-8")
    plain_text = extract_plain_text_from_email_body(body)
    if plain_text:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".txt",
        )
        temp_file.write(plain_text.encode("utf-8"))
        temp_file.close()
        return temp_file.name
    return None


def extract_plain_text_from_email_body(body):
    soup = BeautifulSoup(body, "html.parser")
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    for script_tag in soup.find_all("meta"):
        script_tag.decompose()
    for meta_tag in soup.find_all("html"):
        meta_tag.decompose()
    return soup.get_text()


def decode_msg_header(header):
    value, charset = decode_header(header)[0]
    if charset:
        value = value.decode(charset)
    return value


class EmailSource(Source):

    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.pop_server = ctx["pop_server"]
        self.port = ctx["port"]
        self.email_address = ctx["email_address"]
        self.email_password = ctx["email_password"]
        self.collection = collection
        self.conn = self._connect_to_pop3_server()
        self.email_num = 0

    def _connect_to_pop3_server(self):
        pop_conn = poplib.POP3_SSL(self.pop_server, self.port)
        pop_conn.user(self.email_address)
        pop_conn.pass_(self.email_password)
        return pop_conn

    def scan_documents(self):
        documents = []
        self.email_num = len(self.conn.list()[1])
        try:
            for i in range(self.email_num):
                response, msg_lines, octets = self.conn.retr(i + 1)

                msg_lines_to_str = b"\r\n".join(msg_lines).decode("utf8", "ignore")
                message_object = parser.Parser().parsestr(msg_lines_to_str)

                msg_header = message_object["Subject"]
                decoded_subject = decode_msg_header(msg_header)
                order_and_name = str(i + 1) + '_' + decoded_subject + f".txt"

                msg_date = str(message_object["date"])
                if msg_date.find('(GMT)') != -1 or msg_date.find('(UTC)') != -1:
                    msg_date = msg_date[:-6]

                document = Document(
                    user=self.collection.user,
                    name=order_and_name,
                    status=DocumentStatus.PENDING,
                    size=octets,
                    collection=self.collection,
                    metadata=datetime.datetime.strptime(msg_date, '%a, %d %b %Y %H:%M:%S %z').strftime("%Y-%m-%d "
                                                                                                       "%H:%M:%S"),
                )
                documents.append(document)
        except Exception as e:
            logger.error(f"scan_email_documents {e}")
        return documents

    def prepare_document(self, doc: Document):

        order_and_name = doc.name
        under_line = order_and_name.find('_')
        order = order_and_name[:under_line]
        # name = order_and_name[under_line + 1:]
        # doc.name = name
        temp_file_path = download_email_body_to_temp_file(
            self.conn, order
        )
        return temp_file_path

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        self.conn.quit()
