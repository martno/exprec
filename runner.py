import attr
import uuid
from pathlib import Path
import sys
import pip
import datetime
import json
import shutil
import logging


DEFAULT_PARENT_FOLDER = '.procedures'

METADATA_JSON_FILENAME = 'procedure.json'
PACKAGES_FILENAME = 'pip_freeze.txt'
SOURCE_CODE_FOLDER = 'src'


@attr.s
class Procedure:
    name = attr.ib(default='')
    verbose = attr.ib(default=True)
    exceptions_to_ignore = attr.ib(default=[KeyboardInterrupt])
    parent_folder = attr.ib(default=DEFAULT_PARENT_FOLDER)

    def __attrs_post_init__(self):
        self.uuid = uuid.uuid1()  # Time UUID
        self.path = Path(self.parent_folder) / str(self.uuid)

    def __enter__(self):
        Path(self.parent_folder).mkdir(exist_ok=True)
        self.path.mkdir(exist_ok=False)

        if self.verbose:
            name = self.name if len(self.name) > 0 else '(name N/A)'
            print('Running procedure {} {}'.format(self.uuid, name))
        
        setup_procedure(self.path, self.name)

        self._create_streams()

        return self

    def _create_streams(self):
        self.stdout_logfile = (self.path/'stdout.txt').open('w')
        self.stderr_logfile = (self.path/'stderr.txt').open('w')
        self.stdcombined_logfile = (self.path/'stdcombined.txt').open('w')

        self.stdout = sys.stdout
        self.stderr = sys.stderr
        stdout_stream = MultiStream([sys.stdout, self.stdout_logfile, self.stdcombined_logfile])
        stderr_stream = MultiStream([sys.stderr, self.stderr_logfile, self.stdcombined_logfile])

        sys.stdout = stdout_stream
        sys.stderr = stderr_stream

    def __exit__(self, type, value, traceback):
        self._close_streams()

        with UpdateJson(str(self.path/METADATA_JSON_FILENAME)) as metadata:
            succeeded = type is None or type in self.exceptions_to_ignore
            metadata['status'] = 'succeeded' if succeeded else 'failed'
            metadata['endedDatetime'] = datetime.datetime.now().isoformat()

        if type is not None:
            return type in self.exceptions_to_ignore

    def _close_streams(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        self.stdout_logfile.close()
        self.stderr_logfile.close()
        self.stdcombined_logfile.close()


@attr.s
class MultiStream:
    streams = attr.ib()

    def write(self, string):
        for stream in self.streams:
            stream.write(string)
    
    def flush(self):
        for stream in self.streams:
            stream.flush()


def setup_procedure(path, name):
    create_metadata_json(path, name)
    create_pip_freeze_file(path)
    copy_source_code(path)


def create_metadata_json(path, name):
    filename = sys.argv[0]

    metadata = {
        'name': name,
        'status': 'running',
        'startedDatetime': datetime.datetime.now().isoformat(),
        'filename': sys.argv[0],
        'arguments': sys.argv[1:],
        'pythonVersion': sys.version,
    }

    dump_json(metadata, str(path/METADATA_JSON_FILENAME))


def create_pip_freeze_file(path):
    installed_packages = pip.get_installed_distributions()
    installed_packages_list = sorted(['{}=={}'.format(package.key, package.version) 
                                      for package in installed_packages])

    with open(str(path/PACKAGES_FILENAME), 'w') as fp:
        fp.write('\n'.join(installed_packages_list))


def copy_source_code(path):
    python_files = Path('.').glob('**/*.py')
    python_files = [python_filepath for python_filepath in python_files if not is_hidden_path(python_filepath)]

    for python_file in python_files:
        shutil.copy(str(python_file), str(path/python_file))


def is_hidden_path(path):
    return any(part.startswith('.') for part in path.parts)


def uuid1_to_datetime(uuid1):
    import datetime
    return datetime.datetime.fromtimestamp((uuid1.time - 0x01b21dd213814000)*100/1e9)


@attr.s
class UpdateJson:
    """Updates the json file in the given path

    E.g.
    >>> with UpdateJson(path) as json_data:
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
    

