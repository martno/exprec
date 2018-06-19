from flask import Flask, send_from_directory, request, jsonify
from pathlib import Path
import json
import shutil
import os

from exprec import table_creation
from exprec import experiment_creation
from exprec import compare_creation
from exprec import constants as c
from exprec import utils
from exprec import html_utils


def dashboard(host=None, port=None):
    app = Flask(__name__)

    @app.route('/')
    def index():
        return send_from_directory('', 'index.html')

    @app.route('/js/<path:path>')
    def send_js(path):
        return send_from_directory('js', path)

    @app.route('/css/<path:path>')
    def send_css(path):
        return send_from_directory('css', path)
    
    @app.route('/experiment-table', methods=['POST'])
    def get_main():
        filters = request.json
        path = Path(c.DEFAULT_PARENT_FOLDER)

        uuids = utils.get_uuids(path)
        table = table_creation.create_table_from_uuids(uuids, path, filters)
        return table

    @app.route('/alltags', methods=['GET'])
    def alltags():
        path = Path(c.DEFAULT_PARENT_FOLDER)
        uuids = utils.get_uuids(path)
        all_tags = utils.get_all_tags(uuids)

        return jsonify(all_tags)

    @app.route('/experiment/<id>', methods=['GET', 'DELETE'])
    def experiment(id):
        if request.method == 'GET':
            return experiment_creation.create_experiment_div(id)

        elif request.method == 'DELETE':
            experiment_path = str(Path(c.DEFAULT_PARENT_FOLDER)/id)
            shutil.rmtree(experiment_path)
            return id

        else:
            raise ValueError('Unknown method: ' + request.method)
        
        return id

    @app.route('/deletefiles/<id>', methods=['GET'])
    def deletefiles(id):
        experiment_files_path = Path(c.DEFAULT_PARENT_FOLDER)/id/'files'
        for path in experiment_files_path.glob('*'):
            if path.is_dir():
                shutil.rmtree(str(path))
            elif path.is_file():
                os.remove(str(path))
        
        return id

    @app.route('/save-text/<id>/<text_id>', methods=['POST'])
    def save_text(id, text_id):
        if text_id not in ('title', 'description', 'conclusion'):
            raise ValueError('Invalid text_id: ' + text_id)

        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/id/c.METADATA_JSON_FILENAME

        with utils.UpdateJsonFile(str(experiment_json_path)) as experiment_json:
            experiment_json[text_id] = request.json
        
        return id

    @app.route('/compare-experiments', methods=['POST'])
    def compare_experiments():
        experiment_ids = request.json
        return jsonify(compare_creation.compare_experiments(experiment_ids))

    @app.route('/restore-source-code/<id>')
    def restore_source_code(id):
        utils.restore_source_code(id)
        return id

    @app.route('/get-code/<id>', methods=['POST'])
    def get_code(id):
        code_path = Path(c.DEFAULT_PARENT_FOLDER)/id/request.json
        assert code_path.exists(), code_path

        if code_path.is_dir():
            return ''

        return jsonify(experiment_creation.load_code(code_path))

    @app.route('/add_tags/<id>', methods=['POST'])
    def add_tags(id):
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/id/c.METADATA_JSON_FILENAME

        with utils.UpdateJsonFile(str(experiment_json_path)) as experiment_json:
            for tag in request.json:
                if tag not in experiment_json['tags']:
                    experiment_json['tags'].append(tag)
        
        return id

    @app.route('/remove_tags/<id>', methods=['POST'])
    def remove_tags(id):
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/id/c.METADATA_JSON_FILENAME

        tags_to_remove = request.json

        with utils.UpdateJsonFile(str(experiment_json_path)) as experiment_json:
            tags = experiment_json['tags']
            experiment_json['tags'] = list(set(tags) - set(tags_to_remove))
        
        return id

    app.run(host=host, port=port, debug=True)
