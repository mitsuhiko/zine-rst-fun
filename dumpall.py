import os
# that import is needed because of cirular deps in zine :(
import zine.application
from urlparse import urlparse
from zine.utils.zeml import parse_zeml, Textifier
from sqlalchemy import create_engine


class RSTTextifier(Textifier):

    def visit_sourcecode(self, element):
        self.keep_whitespace = True
        self.flush_par()
        self.curpar.append('.. sourcecode:: %s' % element.attributes.get('syntax', 'text'))
        self.flush_par()
        self.indentation += 4
    def depart_sourcecode(self, element):
        self.flush_par(nowrap=True)
        self.keep_whitespace = False
        self.indentation -= 4

    def visit_pre(self, element):
        self.keep_whitespace = True
        self.flush_par()
        self.curpar.append('::')
        self.flush_par()
        self.indentation += 4
    depart_pre = depart_sourcecode

    def visit_a(self, element):
        self.curpar.append('`')
    def depart_a(self, element):
        if 'href' not in element.attributes:
            return
        self.curpar.append(' <%s>`_' % element.attributes['href'])


def to_rst(zeml):
    return RSTTextifier(ignore_relative_urls=False).multiline(zeml)


engine = create_engine('postgresql:///lucumr', convert_unicode=True)
results = []

for item in engine.execute('select post_id, slug, title, text from posts'):
    filename = os.path.join('dumps', item.slug.strip('/') + '.rst')
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
    zeml = parse_zeml('<h1>%s</h1>%s' % (item.title, item.text), 'text')
    open(filename, 'w').write(to_rst(zeml).encode('utf-8'))
    results.append((filename, engine.execute('select count(*) from comments where post_id = %d and status != 3' % item.post_id).fetchone()[0]))

results.sort(key=lambda x: x[1])
for filename, comments in results:
    print '%-10d  %s' % (comments, filename)
