import os

CACHE_PATH = '.cache'

if os.name == 'nt':
    CTAG_PATH = './ext_tools/ctag/ctags.exe'
else:
    CTAG_PATH = './ext_tools/ctags_linux/ctags'

MOJO_PATH = './ext_tools/mojo.jar'
DEPENDS_PATH = './ext_tools/depends-1.0.0.jar'
DEPENDS_PUB_PATH = './ext_tools/depends-0.9.7.jar'

INTERMIDIATE_INFO_PATH = './extracted_info'
USE_NLTK = True
SUPPORTED_FILE_TYPES = (
    '.c', '.h', # c
    '.cpp', '.hpp', '.cxx', '.hxx', '.cc', # cpp
    '.cpp', '.hpp', '.cxx', '.hxx', # c#
    '.java', # java
    '.py',
)
DEFAULT_STOP_WORD_LIST = './stopwords/stopwords.txt'

DISABLE_CACHE = False

DEPENDS_TIMEOUT_SEC = 120000