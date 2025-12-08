import os
from flask import Flask, render_template, g
from configparser import ConfigParser
# might not use this function
from database.handler import get_db_connection_for_request
from routes.data_entry import data_entry_bp
from routes.evaluation import evaluation_bp
from routes.querying import querying_bp

def create_app():
    app = Flask(__name__)

    try:
        config = ConfigParser()
        config_path = os.path.join(app.root_path, 'config.txt')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        config.read(config_path)
        app.config['DB_CONFIG'] = dict(config.items('database'))
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        exit(1)

    app.register_blueprint(data_entry_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(querying_bp)

    @app.route('/')
    def index():
        return render_template('index.html') 

    @app.teardown_appcontext
    def close_db_connection(exception):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
