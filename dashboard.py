from flask import Flask, send_from_directory
from yattag import Doc
from pathlib import Path

import table_creation
import experiment_creation
import constants as c


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
    
    @app.route('/main')
    def get_main():
        path = Path(c.DEFAULT_PARENT_FOLDER)

        uuids = get_uuids(path)
        table = table_creation.create_table_from_uuids(uuids, path)
        return table
    
    @app.route('/experiment/<id>')
    def experiment(id):
        return experiment_creation.create_experiment_div(id)

    app.run(debug=True)


def get_uuids(path):
    metadata_json_paths = path.glob('*/' + c.METADATA_JSON_FILENAME)
    return [json_path.parent.parts[-1] for json_path in metadata_json_paths]


if __name__ == "__main__":
    main()
