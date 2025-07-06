# if you later decide to use Flask-SQLAlchemy:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

class SunflowerPhoto:
    """
    Placeholder for a future ORM-backed model.
    Currently just describes the data shape.
    """
    def __init__(self, filename, timestamp, url):
        self.filename = filename
        self.timestamp = timestamp
        self.url = url

    def __repr__(self):
        return f"<SunflowerPhoto {self.filename}>"
