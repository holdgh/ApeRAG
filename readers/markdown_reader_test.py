import tempfile
from pathlib import Path

content = """
hello

# Level 1 Title 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

## Level 2 Title 1

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae.

## Level 2 Title 2

Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.

### Level 3 Title 1

Nullam id semper nunc.

### Level 3 Title 2

Sed euismod, nunc id aliquam tincidunt, mauris nunc tincidunt urna.

#### Level 4 Title 1
#### Level 4 Title 2
#### Level 4 Title 3
#### Level 4 Title 4

Id lacinia nisl nunc id justo.

#### Level 4 Title 5

Suspendisse potenti.

##### Level 5 Title 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

##### Level 5 Title 2

Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae.


##### Level 5 Title 3

# Level 1 Title 2

## Level 2 Title 3

hello

##### Level 5 Title 4

hi

"""
f = tempfile.NamedTemporaryFile(delete=False)
f.write(content.encode("utf-8"))
f.close()

from readers.markdown_reader import MarkdownReader
# from llama_index.readers.file.markdown_reader import MarkdownReader
docs = MarkdownReader().load_data(Path(f.name))
for doc in docs:
    print(doc.text)