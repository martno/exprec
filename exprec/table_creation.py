import datetime
from pathlib import Path
import subprocess
import markdown
import psutil
import cgi

from exprec import utils
from exprec import html_utils
from exprec import constants as c
from exprec.html_utils import same_line

N_SIGNIFICANT_DIGITS = 4

METADATA_JSON_FILENAME = 'experiment.json'

COLUMNS = [
    'UUID',  # This must be the first column, since main.js refers to index 0 when accessing the UUID. 
    'select-row',
    'DetailsControl',
    'Show',
    'Icons',
    'PID',
    'ID',
    'Title',
    'Filename',
    'Duration',
    'Start',
    'End',
    'Tags',
    'Name',
    'File space',
    'Git commit',
    'Description',
    'Conclusion',
    'Arguments',
    'Exception',
]

CLASSES_BY_COLUMN = {
    'select-row': ['select-checkbox', 'hidden-title'],
    'DetailsControl': ['hidden-title', 'details-control'],
    'UUID': ['hidden-column'],
    'Show': ['hidden-title'],
    'Icons': ['hidden-title'],
    'PID': ['toggle', 'hidden-column'],
    'ID': ['toggle'],
    'Title': ['toggle'],
    'Filename': ['toggle'],
    'Duration': ['toggle'],
    'Start': ['toggle'],
    'End': ['toggle', 'hidden-column'],
    'Tags': ['toggle'],
    'Name': ['toggle', 'hidden-column'],
    'File space': ['toggle'],
    'Git commit': ['toggle'],
    'Description': ['hidden-column'],
    'Conclusion': ['hidden-column'],
    'Arguments': ['hidden-column'],
    'Exception': ['hidden-column'],
}


def create_table_from_uuids(uuids, path, filters):
    path = Path(c.DEFAULT_PARENT_FOLDER)
    uuids = utils.get_uuids(path)
    all_scalars = utils.get_all_scalars(uuids)
    all_params = utils.get_all_parameters(uuids)    

    procedure_item_by_column_list = []
    for uuid in uuids:
        metadata_json_path = path/uuid/METADATA_JSON_FILENAME
        metadata = utils.load_json(str(metadata_json_path))

        if not show_experiment(metadata, filters):
            continue

        procedure_item_by_column = create_procedure_item_by_column(uuid, path/uuid, metadata, all_scalars, all_params)
        procedure_item_by_column_list.append(procedure_item_by_column)
    
    classes_by_dynamic_columns = {column: ['toggle', 'hidden-column'] for column in all_scalars + all_params}
    classes_by_column = {**CLASSES_BY_COLUMN, **classes_by_dynamic_columns}

    html = '<div style="text-align: right"><small>Updated at {}</small></div>'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html += '\n'
    html += html_utils.create_table(COLUMNS + all_scalars + all_params, procedure_item_by_column_list, id='experiment-table', 
        classes_by_column=classes_by_column, extra_ths=[('', len(COLUMNS)), ('Scalars', len(all_scalars)), ('Parameters', len(all_params))])
    
    return html


def show_experiment(metadata, filters):
    tags = metadata['tags']

    blacklist = filters['blacklist']
    whitelist = filters['whitelist']

    if any(tag in blacklist for tag in tags):
        return False

    if len(whitelist) == 0:
        return True
    
    return any(tag in whitelist for tag in tags)


