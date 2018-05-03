import datetime
from yattag import Doc

import utils
import html_utils
import constants as c


METADATA_JSON_FILENAME = 'experiment.json'

COLUMNS = [
    'Select',
    'Show',
    'Status',
    'Name',
    'Filename',
    'Duration',
    'Start',
    'End',
    'Tags',
    'File space',
    'ID',
]


def create_table_from_uuids(uuids, path):
    procedure_item_by_column_list = []
    for uuid in uuids:
        metadata_json_path = path/uuid/METADATA_JSON_FILENAME
        metadata = utils.load_json(str(metadata_json_path))
        procedure_item_by_column = create_procedure_item_by_column(uuid, path/uuid, metadata)
        procedure_item_by_column_list.append(procedure_item_by_column)

    return html_utils.create_table(COLUMNS, procedure_item_by_column_list)


def create_procedure_item_by_column(uuid, path, metadata):
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

    procedure_item_by_column = {
        'Select': '<input class="experiment-row" type="checkbox" value="" id="checkbox-{}">'.format(uuid),
        'Show': "<button class='btn btn-primary experiment-button' id='button-{}'>Show</button>".format(uuid),
        'Status': html_utils.get_status_icon_tag(status),
        'Name': name if len(name) > 0 else None,
        'Filename': html_utils.monospace(metadata['filename']),
        'Duration': str(duration),
        'Start': start.strftime('%Y-%m-%d %H:%M:%S'),
        'End': end.strftime('%Y-%m-%d %H:%M:%S') if end is not None else None,
        'Tags': ' '.join([html_utils.badge(tag) for tag in tags]),
        'File space': file_space,
        'ID': html_utils.monospace(uuid),
    }

    return procedure_item_by_column


def list_join(lst, item):
    n = len(lst)
    lists = zip(lst, [item] * n)
    lists = [list(tple) for tple in lists]
    return flatten(lists)[:-1]


def flatten(lst):
    return sum(lst, [])
