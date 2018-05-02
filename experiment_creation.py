from yattag import Doc
import collections
from pathlib import Path
import datetime
import plotly.offline as offline
import plotly.graph_objs as go

import html_utils
import constants as c
import utils


def create_experiment_div(uuid):
    path = Path(c.DEFAULT_PARENT_FOLDER)/uuid

    experiment_json = utils.load_json(str(path/c.METADATA_JSON_FILENAME))

    doc, tag, text = Doc().tagtext()
    with tag('div'):
        with tag('button', klass="btn btn-primary go-back", style="width: 61px;"):
            doc.asis(html_utils.icon('fas fa-chevron-left'))
        doc.stag('hr')
        with tag('h5'):
            doc.asis(html_utils.get_status_icon_tag(experiment_json['status']))
            text(' ')
            text(uuid)

            doc.asis('<span style="display:inline-block; width: 16px;"></span>')

            tags = sorted(experiment_json['tags'])
            doc.asis(' '.join([html_utils.badge(tag) for tag in tags]))
        
        with tag('small'):
            text(experiment_json['filename'])
        
        doc.stag('hr')

        content_by_tab_name = collections.OrderedDict()
        content_by_tab_name[icon_title('eye', 'Summary')] = html_utils.margin(create_summary(uuid, path, experiment_json))
        content_by_tab_name[icon_title('terminal', 'Output')] = html_utils.margin(create_output(path))
        content_by_tab_name[icon_title('code', 'Code')] = html_utils.margin(create_code(path, experiment_json))
        content_by_tab_name[icon_title('cube', 'Packages')] = html_utils.margin(create_packages(path))
        content_by_tab_name[icon_title('chart-bar', 'Parameters')] = html_utils.margin(create_parameters(experiment_json))
        content_by_tab_name[icon_title('chart-area', 'Charts')] = html_utils.margin(create_charts(experiment_json))

        tabs_html = html_utils.create_tabs(content_by_tab_name, tabs_id='experiment-tabs')

        doc.asis(tabs_html)

    return doc.getvalue()


def icon_title(icon_name, title):
    return html_utils.fa_icon(icon_name) + ' ' + title


def create_summary(uuid, path, experiment_json):
    doc, tag, text = Doc().tagtext()

    columns = ['Name', 'Value']

    status = experiment_json['status']

    start = datetime.datetime.strptime(experiment_json['startedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")
    end = None if experiment_json['endedDatetime'] is None else datetime.datetime.strptime(experiment_json['endedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")

    if end is None:
        duration = datetime.datetime.now() - start
    else:
        duration = end - start
    duration = utils.floor_timedelta(duration)

    tags = sorted(experiment_json['tags'])

    file_space = utils.get_total_size(str(path/c.FILES_FOLDER))
    if file_space > 0:
        file_space = natural.size.decimalsize(file_space)
    else:
        file_space = None

    items = [
        ('Status', html_utils.get_status_icon_tag(status) + ' ' + status),
        ('Name', experiment_json['name']),
        ('ID', html_utils.monospace(uuid)),
        ('Start', start.strftime('%Y-%m-%d %H:%M:%S')),
        ('End', end.strftime('%Y-%m-%d %H:%M:%S')) if end is not None else None,
        ('Duration', str(duration)),
        ('Filename', experiment_json['filename']),
        ('Tags', ' '.join([html_utils.badge(tag) for tag in tags])),
        ('Python version', experiment_json['pythonVersion']),
        ('Arguments', ' '.join(experiment_json['arguments'])),
        ('File space', utils.get_file_space_representation(str(path/c.FILES_FOLDER)))
    ]
    
    item_by_column_list = [{'Name': name, 'Value': value} for name, value in items]

    return html_utils.create_table(columns, item_by_column_list, [[], [('style', 'width: 100%;')]])


def create_packages(path):
    pip_freeze_path = path/'pip_freeze.txt'

    with pip_freeze_path.open() as fp:
        pip_freeze = fp.read()
    
    return html_utils.monospace(pip_freeze)


def create_code(path, experiment_json):
    filename = experiment_json['filename']

    filepath = path/'src'/filename

    with filepath.open() as fp:
        code = fp.read()

    return html_utils.code(code, language='python')


def create_output(path):
    filepath = path/'stdcombined.txt'

    with filepath.open() as fp:
        output = fp.read()
    
    return html_utils.monospace(output)


def create_parameters(experiment_json):
    params = experiment_json['parameters']

    param_list = [{'Parameter': name, 'Value': str(params[name])} for name in sorted(list(params.keys()))]
    return html_utils.create_table(['Parameter', 'Value'], param_list, [[], [('style', 'width: 100%;')]])


def create_charts(experiment_json):
    html = ''

    for name, points in experiment_json['scalars'].items():
        steps = [point['step'] for point in points]
        values = [point['value'] for point in points]

        if steps[0] is None:
            steps = [i for i in range(len(steps))]

        figure_data = {
            'data': [{
                'x': steps,
                'y': values,
            }], 
            'layout': {
                'title': name,
                'autosize': True,
                'width': '100%',
                'height': '100%',
            }
        }

        div = offline.plot(figure_data, output_type='div')

        html += div

    return html

