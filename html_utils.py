from yattag import Doc


ICON_BY_STATUS = {
    'running': 'fas fa-play text-primary',
    'succeeded': 'fas fa-check text-success',
    'failed': 'fas fa-times text-danger',
}


def monospace(string):
    return "<pre>{}</pre>".format(string)
    # return """<p style="font-family: 'Lucida Console', monospace;">{}<p>""".format(string)


def badge(string):
    return "<span class='badge badge-primary'>{}</span>".format(string)


def icon(icon_name):
    return "<i class='{}'></i>".format(icon_name)


def fa_icon(icon_name):
    return icon('fas fa-' + icon_name)


def get_status_icon_tag(status):
    return icon(ICON_BY_STATUS[status])


def create_table(columns, item_by_column_list, attrs=None):
    if attrs is None:
        attrs = [{} for _ in range(len(columns))]
    assert len(attrs) == len(columns), (len(attrs), len(columns))

    doc, tag, text = Doc().tagtext()

    with tag('table', klass='table'):
        with tag('thead'):
            with tag('tr'):
                for column in columns:
                    with tag('th', scope='col'):
                        doc.asis(get(column, 'N/A'))

        with tag('tbody'):
            for item_by_column in item_by_column_list:
                with tag('tr'):
                    for column, attr in zip(columns, attrs):
                        with tag('td', *attr):
                            item = get(item_by_column[column], 'N/A')
                            doc.asis(item)

    return doc.getvalue()            


def get(value, default):
    if value is None:
        return default
    return value


def create_tabs(content_by_tab_name, tabs_id):
    doc, tag, text = Doc().tagtext()

    with tag('ul', klass='nav nav-pills', id=tabs_id, role='tablist'):
        is_first_tab = True
        for i, tab_name in enumerate(content_by_tab_name.keys()):
            with tag('li', klass='nav-item'):
                tab_id = '{}--tab-{}'.format(tabs_id, i)

                with tag('a', ('data-toggle', 'pill'), klass='nav-link', href='#' + tab_id, role='tab'):
                    if is_first_tab:
                        doc.attr(klass='nav-link active')
                        is_first_tab = False

                    doc.asis(tab_name)
                
    with tag('div', klass='tab-content'):
        is_first_tab = True
        for i, content in enumerate(content_by_tab_name.values()):
            tab_id = '{}--tab-{}'.format(tabs_id, i)

            with tag('div', id=tab_id, klass='tab-pane', role='tabpanel'):
                if is_first_tab:
                    doc.attr(klass='tab-pane active')
                    is_first_tab = False
                
                doc.asis(content)
    
    return doc.getvalue()


def code(code_string, language=None):
    if language is None:
        return "<pre><code>{}</code></pre>".format(code_string)
    
    return '<pre><code class="{}">{}</code></pre>'.format(language, code_string)


def margin(html, amount='10px'):
    return '<div style="margin: {}">{}</div>'.format(amount, html)

