from flask import Flask, send_from_directory, request, jsonify
from yattag import Doc
from pathlib import Path
import json
import shutil

import table_creation
import experiment_creation
import constants as c
import utils
import html_utils


def main():
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

    @app.route('/add_tags/<id>', methods=['POST'])
    def add_tags(id):
        experiment_json_path = Path(c.DEFAULT_PARENT_FOLDER)/id/c.METADATA_JSON_FILENAME

        with utils.UpdateJsonFile(str(experiment_json_path)) as experiment_json:
            for tag in request.json:
                if tag not in experiment_json['tags']:
                    experiment_json['tags'].append(tag)
        
        return json.dumps(experiment_json['tags'])

    app.run(debug=True)




if __name__ == "__main__":
    main()
