import datetime
from yattag import Doc

import utils
import html_utils


METADATA_JSON_FILENAME = 'experiment.json'

COLUMNS = [
    'Select',
    'Status',
    'Name',
    'Filename',
    'Duration',
    'Start',
    'End',
    'Tags',
    'ID',
]

ICON_BY_STATUS = {
    'running': 'fas fa-play text-primary',
    'succeeded': 'fas fa-check text-success',
    'failed': 'fas fa-times text-danger',
}


def create_table_from_uuids(uuids, path):
    procedure_item_by_column_list = []
    for uuid in uuids:
        metadata_json_path = path/uuid/METADATA_JSON_FILENAME
        metadata = utils.load_json(str(metadata_json_path))
        procedure_item_by_column = create_procedure_item_by_column(uuid, metadata)
        procedure_item_by_column_list.append(procedure_item_by_column)

    return create_table(COLUMNS, procedure_item_by_column_list)


def create_procedure_item_by_column(uuid, metadata):
    name = metadata['name']
    start = datetime.datetime.strptime(metadata['startedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")
    end = None if metadata['endedDatetime'] is None else datetime.datetime.strptime(metadata['endedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")

    if end is None:
        duration = datetime.datetime.now() - start
    else:
        duration = end - start

    status = metadata['status']
    tags = sorted(metadata['tags'])

    procedure_item_by_column = {
        'Select': "<button class='btn btn-primary experiment-button' id='button-{}'>Show</button>".format(uuid),
        'Status': html_utils.icon(ICON_BY_STATUS[status]),
        'Name': name if len(name) > 0 else None,
        'Filename': html_utils.monospace(metadata['filename']),
        'Duration': str(duration),
        'Start': start.strftime('%Y-%m-%d %H:%M:%S'),
        'End': end.strftime('%Y-%m-%d %H:%M:%S') if end is not None else None,
        'Tags': ' '.join([html_utils.badge(tag) for tag in tags]),
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


def create_table(columns, item_by_column_list):
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
                    for column in columns:
                        with tag('td'):
                            item = get(item_by_column[column], 'N/A')
                            doc.asis(item)

    return doc.getvalue()            


def get(value, default):
    if value is None:
        return default
    return value

