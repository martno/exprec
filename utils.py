import attr
import json
import datetime
import os
import natural.size
from pathlib import Path

import constants as c


@attr.s
class UpdateJsonFile:
    """Updates the json file in the given path

    E.g.
    >>> with UpdateJsonFile(path) as json_data:
    ...     json_data['new_value'] = 42
    """
    path = attr.ib()

    def __enter__(self):
        self.json_data = load_json(self.path)
        return self.json_data

    def __exit__(self, type, value, traceback):
        if type is not None:
            return False
        
        dump_json(self.json_data, self.path)


def load_json(path):
    with open(path) as fp:
        return json.load(fp)


def dump_json(json_data, path):
    with open(path, 'w') as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=4)


def floor_timedelta(td):
    return datetime.timedelta(days=td.days, seconds=td.seconds)


def get_file_space_representation(root):
    file_space = get_total_size(root)
    if file_space > 0:
        file_space = natural.size.decimalsize(file_space)
    else:
        file_space = None
    
    return file_space


def get_total_size(root):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)

    return total_size


def get_uuids(path):
    metadata_json_paths = path.glob('*/' + c.METADATA_JSON_FILENAME)
    return [json_path.parent.parts[-1] for json_path in metadata_json_paths]


def get_all_tags(uuids):
    all_tags = []

    for uuid in uuids:
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.METADATA_JSON_FILENAME
        experiment_json = load_json(str(experiment_json_path))

        all_tags += experiment_json['tags']
    
    all_tags = sorted(list(set(all_tags)))

    if 'archive' in all_tags:
        all_tags.remove('archive')

    return all_tags


def get_all_scalars(uuids):
    all_columns = []

    for uuid in uuids:
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.METADATA_JSON_FILENAME
        experiment_json = load_json(str(experiment_json_path))

        all_columns += list(experiment_json['scalars'].keys())
    
    all_columns = sorted(list(set(all_columns)))

    return all_columns


def get_all_parameters(uuids):
    all_params = []

    for uuid in uuids:
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.METADATA_JSON_FILENAME
        experiment_json = load_json(str(experiment_json_path))

        all_params += list(experiment_json['parameters'].keys())
    
    all_params = sorted(list(set(all_params)))

    return all_params
