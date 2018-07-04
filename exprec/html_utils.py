from pathlib import Path
import colorhash
import pandas as pd
from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.models import HoverTool
import bokeh.colors
from jinja2 import Template

from exprec import constants as c
from exprec import utils


ICON_BY_STATUS = {
    'running': 'fas fa-play text-primary',
    'succeeded': 'fas fa-check text-success',
    'failed': 'fas fa-times text-danger',
}

FIGURE_WIDTH = 600
FIGURE_HEIGHT = 400

N_A = '<div style="color: #B2B2B2;">N/A</div>'

N_SIGNIFICANT_DIGITS = 4


def monospace(string):
    return "<pre>{}</pre>".format(string)
    # return """<p style="font-family: 'Lucida Console', monospace;">{}<p>""".format(string)


def badge(string):
    return "<span class='badge badge-primary'>{}</span>".format(string)


def icon(icon_name):
    return "<i class='{}'></i>".format(icon_name)


def fa_icon(icon_name):
    return icon('fas fa-' + icon_name)


def m_icon(icon_name):
    return '<i class="material-icons">{}</i>'.format(icon_name)


def get_status_icon_tag(status):
    return icon(ICON_BY_STATUS[status])


def icon_title(icon_name, title):
    return fa_icon(icon_name) + ' ' + title


def create_table(columns, item_by_column_list, id, attrs=None, classes_by_column=None, extra_ths=()):
    if attrs is None:
        attrs = [{} for _ in range(len(columns))]
    assert len(attrs) == len(columns), (len(attrs), len(columns))

    if classes_by_column is None:
        classes_by_column = {column: [] for column in columns}

    item_by_column_list = [
        {column: item if item is not None else N_A for column, item in item_by_column.items()}
        for item_by_column in item_by_column_list
    ]

    temp_attrs = []
    for attr in attrs:
        attr_string = ' '.join('{}="{}"'.format(key, value) for key, value in attr)
        temp_attrs.append(attr_string)
    attrs = temp_attrs

    template = Template('''
    <small>
        <table class="table display" id={{ id }}>
            <thead>
                <tr>
                    {% for name, colspan in extra_ths %}
                        {% if colspan > 0 %}
                            <th colspan={{ colspan }}>
                                {{ name }}
                            </th>
                        {% endif %}
                    {% endfor %}
                </tr>
                <tr>
                    {% for column in columns %}
                        <th scope="col" class="{{ ' '.join(classes_by_column[column]) }}">
                            {{ column }}
                        </th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for item_by_column in item_by_column_list %}
                    <tr>
                        {% for column, attr in zip(columns, attrs) %}
                            <td class="{{ ' '.join(classes_by_column[column]) }}" {{ attr }}>
                                {{ item_by_column[column] }}
                            </td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </small>
    ''')

    return template.render(id=id, extra_ths=extra_ths, columns=columns, item_by_column_list=item_by_column_list, 
        attrs=attrs, classes_by_column=classes_by_column, zip=zip)


def create_tabs(content_by_tab_name, tabs_id):
    template = Template('''
    <ul class="nav nav-pills" id={{ tabs_id }} role="tablist">
        {% for tab_name in content_by_tab_name.keys() %}
            <li class="nav-item">
                <a href="#{{ tabs_id }}--tab-{{ loop.index0 }}" class={% if loop.first %}"nav-link active"{% else %}"nav-link"{% endif %} role="tab" data-toggle="pill">
                    {{ tab_name }}
                </a>
            </li>
        {% endfor %}
    </ul>
    <div class="tab-content">
        {% for content in content_by_tab_name.values() %}
            <div class={% if loop.first %}"tab-pane active"{% else %}"tab-pane"{% endif %} id="{{ tabs_id }}--tab-{{ loop.index0 }}" role="tabpanel">
                {{ content }}
            </div>
        {% endfor %}
    </div>
    ''')

    return template.render(tabs_id=tabs_id, content_by_tab_name=content_by_tab_name)