def create_procedure_item_by_column(uuid, path, metadata, all_scalars, all_params):
    name = metadata['name']
    start = datetime.datetime.strptime(metadata['startedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")
    end = None if metadata['endedDatetime'] is None else datetime.datetime.strptime(metadata['endedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")

    if end is None:
        duration = datetime.datetime.now() - start
    else:
        duration = end - start
    duration = utils.floor_timedelta(duration)

    status = metadata['status']
    tags = sorted(metadata['tags'])

    file_space = utils.get_file_space_representation(str(path/c.FILES_FOLDER))

    experiment_pid = int(metadata['pid'])
    pids = psutil.pids()
    pid_icon_name = 'fas fa-play text-success' if experiment_pid in pids else 'fas fa-stop text-danger'

    # Set lightbulb class:
    if metadata['status'] == 'running':
        lightbulb_class = 'text-{}'.format('primary' if metadata['conclusion'] else 'secondary')
    else:
        lightbulb_class = 'text-{}'.format('primary' if metadata['conclusion'] else 'danger')

    infoicon_class = 'text-primary' if metadata['description'] else 'text-secondary'

    arguments = utils.arguments_to_string(metadata['arguments'])

    procedure_item_by_column = {
        'select-row': '',
        'DetailsControl': '',
        'UUID': uuid,
        'Show': "<button class='btn btn-primary btn-xs experiment-button' id='button-{}'>Show</button>".format(uuid),
        'Icons': same_line('{}<span style="display:inline-block; width: 12px;"></span>{}<span style="display:inline-block; width: 12px;"></span>{}'.format(
            html_utils.get_status_icon_tag(status), 
            html_utils.icon('fas fa-info-circle {}'.format(infoicon_class)), 
            html_utils.icon('fas fa-lightbulb {}'.format(lightbulb_class)),
        )),
        'PID': same_line(html_utils.fa_icon(pid_icon_name) + ' ' + str(experiment_pid)),
        'Name': name if len(name) > 0 else None,
        'Title': cgi.escape(metadata['title']) if metadata['title'] else None,
        'Filename': same_line(html_utils.color_circle_and_string(metadata['filename'])),
        'Duration': str(duration),
        'Start': start.strftime('%Y-%m-%d %H:%M:%S'),
        'End': end.strftime('%Y-%m-%d %H:%M:%S') if end is not None else None,
        'Tags': ' '.join([html_utils.badge(tag) for tag in tags]),
        'File space': file_space,
        'ID': same_line("""<button class='btn btn-light btn-xs' onclick="copyToClipboard('{}')">{}</button>""".format(utils.get_short_uuid(uuid), html_utils.fa_icon('copy')) \
            + ' ' + html_utils.color_circle(uuid) + ' ' + utils.get_short_uuid(uuid)),
        'Git commit': same_line(html_utils.color_circle_and_string(metadata['git']['short'])) if metadata['git'] is not None else None,
        'Description': markdown.markdown(cgi.escape(metadata['description'])),
        'Conclusion': markdown.markdown(cgi.escape(metadata['conclusion'])),
        'Arguments': html_utils.monospace(arguments + """ <button class='btn btn-light btn-xs' onclick="copyToClipboard('{}')">{}</button>""".format(arguments, html_utils.fa_icon('copy')))
            if arguments else '',
        'Exception': html_utils.monospace('{}: {}'.format(metadata['exceptionType'], metadata['exceptionValue']) if metadata['exceptionType'] is not None else ''),
    }

    for scalar_name in all_scalars:
        value = get_scalar_value(path, scalar_name)
        if value is not None:
            value = str(utils.round_to_significant_digits(value, N_SIGNIFICANT_DIGITS))
        procedure_item_by_column[scalar_name] = value

    params = metadata['parameters']
    for name in all_params:
        if name in params:
            value = params[name]
            if type(value) in (int, float):
                value = utils.round_to_significant_digits(value, N_SIGNIFICANT_DIGITS)
            value = str(value)
        else:
            value = None
        
        procedure_item_by_column[name] = value

    return procedure_item_by_column


def list_join(lst, item):
    n = len(lst)
    lists = zip(lst, [item] * n)
    lists = [list(tple) for tple in lists]
    return flatten(lists)[:-1]


def flatten(lst):
    return sum(lst, [])


def get_scalar_value(path, scalar_name):
    scalar_folder_path = path/c.SCALARS_FOLDER
    scalar_path = scalar_folder_path / '{}.csv'.format(scalar_name)

    if not scalar_path.exists():
        return None

    last_line = get_last_line_in_file(str(scalar_path))
    _, value, _ = last_line.strip().split(',')
    if value == 'value':
        return None
    
    return float(value)


def get_last_line_in_file(filepath):
    return subprocess.check_output(['tail', '-1', filepath]).decode('utf-8')

