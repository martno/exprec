import subprocess
from pathlib import Path

import constants as c


def create_compare(uuid1, uuid2):
    html = """
    <div>
        <button class="btn btn-primary button-go-back" style="width: 61px;"><i class="fas fa-arrow-left"></i></button>
        <hr>
        <h6>{uuid1} <i class="fas fa-exchange-alt"></i> {uuid2}</h6>

        <div id="diff-div"></div>
    </div>
    """.format(uuid1=uuid1, uuid2=uuid2)

    uuid1_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid1/'src')
    uuid2_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid2/'src')
    command = 'diff -u {} {}'.format(uuid1_source_path, uuid2_source_path)
    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    diff_string = output.stdout.read().decode('utf-8')

    return {
        "html": html,
        "diffString": diff_string,
    }

