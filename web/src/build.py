"""Baut die fertige Ausstellungsseite web/stadt_der_jahre.html aus der Quelle.

Builds the finished, offline exhibition page from the source:
  1. inserts the map data from maps.json (const MAPS = ...)
  2. embeds only the glyphs the page needs from the fonts as WOFF2

Fonts (SIL Open Font License) go into web/src/fonts/ first:
  Shippori Mincho  Regular, SemiBold, ExtraBold   https://fonts.google.com/specimen/Shippori+Mincho
  Big Shoulders Display (variable)                https://fonts.google.com/specimen/Big+Shoulders+Display

Run:  pip install fonttools brotli
      python build.py
"""
import base64, io, json, pathlib, string
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).parent
SRC, OUT, FONTS = HERE / 'stadt_der_jahre.src.html', HERE.parent / 'stadt_der_jahre.html', HERE / 'fonts'

html = SRC.read_text(encoding='utf-8')
maps = json.loads((HERE / 'maps.json').read_text(encoding='utf-8'))
assert html.count('const MAPS = null;') == 1
html = html.replace('const MAPS = null;', 'const MAPS = ' + json.dumps(maps, separators=(',', ':')) + ';')

# every character on the page plus everything that can appear at runtime
chars = ''.join(sorted(set(html + string.printable + 'äöüÄÖÜß°℃〜–—−±·…、。（）：「」・×÷') - set('\n\r\t\x0b\x0c')))

def woff2(path):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['*']      # keep vert/vrt2 for vertical Japanese text
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    opts.hinting = False
    font = TTFont(path)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO(); font.flavor = 'woff2'; font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()

FACES = [('Shippori Mincho', '400', 'ShipporiMincho-Regular.ttf'),
         ('Shippori Mincho', '600', 'ShipporiMincho-SemiBold.ttf'),
         ('Shippori Mincho', '800', 'ShipporiMincho-ExtraBold.ttf'),
         ('Big Shoulders Display', '100 900', 'BigShouldersDisplay[wght].ttf')]
css = []
for fam, w, fn in FACES:
    if not (FONTS / fn).exists():
        print('missing font, page will use system fonts:', fn); continue
    css.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:block;"
               f"src:url(data:font/woff2;base64,{woff2(FONTS / fn)}) format('woff2')}}")
html = html.replace('/*FONTS*/', '\n'.join(css), 1)
OUT.write_text(html, encoding='utf-8')
print(f'{OUT.name}: {len(html) // 1024} KB, {len(css)} fonts embedded')
