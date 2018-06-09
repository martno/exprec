from yattag import Doc
import collections
from pathlib import Path
import datetime
import json
import cgi
from PIL import Image
import base64
from io import BytesIO

from exprec import html_utils
from exprec import constants as c
from exprec import utils


def create_experiment_div(uuid):
    path = Path(c.DEFAULT_PARENT_FOLDER)/uuid

    experiment_json = utils.load_json(str(path/c.METADATA_JSON_FILENAME))

    doc, tag, text = Doc().tagtext()
    with tag('div'):
        with tag('button', klass="btn btn-primary button-go-back", style="width: 61px;"):
            doc.asis(html_utils.fa_icon('arrow-left'))
        text(' ')
        with tag('button', klass="btn btn-primary button-restore-source-code", style="width: 61px;"):
            doc.asis(html_utils.fa_icon('file-code'))
        doc.stag('hr')
        with tag('h5'):
            doc.asis(html_utils.get_status_icon_tag(experiment_json['status']))
            text(' ')
            text(uuid)

            doc.asis('<span style="display:inline-block; width: 16px;"></span>')
            text('[{}]'.format(experiment_json['filename']))
            doc.asis('<span style="display:inline-block; width: 16px;"></span>')

            tags = sorted(experiment_json['tags'])
            doc.asis(' '.join([html_utils.badge(tag) for tag in tags]))

        text(experiment_json['title'])
        
        doc.stag('hr')

        content_by_tab_name = collections.OrderedDict()
        content_by_tab_name[html_utils.icon_title('eye', 'Summary')] = create_summary(uuid, path, experiment_json)
        content_by_tab_name[html_utils.icon_title('terminal', 'Output')] = create_output(path)
        content_by_tab_name[html_utils.icon_title('code', 'Code')] = create_code(uuid, path, experiment_json)
        content_by_tab_name[html_utils.icon_title('cube', 'Packages')] = create_packages(path)
        content_by_tab_name[html_utils.icon_title('chart-bar', 'Parameters')] = html_utils.create_parameters([uuid])
        content_by_tab_name[html_utils.icon_title('chart-area', 'Charts')] = html_utils.create_charts([uuid])
        content_by_tab_name[html_utils.icon_title('image', 'Images')] = create_images(path)

        content_by_tab_name = collections.OrderedDict([(key, html_utils.margin(value)) for key, value in content_by_tab_name.items()])

        tabs_html = html_utils.create_tabs(content_by_tab_name, tabs_id='experiment-tabs')

        doc.asis(tabs_html)

    return doc.getvalue()




