from flask import Flask
from models.db import init_db
from controllers.routes import main

app = Flask(__name__)
app.secret_key = 'devops_secret_key_2024'
app.register_blueprint(main)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)