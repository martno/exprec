from yattag import Doc


def monospace(string):
    return """<p style="font-family: 'Lucida Console', monospace;">{}<p>""".format(string)


def badge(string):
    return "<span class='badge badge-primary'>{}</span>".format(string)


def icon(icon_name):
    return "<i class='{}'></i>".format(icon_name)


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

                    text(tab_name)
                
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