def create_summary(uuid, path, experiment_json):
    doc, tag, text = Doc().tagtext()

    columns = ['Name', 'Value']

    status = experiment_json['status']

    start = datetime.datetime.strptime(experiment_json['startedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")
    end = None if experiment_json['endedDatetime'] is None else datetime.datetime.strptime(experiment_json['endedDatetime'], "%Y-%m-%dT%H:%M:%S.%f")

    if end is None:
        duration = datetime.datetime.now() - start
    else:
        duration = end - start
    duration = utils.floor_timedelta(duration)

    tags = sorted(experiment_json['tags'])

    parents = get_parents(experiment_json)

    exception = None
    if experiment_json['exceptionType'] is not None:
        exception = '{}: {}'.format(experiment_json['exceptionType'], experiment_json['exceptionValue'])

    items = [
        ('Status', html_utils.get_status_icon_tag(status) + ' ' + status),
        ('ID', html_utils.monospace(uuid)),
        ('Title<br><br><button type="button" class="btn btn-primary btn-xs" data-toggle="modal" data-target="#titleModal">Edit</button>', '<div id="title-div">{}</div>'.format(experiment_json['title'])),
        ('Description<br><br><button type="button" class="btn btn-primary btn-xs" data-toggle="modal" data-target="#descriptionModal">Edit</button>', '<div id="description-div"></div>'),
        ('Conclusion<br><br><button type="button" class="btn btn-primary btn-xs" data-toggle="modal" data-target="#conclusionModal">Edit</button>', '<div id="conclusion-div"></div>'),
        ('Filename', html_utils.color_circle_and_string(experiment_json['filename'])),
        ('Duration', str(duration)),
        ('Start', start.strftime('%Y-%m-%d %H:%M:%S')),
        ('End', end.strftime('%Y-%m-%d %H:%M:%S') if end is not None else None),
        ('Tags', ' '.join([html_utils.badge(tag) for tag in tags])),
        ('Arguments', html_utils.monospace(' '.join(experiment_json['arguments']))),
        ('Name', experiment_json['name']),
        ('File space', utils.get_file_space_representation(str(path/c.FILES_FOLDER))),
        ('Parents', html_utils.monospace(' '.join(parents))),
        ('Exception', html_utils.monospace(exception) if exception is not None else None),
        ('Git commit', html_utils.monospace(html_utils.color_circle_and_string(experiment_json['git']['short'])) if experiment_json['git'] is not None else None),
        ('PID', html_utils.monospace(experiment_json['pid'])),
        ('Python version', experiment_json['pythonVersion']),
        ('OS', experiment_json['osVersion']),
    ]

    item_by_column_list = [{'Name': name, 'Value': value} for name, value in items]

    html = html_utils.create_table(columns, item_by_column_list, id='summary-table', attrs=[[], [('style', 'width: 100%;')]])

    html += create_modal_html(uuid, experiment_json)

    return html


def create_packages(path):
    pip_freeze_path = path/'pip_freeze.txt'

    with pip_freeze_path.open() as fp:
        pip_freeze = fp.read()
    
    return html_utils.monospace(pip_freeze)


def create_code(uuid, path, experiment_json):
    filename = experiment_json['filename']

    tree = create_tree(root=path/'src', path_to_root=Path('src'), selected_path='{}/{}'.format(c.SOURCE_CODE_FOLDER, filename))

    json_string_tree = json.dumps(tree)

    html = """
    <div>
        <div id="jstree-code-div" style="min-width: 200px; display: table-cell;"></div>
        <div id="code-content-div" style="width: 100%; display: table-cell;"></div>
    </div>

    <script>
        $('#jstree-code-div').jstree({
            "types" : {
                "default" : {
                    "icon" : "far fa-folder"
                },
                "file" : {
                    "icon" : "far fa-file"
                }
            },
            "plugins" : [ "types" ],
            'core' : {
                'data' : JSON_TREE
            }
        });

        $('#jstree-code-div').on("changed.jstree", function (e, data) {
            var selected = data.selected[0];
            var promise = postJson('/get-code/UUID', selected);
            promise.done(function(result) {
                $("#code-content-div").html(result);
                highlightAllCode();
            });
        });
    </script>
    """.replace('JSON_TREE', json_string_tree).replace('UUID', uuid)

    return html


def create_tree(root, path_to_root, selected_path=None):
    agg = {
        'text': root.name,
        'id': str(path_to_root),
        'children': [],
        'state': {
            'opened': True,
        }
    }

    sub_dirs = sorted([directory for directory in root.iterdir() if directory.is_dir()])
    for sub_dir in sub_dirs:
        sub_agg = create_tree(sub_dir, path_to_root/sub_dir.name, selected_path)
        agg['children'].append(sub_agg)

    files = sorted([file for file in root.iterdir() if file.is_file()])
    for file in files:
        agg['children'].append({
            'text': file.name,
            'id': str(path_to_root/file.name),
            'type': 'file',
            'state': {
                'selected': str(path_to_root/file.name) == selected_path
            },
        })
    
    return agg


def load_code(code_path):
    with code_path.open() as fp:
        code = fp.read()
    
    code = cgi.escape(code)

    return html_utils.code(code, language='python')


def create_output(path):
    filepath = path/'stdcombined.txt'

    with filepath.open() as fp:
        output = fp.read()
    
    return html_utils.monospace(output)


def create_charts(path):
    scalars_folder = path / c.SCALARS_FOLDER

    if scalars_folder.exists():
        scalar_paths = scalars_folder.glob('*.csv')
    else:
        scalar_paths = []

    hover = HoverTool(
        tooltips=[
            ('step', '@x'),
            ('value', '@y'),
        ],
        mode='vline'
    )

    plots = []
    for scalar_path in sorted(scalar_paths):
        scalar_name = scalar_path.stem

        df = pd.read_csv(scalar_path)

        xs = df['step']
        ys = df['value']
        
        source = ColumnDataSource(data={
            'x': xs,
            'y': ys,
        })

        plot = figure(
            tools=[hover], 
            title=scalar_name,
            x_axis_label='Step',
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
        )
        plot.line('x', 'y', source=source)

        script, div = components(plot)
        plots.append('{}\n{}'.format(script, div))

    return '\n\n'.join(plots)


def get_parents(experiment_json):
    return list(experiment_json['fileDependencies'].keys())


def create_images(path):
    image_by_name = get_image_by_name_map(path)
    
    names = list(image_by_name.keys())

    html = ''

    for name in sorted(names):
        image = image_by_name[name]
        
        image_string = convert_image_to_base64(image)

        html += '<h4>{}</h4>\n'.format(name)
        html += '<img src="data:image/png;base64,{}">\n\n'.format(image_string)
    
    return html


def get_image_by_name_map(path):
    image_parent_path = path/c.IMAGE_FOLDER

    image_by_name = {}

    if image_parent_path.exists():
        image_folder_paths = [image_folder_path for image_folder_path in image_parent_path.iterdir() 
                              if image_folder_path.is_dir()]

        for image_folder_path in image_folder_paths:
            image_ids = [int(image_path.stem) for image_path in image_folder_path.glob('*.png')]
            if not image_ids:
                continue

            max_image_id = max(image_ids)

            image_path = image_folder_path / '{}.png'.format(max_image_id)
            image = Image.open(image_path)

            name = '{} [step: {}]'.format(image_folder_path.name, max_image_id)

            image_by_name[name] = image

    return image_by_name


def convert_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="png")
    image_bytes = base64.b64encode(buffered.getvalue())
    image_string = image_bytes.decode('utf-8')

    return image_string


def create_modal_html(uuid, experiment_json):
    html = """
      <!-- Title Modal -->
      <div class="modal" id="titleModal" tabindex="-1" role="dialog" aria-labelledby="titleModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="titleModalLabel">Title</h5>
            </div>
            <div class="modal-body">
              <input type="text" class="form-control" id="titleTextInput" value='{title}'></textarea>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
              <button type="button" class="btn btn-primary" data-dismiss="modal" onclick="saveTitle('{uuid}')">Save</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Description Modal -->
      <div class="modal" id="descriptionModal" tabindex="-1" role="dialog" aria-labelledby="descriptionModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-" id="ModalLabel">Description</h5>
            </div>
            <div class="modal-body">
              <textarea class="form-control" id="descriptionTextArea" rows="18" style="font-family: monospace;"></textarea>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
              <button type="button" class="btn btn-primary" data-dismiss="modal" onclick="saveDescription('{uuid}')">Save</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Conclusion Modal -->
      <div class="modal" id="conclusionModal" tabindex="-1" role="dialog" aria-labelledby="conclusionModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-conclusion" id="conclusionModalLabel">Conclusion</h5>
            </div>
            <div class="modal-body">
              <textarea class="form-control" id="conclusionTextArea" rows="18" style="font-family: monospace;"></textarea>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
              <button type="button" class="btn btn-primary" data-dismiss="modal" onclick="saveConclusion('{uuid}')">Save</button>
            </div>
          </div>
        </div>
      </div>

      <script>
        var converter = new showdown.Converter();
        $('#descriptionTextArea').text(`{description}`);
        $('#conclusionTextArea').text(`{conclusion}`);
        $('#description-div').html(converter.makeHtml(`{description}`));
        $('#conclusion-div').html(converter.makeHtml(`{conclusion}`));
      </script>
    """.format(
        uuid=uuid, 
        title=experiment_json['title'], 
        description=experiment_json['description'], 
        conclusion=experiment_json['conclusion'],
    )

    return html

