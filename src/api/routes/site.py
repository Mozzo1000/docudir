from flask import Blueprint, request, jsonify, abort, current_app, send_from_directory
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_identity, get_jwt)
from api.models import Folder, FolderSchema, User, Site, SiteSchema, File, FileSchema
from werkzeug.utils import secure_filename
import os
import pathlib
from api.decorators import check_site_permissions

site_endpoint = Blueprint('site', __name__)

@site_endpoint.route("/v1/sites/<id>")
@jwt_required()
@check_site_permissions("id")
def get_site(id):
    sites_schema = SiteSchema()
    site = Site.query.filter(Site.id==id).first()
    if site:
        return jsonify(sites_schema.dump(site))
    else:
        return jsonify({
            "error": "Not found",
            "message": "Site not found"
        }), 404

@site_endpoint.route("/v1/sites")
@jwt_required()
def get_sites():
    sites_schema = SiteSchema(many=True)
    current_user = User.find_by_email(get_jwt_identity())
    sites = Site.query.filter(Site.members.any(id=current_user.id)).all()
    if sites:
        return jsonify(sites_schema.dump(sites))
    else:
        return jsonify({
            "error": "Not found",
            "message": "You are not a member of any sites"
        }), 404

@site_endpoint.route("/v1/sites/<id>/folders")
@jwt_required()
@check_site_permissions("id")
def get_folders_in_site(id):
    folders_schema = FolderSchema()
    folders = Folder.query.filter(Folder.site_id==id).first()
    if folders:
        return jsonify(folders_schema.dump(folders))
    else:
        return jsonify({
            "error": "Not found",
            "message": "No folders in site"
        }), 404


@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>")
@jwt_required()
@check_site_permissions("site_id")
def get_folder_by_id(site_id, folder_id):
    folders_schema = FolderSchema()
    folders = Folder.query.filter(Folder.id==folder_id, Folder.site_id==site_id).first()
    if folders:
        return jsonify(folders_schema.dump(folders))
    else:
        return jsonify({
            "error": "Not found",
            "message": "Folder not found"
        }), 404

@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>")
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>")
@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>.<ext>")
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>.<ext>")
@jwt_required()
@check_site_permissions("site_id")
def get_file(site_id, file_id, folder_id=None, ext=None):
    file_schema = FileSchema()
    files = File.query.filter(File.id==file_id, File.site_id==site_id, File.folder_id==folder_id).first()
    if files:
        if ext == files.ext.replace(".", ""):
            return send_from_directory(os.path.join(os.getcwd(), current_app.config["DATA_FOLDER"], site_id), str(files.id + files.ext))
        else:
            return jsonify(file_schema.dump(files))
    else:
        return jsonify({
            "error": "Not found",
            "message": "File not found"
        }), 404

@site_endpoint.route("/v1/sites/<site_id>/files")
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files")
@jwt_required()
@check_site_permissions("site_id")
def get_files_(site_id, folder_id=None):
    file_schema = FileSchema(many=True)
    files = File.query.filter(File.site_id==site_id, File.folder_id==folder_id).all()
    if files:
        return jsonify(file_schema.dump(files))
    else:
        return jsonify({
            "error": "Not found",
            "message": "No files in site"
        }), 404

@site_endpoint.route("/v1/sites/<site_id>/folders", methods=["POST"])
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>", methods=["POST"])
@jwt_required()
@check_site_permissions("site_id")
def add_folder(site_id, folder_id=None):
    if not "name" in request.json:
        return jsonify({
            "error": "Bad request",
            "message": "name not given"
        }), 400
    
    try:
        new_folder = Folder(name=request.json["name"], site_id=site_id, parent_id=folder_id)
        new_folder.save_to_db()
        return {
            "message": "New folder created",
            "id": new_folder.id,
            "name": new_folder.name
        }, 201
    except:
        return jsonify({
            "error": "Unknown error",
            "message": "Unkown error occurred"
        }), 500
    

@site_endpoint.route("/v1/sites", methods=["POST"])
@jwt_required()
def add_site():
    if not "name" in request.json:
        return jsonify({
            "error": "Bad request",
            "message": "name not given"
        }), 400
    
    current_user = User.find_by_email(get_jwt_identity())
    new_site = Site(name=request.json["name"])
    new_site.members.append(current_user)
    try:
        new_site.save_to_db()
        return jsonify({'message': 'New site created'}), 201
    except IntegrityError:
        return jsonify({
            "error": "Server error",
            "message": "Could not generate a unique ID, try again later."
        }), 500

@site_endpoint.route("/v1/sites/<site_id>/files", methods=["POST"])
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files", methods=["POST"])
@jwt_required()
def add_file(site_id, folder_id=None):
    if "file" not in request.files:
        return jsonify({
            "error": "Bad request",
            "message": "file not given"
        }), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({
            "error": "Bad request",
            "message": "file is empty"
        }), 400
    if file:
        filepath = os.path.join(current_app.config["DATA_FOLDER"], site_id)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        
        file_extension = pathlib.Path(file.filename).suffix
        try:
            new_file = File(name=file.filename, site_id=site_id, mimetype=file.mimetype, ext=file_extension, folder_id=folder_id)
            new_file.save_to_db()
            file.save(os.path.join(filepath, str(new_file.id + file_extension)))
            return {
                "message": "Upload complete",
                "id": new_file.id,
                "name": new_file.name
            }, 201
        except:
            return jsonify({
                "error": "Unknown error",
                "message": "Unkown error occurred"
            }), 500