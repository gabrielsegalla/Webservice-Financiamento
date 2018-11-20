# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_marshmallow import Marshmallow
# from flask_cors import CORS
# import os

# app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost/webservice-financiamento'
# CORS(app)
# db = SQLAlchemy(app)
# ma = Marshmallow(app)

# host = "localhost"
# debug = True
# port = 8081

# SQLALCHEMY_ECHO = False

# @manager.command
# def runserver():
#     """Method for run project."""
#     app.run(
#         host=(host),
#         port=int(port),
#         debug=bool(debug)
#     )
