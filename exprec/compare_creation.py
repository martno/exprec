import subprocess
from pathlib import Path
import collections

from exprec import constants as c
from exprec import html_utils


def compare_experiments(uuids):
    html = '<button class="btn btn-primary button-go-back" style="width: 61px;"><i class="fas fa-arrow-left"></i></button>'
    html += '<hr>'

    content_by_tab_name = collections.OrderedDict()

    if len(uuids) == 1:
        diff_html, diff_string = get_experiment_diff_with_local(uuids[0])
        content_by_tab_name[html_utils.icon_title('code', 'Diff')] = diff_html
    elif len(uuids) == 2:
        diff_html, diff_string = get_experiments_diff(*uuids)
        content_by_tab_name[html_utils.icon_title('code', 'Diff')] = diff_html
    else:
        diff_string = None

    content_by_tab_name[html_utils.icon_title('chart-bar', 'Parameters')] = html_utils.create_parameters(uuids)
    content_by_tab_name[html_utils.icon_title('chart-area', 'Charts')] = html_utils.create_charts(uuids)

    html += html_utils.create_tabs(content_by_tab_name, tabs_id='compare-tabs')

    return {
        'html': html,
        'diffString': diff_string,
    }


def get_experiment_diff_with_local(uuid):
    local_path = '.'
    uuid_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid/'src')

    return create_compare('local', html_utils.circle_with_short_uuid(uuid), local_path, uuid_source_path)


def get_experiments_diff(uuid1, uuid2):
    uuid1_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid1/'src')
    uuid2_source_path = str(Path(c.DEFAULT_PARENT_FOLDER)/uuid2/'src')

    return create_compare(html_utils.circle_with_short_uuid(uuid1), 
        html_utils.circle_with_short_uuid(uuid2), uuid1_source_path, uuid2_source_path)


def create_compare(source1_name, source2_name, source1_path, source2_path):
    html = """
    <div>
        <h5>{source1_name} <i class="material-icons">compare_arrows</i> {source2_name}</h5>

        <div id="diff-div"></div>
    </div>
    """.format(source1_name=source1_name, source2_name=source2_name)

    command = 'diff --recursive --unified --new-file {} {}'.format(source1_path, source2_path)
    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    diff_string = output.stdout.read().decode('utf-8')

    if not diff_string:
        # This is required, or Diff2Html will raise a warning. 
        diff_string = 'diff -ru {} {}'.format(source1_path, source2_path)

    return html, diff_string
