from flask import Blueprint, request, jsonify, abort, current_app, send_from_directory
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_identity, get_jwt)
from api.models import Folder, FolderSchema, User, Site, SiteSchema, File, FileSchema
from werkzeug.utils import secure_filename
import os
import pathlib
import shutil
from api.decorators import check_site_permissions

site_endpoint = Blueprint('site', __name__)

@site_endpoint.route("/v1/sites/<id>")
@jwt_required()
@check_site_permissions("id")
def get_site(id):
    """Retrieve information about a specific site
    ---
    tags: [Sites]
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The ID of a site
    responses:
      200:
        description: Information about a site
      404:
        description: Site not found
    """
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
    """Retrieve information about all sites belonging to the user
    ---
    tags: [Sites]
    responses:
      200:
        description: Information about all sites belonging to the user
      404:
        description: User is not a member of any sites
    """
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
    """Retrieve information about all folders in a specific site
    ---
    tags: [Folders]
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The ID of a site
    responses:
      200:
        description: Information about all folders in site
      404:
        description: No folders found in site
    """
    folders_schema = FolderSchema(many=True)
    folders = Folder.query.filter(Folder.site_id==id, Folder.parent_id==None).all()
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
    """Retrieve information about a specific folder
    ---
    tags: [Folders]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: folder_id
        in: path
        type: string
        required: true
        description: The ID of a folder
    responses:
      200:
        description: Information about the specified folder
      404:
        description: Folder not found
    """
    folders_schema = FolderSchema()
    folders = Folder.query.filter(Folder.id==folder_id, Folder.site_id==site_id).first()
    if folders:
        return jsonify(folders_schema.dump(folders))
    else:
        return jsonify({
            "error": "Not found",
            "message": "Folder not found"
        }), 404

@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>", methods=["PATCH"])
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>", methods=["PATCH"])
@jwt_required()
@check_site_permissions("site_id")
def edit_file(site_id, file_id, folder_id=None):
    """Change information about a file
    ---
    tags: [Files]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: file_id
        in: path
        type: string
        required: true
        description: The ID of a file
      - name: folder_id
        in: path
        type: string
        required: false
        description: The ID of a folder
      - name: name
        in: body
        type: string
        required: false
        description: The ID of a folder
    responses:
      200:
        description: File information changed successfully
      400:
        description: Returns if body is empty
      404:
        description: File not found
    """
    file_schema = FileSchema()
    files = File.query.filter(File.id==file_id, File.site_id==site_id, File.folder_id==folder_id, File.deleted==False).first()
    if files:
        if request.json:
            if "name" in request.json:
                ext = pathlib.Path(request.json["name"]).suffix
                if ext:
                    if ext != files.ext:
                        os.rename(os.path.join(current_app.config["DATA_FOLDER"], site_id, str(files.id + files.ext)),
                                os.path.join(current_app.config["DATA_FOLDER"], site_id, str(files.id + ext)))
                        files.ext = ext
                    files.name = request.json["name"]
                else:
                    files.name = request.json["name"] + files.ext
            files.save_to_db()
            return jsonify({"message": "File updated"}), 200
        else:
            return jsonify({
                "error": "Bad request",
                "message": "name not given"
            }), 400
    else:
        return jsonify({
            "error": "Not found",
            "message": "File not found"
        }), 404
@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>", methods=["DELETE"])
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>", methods=["DELETE"])
@jwt_required()
@check_site_permissions("site_id")
def remove_file(site_id, file_id, folder_id=None):
    """Remove specific file
    ---
    tags: [Files]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: file_id
        in: path
        type: string
        required: true
        description: The ID of a file
      - name: folder_id
        in: path
        type: string
        required: false
        description: The ID of a folder
    responses:
      200:
        description: File removed successfully
      404:
        description: File not found
      500:
        description: Unkown error occurred while trying to delete file
    """
    file_schema = FileSchema()
    files = File.query.filter(File.id==file_id, File.site_id==site_id, File.folder_id==folder_id, File.deleted==False).first()
    if files:
        try:
            files.deleted = True
            files.save_to_db()

            trash_path = os.path.join(current_app.config["DATA_FOLDER"], site_id, ".trash")
            if not os.path.exists(trash_path):
                os.makedirs(trash_path)
            
            shutil.move(os.path.join(current_app.config["DATA_FOLDER"], site_id, str(files.id + files.ext)), trash_path)

            return jsonify({"message": "File deleted"})
        except:
            return jsonify({
                "error": "Unknown error",
                "message": "Unkown error occurred"
            }), 500
    else:
        return jsonify({
            "error": "Not found",
            "message": "File not found"
        }), 404

@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>")
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>")
@site_endpoint.route("/v1/sites/<site_id>/files/<file_id>.<ext>")
@site_endpoint.route("/v1/sites/<site_id>/folders/<folder_id>/files/<file_id>.<ext>")
@jwt_required()
@check_site_permissions("site_id")
def get_file(site_id, file_id, folder_id=None, ext=None):
    """Retrieve information or contents of a file
    ---
    tags: [Files]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: file_id
        in: path
        type: string
        required: true
        description: The ID of a file
      - name: folder_id
        in: path
        type: string
        required: false
        description: The ID of a folder
      - name: ext
        in: path
        type: string
        required: false
        description: The file extension  
    responses:
      200:
        description: Return information about the file. If ext is present it will deliver the file content instead.
      404:
        description: File not found
    """

    file_schema = FileSchema()
    files = File.query.filter(File.id==file_id, File.site_id==site_id, File.folder_id==folder_id, File.deleted==False).first()
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
    """Retrieve information about all files in site and/or folder
    ---
    tags: [Files]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: folder_id
        in: path
        type: string
        required: false
        description: The ID of a folder 
    responses:
      200:
        description: Return information about all files in site and/or folder
      404:
        description: No files found in site
    """
    file_schema = FileSchema(many=True)
    files = File.query.filter(File.site_id==site_id, File.folder_id==folder_id, File.deleted==False).all()
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
    """Create a new folder
    ---
    tags: [Folders]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: The ID of a site
      - name: folder_id
        in: path
        type: string
        required: false
        description: The ID of a folder
      - name: name
        in: body
        type: string
        required: true
        description: Name of the folder 
    responses:
      201:
        description: Returns successful message and information about the resource created
      400:
        description: name not given in body
      500:
        description: Unkown error occurred while trying to create new folder  
    """
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
    """Create a new site
    ---
    tags: [Sites]
    parameters:
      - name: name
        in: body
        type: string
        required: true
        description: Name of the site 
    responses:
      201:
        description: Returns successful message and information about the resource created
      400:
        description: name not given in body
      500:
        description: Server error, could not generate unique ID key  
    """
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
    """Upload file
    ---
    tags: [Files]
    parameters:
      - name: site_id
        in: path
        type: string
        required: true
        description: ID of the site
      - name: folder_id
        in: path
        type: string
        required: false
        description: ID of a folder 
      - name: file
        in: formData
        type: file
        required: true
        description: FormData of file 
    responses:
      201:
        description: Returns successful message and information about the resource created
      400:
        description: file not given in body
      400:
        description: file is empty
      500:
        description: Unknown error occurred while saving file  
    """
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