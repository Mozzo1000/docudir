from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, fields
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
import shortuuid

db = SQLAlchemy()
ma = Marshmallow()

user_sites = db.Table("user_sites", 
                        db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
                        db.Column("site_id", UUID(as_uuid=True), db.ForeignKey("sites.id")),
                        db.Column("permission", db.String, default="owner"))

class File(db.Model):
    __tablename__ = "files"
    id = db.Column(db.String, primary_key=True, default=shortuuid.uuid)
    name = db.Column(db.String, nullable=False)
    ext = db.Column(db.String)
    mimetype = db.Column(db.String)
    size = db.Column(db.Integer)
    site_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sites.id"), nullable=False)
    folder_id = db.Column(db.String, db.ForeignKey("folders.id"), nullable=True)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class FileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = File
        
class Folder(db.Model):
    __tablename__ = "folders"
    id = db.Column(db.String, primary_key=True, default=shortuuid.uuid)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.String, db.ForeignKey("folders.id"))
    children = db.relationship("Folder", backref=db.backref("parent", remote_side=[id]))
    site_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sites.id"), nullable=False)
    files = db.relationship("File")
    

class FolderSchema(ma.SQLAlchemyAutoSchema):
    children = ma.Nested('FolderSchema', many=True)
    file_count = ma.Method("calculate_file_count")
    
    def calculate_file_count(self, obj):
        if obj:
            return len(obj.files)
    
    class Meta:
        model = Folder
        include_fk = True

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default="user")
    status = db.Column(db.String, default="active")

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @staticmethod
    def generate_hash(password):
        return generate_password_hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return check_password_hash(hash, password)

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ("id", "name", "email", "role", "status")

class Site(db.Model):
    __tablename__ = "sites"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    members = db.relationship("User", secondary="user_sites", backref="sites")
    folders = db.relationship("Folder")

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class SiteSchema(ma.SQLAlchemySchema):
    id = ma.auto_field()
    name = ma.auto_field()
    folder_count = ma.Method("calculate_folder_count")
    

    def calculate_folder_count(self, obj):
        if obj:
            return len(obj.folders)
    class Meta:
        model = Site

class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)