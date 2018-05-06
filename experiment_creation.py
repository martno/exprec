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
        with tag('button', klass="btn btn-primary button-go-back", style="width: 61px;"):
            doc.asis(html_utils.fa_icon('arrow-left'))
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
        content_by_tab_name[icon_title('eye', 'Summary')] = create_summary(uuid, path, experiment_json)
        content_by_tab_name[icon_title('terminal', 'Output')] = create_output(path)
        content_by_tab_name[icon_title('code', 'Code')] = create_code(path, experiment_json)
        content_by_tab_name[icon_title('cube', 'Packages')] = create_packages(path)
        content_by_tab_name[icon_title('chart-bar', 'Parameters')] = create_parameters(experiment_json)
        content_by_tab_name[icon_title('chart-area', 'Charts')] = create_charts(experiment_json)
        content_by_tab_name[icon_title('sticky-note', 'Notes')] = create_notes(uuid, experiment_json)

        content_by_tab_name = collections.OrderedDict([(key, html_utils.margin(value)) for key, value in content_by_tab_name.items()])

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

    parents = get_parents(experiment_json)

    items = [
        ('Status', html_utils.get_status_icon_tag(status) + ' ' + status),
        ('Name', experiment_json['name']),
        ('ID', html_utils.monospace(uuid)),
        ('Start', start.strftime('%Y-%m-%d %H:%M:%S')),
        ('End', end.strftime('%Y-%m-%d %H:%M:%S') if end is not None else None),
        ('Duration', str(duration)),
        ('Filename', experiment_json['filename']),
        ('Tags', ' '.join([html_utils.badge(tag) for tag in tags])),
        ('Python version', experiment_json['pythonVersion']),
        ('Arguments', html_utils.monospace(' '.join(experiment_json['arguments']))),
        ('File space', utils.get_file_space_representation(str(path/c.FILES_FOLDER))),
        ('Parents', html_utils.monospace(' '.join(parents))),
    ]

    item_by_column_list = [{'Name': name, 'Value': value} for name, value in items]

    return html_utils.create_table(columns, item_by_column_list, id='summary-table', attrs=[[], [('style', 'width: 100%;')]])


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
    return html_utils.create_table(['Parameter', 'Value'], param_list, id='parameter-table', attrs=[[], [('style', 'width: 100%;')]])


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


def get_parents(experiment_json):
    return list(experiment_json['fileDependencies'].keys())


def create_notes(uuid, experiment_json):
    notes = experiment_json['notes']

    html = """
    <textarea class="form-control" id="notes-textarea" rows="15">{notes}</textarea>
    <br>
    <button type="button" class="btn btn-primary" onclick="myFunction()">Save</button>

    <script>
    function myFunction() {{
        var notes = $("#notes-textarea").val()
        postJson("/save-notes/{uuid}", notes);
    }}
    </script>
    """.format(notes=notes, uuid=uuid)

    return html
