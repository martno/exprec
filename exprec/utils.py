import attr
import json
import datetime
import os
import humanize
from pathlib import Path
import shutil
import uuid

from exprec import constants as c


MINIMUM_SHORT_UUID_LENGTH = 7


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
        file_space = humanize.naturalsize(file_space)
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
        scalar_folder = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.SCALARS_FOLDER
        if scalar_folder.exists():
            scalar_filepaths = scalar_folder.glob('*.csv')
            all_columns += [scalar_filepath.stem for scalar_filepath in scalar_filepaths]
    
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


def restore_source_code(uuid):
    experiment_source_path = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.SOURCE_CODE_FOLDER
    assert experiment_source_path.exists()

    local_python_files = Path('.').glob('**/*.py')
    local_python_files = remove_hidden_paths(local_python_files)

    for python_file in local_python_files:
        os.remove(str(python_file))
    
    copy_source_code(source_path=experiment_source_path, target_path='.')


def copy_source_code(source_path, target_path, extension='*.py'):
    source_path = Path(source_path)
    target_path = Path(target_path)

    python_files = source_path.glob('**/' + extension)

    for source_file_path in python_files:
        python_file = source_file_path.relative_to(source_path)
        if is_hidden_path(python_file):
            continue

        target_file_path = target_path/python_file

        target_file_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(str(source_file_path), str(target_file_path))


def remove_hidden_paths(paths):
    return [path for path in paths if not is_hidden_path(path)]


def is_hidden_path(path):
    return any(part.startswith('.') for part in path.parts)


def get_class_name(object):
    return object.__class__.__name__


def load_experiment_json(uuid):
    path = Path(c.DEFAULT_PARENT_FOLDER)/uuid/c.METADATA_JSON_FILENAME
    return load_json(str(path))


def get_short_uuid(uuid):
    length = get_short_uuid_length()
    return uuid[:length]


def get_short_uuid_length():
    uuids = get_uuids(Path(c.DEFAULT_PARENT_FOLDER))

    if not uuids:
        return MINIMUM_SHORT_UUID_LENGTH

    for length in range(MINIMUM_SHORT_UUID_LENGTH, len(uuids[0])):
        short_uuids = set(uuid[:length] for uuid in uuids)
        if len(short_uuids) == len(uuids):
            return length
    
    assert False, "get_uuids() returned two identical uuids."


def get_full_uuid(short_uuid):
    uuids = get_uuids(Path(c.DEFAULT_PARENT_FOLDER))
    uuids = [uuid for uuid in uuids if uuid.startswith(short_uuid)]
    if not uuids:
        raise ValueError("No UUID exists corresponding to the short UUID '{}'".format(short_uuid))

    uuid = min(uuids, key=lambda uuid: uuid1_to_datetime(uuid))

    return uuid


def uuid1_to_datetime(uuid1_string):
    uuid1 = uuid.UUID(uuid1_string)
    return datetime.datetime(1582, 10, 15) + datetime.timedelta(microseconds=uuid1.time//10)


def round_to_significant_digits(value, n_digits):
    format_string = '%.{}g'.format(n_digits)
    return float(format_string % value)


def arguments_to_string(arguments):
    return ' '.join('"{}"'.format(arg) if ' ' in arg else arg for arg in arguments)
