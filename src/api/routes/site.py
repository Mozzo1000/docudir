from flask import Blueprint, request, jsonify, abort, current_app
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_identity, get_jwt)
from api.models import Folder, FolderSchema, User, Site, SiteSchema, File, FileSchema
from werkzeug.utils import secure_filename
import os
import pathlib

site_endpoint = Blueprint('site', __name__)

@site_endpoint.route("/v1/sites/<id>")
@jwt_required()
def get_site(id):
    sites_schema = SiteSchema()
    current_user = User.find_by_email(get_jwt_identity())
    site = Site.query.filter(Site.id==id, Site.members.any(id=current_user.id)).first()
    if site:
        return jsonify(sites_schema.dump(site))
    else:
        return jsonify({
            "error": "Not found",
            "message": "Site not found"
        }), 404

@site_endpoint.route("/v1/sites/<id>/folders")
@jwt_required()
def get_folders_in_site(id):
    folders_schema = FolderSchema()
    current_user = User.find_by_email(get_jwt_identity())
    allowed_site = Site.query.filter(Site.id==id, Site.members.any(id=current_user.id)).first() is not None
    if allowed_site:
        folders = Folder.query.filter(Folder.site_id==id).first()
        return jsonify(folders_schema.dump(folders))
    else:
        return jsonify({
            "error": "Unauthorized access",
            "message": "You do not have access to this site"
        }), 401


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

@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files", methods=["POST"])
@jwt_required()
def add_file_to_folder(site_id, folder_id):
    return upload_file_helper(request.files, site_id, folder_id)

@site_endpoint.route("/v1/sites/<id>/files", methods=["POST"])
@jwt_required()
def add_file(id):
    return upload_file_helper(request.files, id)
    
def upload_file_helper(req_files, site_id, folder_id=None):
    #req_files = flask request.files - required
    #site_id - required
    #folder_id - optional

    if "file" not in req_files:
        return jsonify({
            "error": "Bad request",
            "message": "file not given"
        }), 400

    file = req_files["file"]
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