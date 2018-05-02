import attr
import json
import datetime


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