def code(code_string, language=None):
    if language is None:
        return "<pre><code>{}</code></pre>".format(code_string)
    
    return '<pre><code class="{}">{}</code></pre>'.format(language, code_string)


def margin(html, amount='10px'):
    return '<div style="margin: {}">{}</div>'.format(amount, html)


def color_circle(string):
    hex_color = colorhash.ColorHash(string).hex
    circle = "<i class='fas fa-circle' style='color:{}'></i>".format(hex_color)
    return circle


def color_circle_and_string(string):
    return '{} {}'.format(color_circle(string), string)


def create_charts(uuids):
    paths = [Path(c.DEFAULT_PARENT_FOLDER)/uuid for uuid in uuids]

    html = ''
    for uuid in uuids:
        experiment_json = utils.load_experiment_json(uuid)
        title = experiment_json['title']
        
        if title:
            html += '{} {} - {}\n<br>'.format(color_circle(uuid), utils.get_short_uuid(uuid), title)
        else:
            html += '{} {}\n<br>'.format(color_circle(uuid), utils.get_short_uuid(uuid))

    scalar_names = get_all_scalar_names(paths)

    hover = HoverTool(
        tooltips=[
            ('step', '@x'),
            ('value', '@y'),
        ],
        mode='vline'
    )

    plots = []

    for scalar_name in scalar_names:
        plot = figure(
            tools=[hover, 'reset', 'pan', 'wheel_zoom', 'box_zoom'], 
            title=scalar_name,
            x_axis_label='Step',
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
        )

        for uuid, path in zip(uuids, paths):
            scalar_file = path / c.SCALARS_FOLDER / '{}.csv'.format(scalar_name)

            if scalar_file.is_file():
                df = pd.read_csv(scalar_file)
                
                source = ColumnDataSource(data={
                    'x': df['step'],
                    'y': df['value'],
                })

                color = colorhash.ColorHash(uuid).rgb

                plot.line('x', 'y', 
                    source=source, 
                    line_color=bokeh.colors.RGB(*color),
                    legend=utils.get_short_uuid(uuid),
                    line_width=2,
                )

        plot.legend.location = "top_left"
        plot.legend.click_policy = "hide"

        script, div = components(plot)
        plots.append('{}\n{}'.format(script, div))

    return html + '\n\n'.join(plots)


def get_all_scalar_names(paths):
    scalar_names = set()
    for path in paths:
        scalars_folder = path / c.SCALARS_FOLDER

        scalar_paths = scalars_folder.glob('*.csv')
        scalar_names.update(scalar_path.stem for scalar_path in scalar_paths)
    
    scalar_names = sorted(list(scalar_names))

    return scalar_names


def create_parameters(uuids):
    experiment_json_by_uuid = {uuid: utils.load_experiment_json(uuid) for uuid in uuids}

    params_by_uuid = {uuid: experiment_json['parameters'] for uuid, experiment_json in experiment_json_by_uuid.items()}
    params_by_uuid = {utils.get_short_uuid(uuid): params for uuid, params in params_by_uuid.items()}

    all_params = set()
    for params in params_by_uuid.values():
        all_params.update(params)
    all_params = sorted(list(all_params))

    rows = []
    for param in all_params:
        row = {'Parameter': param}
        for uuid, params in params_by_uuid.items():
            value = params[param] if param in params else None
            if type(value) in (int, float):
                value = str(utils.round_to_significant_digits(value, N_SIGNIFICANT_DIGITS))
            row[uuid] = value
        rows.append(row)
    
    # The last column has width 100%:
    attrs = [[]]*len(uuids) + [[('style', 'width: 100%;')]]

    return create_table(['Parameter', *params_by_uuid.keys()], rows, id='parameter-table', attrs=attrs)


def circle_with_short_uuid(uuid):
    return '{} {}'.format(color_circle(uuid), utils.get_short_uuid(uuid))


def same_line(html):
    return '<div style="white-space: nowrap">{}</div>'.format(html)
