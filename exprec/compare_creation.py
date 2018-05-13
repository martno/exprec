import subprocess
from pathlib import Path

from exprec import constants as c


def compare_experiments(uuid1, uuid2):
    uuid1_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid1/'src')
    uuid2_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid2/'src')

    return create_compare(uuid1, uuid2, uuid1_source_path, uuid2_source_path)


def compare_with_local(uuid):
    local_path = '.'
    uuid_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid/'src')

    return create_compare('local', uuid, local_path, uuid_source_path)


def create_compare(source1_name, source2_name, source1_path, source2_path):
    html = """
    <div>
        <button class="btn btn-primary button-go-back" style="width: 61px;"><i class="fas fa-arrow-left"></i></button>
        <hr>
        <h5>{source1_name} <i class="fas fa-exchange-alt"></i> {source2_name}</h5>

        <div id="diff-div"></div>
    </div>
    """.format(source1_name=source1_name, source2_name=source2_name)

    command = 'diff -u {} {}'.format(source1_path, source2_path)
    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    diff_string = output.stdout.read().decode('utf-8')

    return {
        "html": html,
        "diffString": diff_string,
    }

