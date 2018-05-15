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
import traceback
import platform
import os

from exprec import utils
from exprec import constants as c


DEFAULT_PARENT_FOLDER = '.experiments'

METADATA_JSON_FILENAME = 'experiment.json'
PACKAGES_FILENAME = 'pip_freeze.txt'
FILES_FOLDER = 'files'


@attr.s
class Experiment:
    name = attr.ib(default='')
    tags = attr.ib(default=attr.Factory(list))
    verbose = attr.ib(default=True)
    exceptions_to_ignore = attr.ib(default=[KeyboardInterrupt])
    parent_folder = attr.ib(default=DEFAULT_PARENT_FOLDER)

    def __attrs_post_init__(self):
        self.name = self.name.strip()

        self.uuid = str(uuid.uuid1())  # Time UUID
        self.path = Path(self.parent_folder) / self.uuid

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

    def __exit__(self, exc_type, exc_value, tb):
        reraise_exception = (exc_type is not None) and (exc_type not in self.exceptions_to_ignore)
        if reraise_exception:
            traceback.print_exception(exc_type, exc_value, tb)

        self._close_streams()

        with utils.UpdateJsonFile(str(self.path/METADATA_JSON_FILENAME)) as metadata:
            metadata['status'] = 'failed' if reraise_exception else 'succeeded'
            metadata['endedDatetime'] = datetime.datetime.now().isoformat()

            if reraise_exception:
                metadata['exceptionType'] = exc_type.__name__
                metadata['exceptionValue'] = str(exc_value)

        if exc_type is not None:
            return not reraise_exception

    def _close_streams(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        self.stdout_logfile.close()
        self.stderr_logfile.close()
        self.stdcombined_logfile.close()
    
    def set_parameter(self, name, value):
        json_path = self.path / METADATA_JSON_FILENAME
        with utils.UpdateJsonFile(str(json_path)) as metadata_json:
            metadata_json['parameters'][name] = value

    def add_scalar(self, name, value, step=None):
        json_path = self.path / METADATA_JSON_FILENAME
        with utils.UpdateJsonFile(str(json_path)) as metadata_json:
            if name not in metadata_json['scalars']:
                metadata_json['scalars'][name] = []

            metadata_json['scalars'][name].append({
                'value': value,
                'step': step,
                'time': datetime.datetime.now().isoformat(),
            })

    def open(self, filename, mode='r', uuid=None):
        assert uuid != self.uuid, "'uuid' may not be the same as this experiment's uuid. Set `uuid=None` to open a file with this experiment."
        assert '..' not in filename, filename

        if uuid is None:
            filepath = self.path/FILES_FOLDER/filename
            filepath.parent.mkdir(exist_ok=True)
        else:
            assert 'w' not in mode, mode
            assert 'a' not in mode, mode
            filepath = Path(self.parent_folder)/uuid/FILES_FOLDER/filename
            
            if not filepath.exists():
                raise FileNotFoundError("File '{}' doesn't exist.".format(str(filepath)))
            
            other_experiment_metadata_json = utils.load_json(str(Path(self.parent_folder)/uuid/METADATA_JSON_FILENAME))
            if other_experiment_metadata_json['status'] == 'running':
                raise ValueError("Loading from a running experiment is not allowed. Other experiment's UUID: {}".format(uuid))

            with utils.UpdateJsonFile(str(self.path/METADATA_JSON_FILENAME)) as metadata:
                if uuid not in metadata['fileDependencies']:
                    metadata['fileDependencies'][uuid] = []

                if filename not in metadata['fileDependencies'][uuid]:
                    metadata['fileDependencies'][uuid].append(filename)

        return open(str(filepath), mode)


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
    utils.copy_source_code(source_path='.', target_path=path/c.SOURCE_CODE_FOLDER)


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
        'parameters': {},
        'scalars': {},
        'fileDependencies': {},
        'notes': '',
        'osVersion': '{} {}'.format(platform.system(), platform.release()),
        'exceptionType': None,
        'exceptionValue': None,
        'title': '',
        'pid': os.getpid(),
    }   

    utils.dump_json(metadata, str(path/METADATA_JSON_FILENAME))


def create_pip_freeze_file(path):
    installed_packages_list = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8').split('\n')
    installed_packages_list = sorted(installed_packages_list)

    with open(str(path/PACKAGES_FILENAME), 'w') as fp:
        fp.write('\n'.join(installed_packages_list))


def uuid1_to_datetime(uuid1):
    import datetime
    return datetime.datetime.fromtimestamp((uuid1.time - 0x01b21dd213814000)*100/1e9)    

