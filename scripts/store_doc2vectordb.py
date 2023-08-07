import os
from services.kubeblocks.text2kbcli import inflate_doc_to_database, list_specific_end_files
from config import settings
import logging

logger = logging.getLogger(__name__)

# store kbcli document to vector db
if __name__ == "__main__":
    kbcli_md_path = settings.KBCLIDOC_DIR
    kbcli_md_list = list_specific_end_files(directory=kbcli_md_path, end=".md")
    if len(kbcli_md_list) == 0:
        logger.error("no local kbcli doc was detected")
    success = inflate_doc_to_database(file_paths=kbcli_md_list, collection_id=settings.KBCLIDOC_COLLECTION_NAME)
    if success is False:
        logger.error("inserting kbcli doc to vector db failed")
