import attr
import uuid
from pathlib import Path
import sys
import pip
import datetime
import json
import shutil
import logging
import subprocess

import utils


DEFAULT_PARENT_FOLDER = '.experiments'

METADATA_JSON_FILENAME = 'experiment.json'
PACKAGES_FILENAME = 'pip_freeze.txt'
SOURCE_CODE_FOLDER = 'src'


@attr.s
class Experiment:
    name = attr.ib(default='')
    tags = attr.ib(default=attr.Factory(list))
    verbose = attr.ib(default=True)
    exceptions_to_ignore = attr.ib(default=[KeyboardInterrupt])
    parent_folder = attr.ib(default=DEFAULT_PARENT_FOLDER)

    def __attrs_post_init__(self):
        self.name = self.name.strip()

        self.uuid = uuid.uuid1()  # Time UUID
        self.path = Path(self.parent_folder) / str(self.uuid)

    def __enter__(self):
        Path(self.parent_folder).mkdir(exist_ok=True)

        if not is_name_available(self.name, self.parent_folder):
            raise ValueError("Name '{}' is already occupied.".format(self.name))

        self.path.mkdir(exist_ok=False)

        if self.verbose:
            name = self.name if len(self.name) > 0 else '(name N/A)'
            print('Running experiment {} {}'.format(self.uuid, name))
        
        setup_procedure(self.path, self.name, self.tags)

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

        with utils.UpdateJsonFile(str(self.path/METADATA_JSON_FILENAME)) as metadata:
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


def is_name_available(name, folder):
    if name == '':
        return True

    for metadata_json_path in Path(folder).glob('*/' + METADATA_JSON_FILENAME):
        metadata_json = utils.load_json(str(metadata_json_path))
        if metadata_json['name'] == name:
            return False
    
    return True


@attr.s
class MultiStream:
    streams = attr.ib()

    def write(self, string):
        for stream in self.streams:
            stream.write(string)
    
    def flush(self):
        for stream in self.streams:
            stream.flush()


def setup_procedure(path, name, tags):
    create_metadata_json(path, name, tags)
    create_pip_freeze_file(path)
    copy_source_code(path)


def create_metadata_json(path, name, tags):
    filename = sys.argv[0]

    metadata = {
        'name': name,
        'tags': sorted(tags),
        'status': 'running',
        'startedDatetime': datetime.datetime.now().isoformat(),
        'endedDatetime': None,
        'filename': sys.argv[0],
        'arguments': sys.argv[1:],
        'pythonVersion': sys.version,
    }   

    utils.dump_json(metadata, str(path/METADATA_JSON_FILENAME))


def create_pip_freeze_file(path):
    installed_packages_list = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8').split('\n')
    installed_packages_list = sorted(installed_packages_list)

    with open(str(path/PACKAGES_FILENAME), 'w') as fp:
        fp.write('\n'.join(installed_packages_list))


def copy_source_code(path):
    python_files = Path('.').glob('**/*.py')
    python_files = [python_filepath for python_filepath in python_files if not is_hidden_path(python_filepath)]

    for python_file in python_files:
        target_path = path/SOURCE_CODE_FOLDER/python_file
        target_path.parent.mkdir(exist_ok=True)

        shutil.copy(str(python_file), str(target_path))


def is_hidden_path(path):
    return any(part.startswith('.') for part in path.parts)


def uuid1_to_datetime(uuid1):
    import datetime
    return datetime.datetime.fromtimestamp((uuid1.time - 0x01b21dd213814000)*100/1e9)    

