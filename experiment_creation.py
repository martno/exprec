from yattag import Doc
import collections
from pathlib import Path

import html_utils


DEFAULT_PARENT_FOLDER = '.procedures'


def create_experiment_div(uuid):
    path = Path(DEFAULT_PARENT_FOLDER)/uuid

    doc, tag, text = Doc().tagtext()
    with tag('div'):
        with tag('button', klass="btn btn-primary go-back", style="width: 61px;"):
            doc.asis(html_utils.icon('fas fa-chevron-left'))
        doc.stag('hr')
        with tag('h5'):
            text(uuid)
        
        doc.stag('hr')

        content_by_tab_name = collections.OrderedDict()
        content_by_tab_name['A'] = 'a'
        content_by_tab_name['B'] = 'b'

        tabs_html = html_utils.create_tabs(content_by_tab_name, tabs_id='experiment-tabs')

        doc.asis(tabs_html)

    return doc.getvalue()







