"Print fonts.css with each url(et-book/...woff) replaced by a data URI: python embed_fonts.py fonts.css EXT_DIR"
import base64, re, sys
from pathlib import Path
css, ext = Path(sys.argv[1]).read_text(), Path(sys.argv[2])
def data(m):
    return 'url("data:font/woff;base64,' + base64.b64encode((ext / m.group(1)).read_bytes()).decode() + '")'
print(re.sub(r'url\("(et-book/[^"]+\.woff)"\)', data, css))
