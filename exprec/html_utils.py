from yattag import Doc
from pathlib import Path
import colorhash
import pandas as pd
from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.models import HoverTool
import bokeh.colors

from exprec import constants as c
from exprec import utils


ICON_BY_STATUS = {
    'running': 'fas fa-play text-primary',
    'succeeded': 'fas fa-check text-success',
    'failed': 'fas fa-times text-danger',
}

FIGURE_WIDTH = 600
FIGURE_HEIGHT = 400


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


def icon_title(icon_name, title):
    return fa_icon(icon_name) + ' ' + title


def create_table(columns, item_by_column_list, id, attrs=None, classes_by_column=None, extra_ths=()):
    if attrs is None:
        attrs = [{} for _ in range(len(columns))]
    assert len(attrs) == len(columns), (len(attrs), len(columns))

    if classes_by_column is None:
        classes_by_column = {column: [] for column in columns}

    doc, tag, text = Doc().tagtext()

    with tag('small'):
        with tag('table', klass='table display', id=id):
            with tag('thead'):
                with tag('tr'):
                    for name, colspan in extra_ths:
                        with tag('th'):
                            doc.attr(colspan=colspan)
                            text(name)

                with tag('tr'):
                    for column in columns:
                        with tag('th', scope='col'):
                            doc.attr(klass=' '.join(classes_by_column[column]))
                            doc.asis(column)

            with tag('tbody'):
                for item_by_column in item_by_column_list:
                    with tag('tr'):
                        for column, attr in zip(columns, attrs):
                            with tag('td', *attr):
                                doc.attr(klass=' '.join(classes_by_column[column]))
                                item = get(item_by_column[column], default='<div style="color: #B2B2B2;">N/A</div>')
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


def color_circle(string):
    hex_color = colorhash.ColorHash(string).hex
    circle = "<i class='fas fa-circle' style='color:{}'></i>".format(hex_color)
    return circle


def color_circle_and_string(string):
    return '{} {}'.format(color_circle(string), string)


def create_charts(uuids):
    paths = [Path(c.DEFAULT_PARENT_FOLDER)/uuid for uuid in uuids]

    html = ''
    for uuid in uuids:
        experiment_json = utils.load_experiment_json(uuid)
        title = experiment_json['title']
        
        if title:
            html += '{} {} - {}\n<br>'.format(color_circle(uuid), utils.get_short_uuid(uuid), title)
        else:
            html += '{} {}\n<br>'.format(color_circle(uuid), utils.get_short_uuid(uuid))

    scalar_names = get_all_scalar_names(paths)

    hover = HoverTool(
        tooltips=[
            ('step', '@x'),
            ('value', '@y'),
        ],
        mode='vline'
    )

    plots = []

    for scalar_name in scalar_names:
        plot = figure(
            tools=[hover, 'reset', 'pan', 'wheel_zoom', 'box_zoom'], 
            title=scalar_name,
            x_axis_label='Step',
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
        )

        for uuid, path in zip(uuids, paths):
            scalar_file = path / c.SCALARS_FOLDER / '{}.csv'.format(scalar_name)

            if scalar_file.is_file():
                df = pd.read_csv(scalar_file)
                
                source = ColumnDataSource(data={
                    'x': df['step'],
                    'y': df['value'],
                })

                color = colorhash.ColorHash(uuid).rgb

                plot.line('x', 'y', 
                    source=source, 
                    line_color=bokeh.colors.RGB(*color),
                    legend=utils.get_short_uuid(uuid),
                    line_width=2,
                )

        plot.legend.location = "top_left"
        plot.legend.click_policy = "hide"

        script, div = components(plot)
        plots.append('{}\n{}'.format(script, div))

    return html + '\n\n'.join(plots)


def get_all_scalar_names(paths):
    scalar_names = set()
    for path in paths:
        scalars_folder = path / c.SCALARS_FOLDER

        scalar_paths = scalars_folder.glob('*.csv')
        scalar_names.update(scalar_path.stem for scalar_path in scalar_paths)
    
    scalar_names = sorted(list(scalar_names))

    return scalar_names


def create_parameters(uuids):
    experiment_json_by_uuid = {uuid: utils.load_experiment_json(uuid) for uuid in uuids}

    params_by_uuid = {uuid: experiment_json['parameters'] for uuid, experiment_json in experiment_json_by_uuid.items()}
    params_by_uuid = {utils.get_short_uuid(uuid): params for uuid, params in params_by_uuid.items()}

    all_params = set()
    for params in params_by_uuid.values():
        all_params.update(params)
    all_params = sorted(list(all_params))

    rows = []
    for param in all_params:
        row = {'Parameter': param}
        for uuid, params in params_by_uuid.items():
            row[uuid] = str(params[param]) if param in params else None
        rows.append(row)
    
    # The last column has width 100%:
    attrs = [[]]*len(uuids) + [[('style', 'width: 100%;')]]

    return create_table(['Parameter', *params_by_uuid.keys()], rows, id='parameter-table', attrs=attrs)
