from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_identity, get_jwt)
from api.models import User, RevokedTokenModel

auth_endpoint = Blueprint('auth', __name__)

@auth_endpoint.route("/v1/auth/register", methods=["POST"])
def register():
    """Register account
    ---
    tags: [Auth]
    parameters:
      - name: email
        in: body
        type: string
        required: true
        description: Email
      - name: name
        in: body
        type: string
        required: true
        description: Name of account 
      - name: password
        in: body
        type: string
        required: true
        description: Password 
    responses:
      201:
        description: Returns successful message and information about the resource created
      422:
        description: Returns if email, password and name is not given in body
      409:
        description: Email already in use by another account
      500:
        description: Unknown error occurred while creating account
    """
    if not "email" or not "password" or not "name" in request.json:
        abort(422)
    if User.find_by_email(request.json["email"]):
        return jsonify({'message': 'Email {} is already in use'.format(request.json["email"])}), 409
    
    new_user = User(email=request.json["email"], password=User.generate_hash(request.json["password"]), name=request.json["name"])

    try:
        new_user.save_to_db()
        access_token = create_access_token(identity=request.json["email"])
        refresh_token = create_refresh_token(identity=request.json["email"])
        return jsonify({'message': 'Account with email {} was created'.format(request.json["email"]), 'access_token': access_token, 'refresh_token': refresh_token}), 201

    except:
        return jsonify({'message': 'Something went wrong'}), 500

@auth_endpoint.route("/v1/auth/login", methods=["POST"])
def login():
    """Register account
    ---
    tags: [Auth]
    parameters:
      - name: email
        in: body
        type: string
        required: true
        description: Email
      - name: password
        in: body
        type: string
        required: true
        description: Password 
    responses:
      201:
        description: Logged in successfully
      422:
        description: Returns if email and password is not given in body
      403:
        description: Returns if account has been inactivated
      404:
        description: Wrong email or password
      500:
        description: Unknown error occurred while creating account
    """
    if not "email" or not "password" in request.json:
        abort(422)
    current_user = User.find_by_email(request.json["email"])
    if not current_user:
        return jsonify({'message': 'Wrong email or password, please try again.'}), 404

    if User.verify_hash(request.json["password"], current_user.password) and current_user.status == "active":
        access_token = create_access_token(identity=request.json['email'], additional_claims={"role": current_user.role})
        refresh_token = create_refresh_token(identity=request.json['email'])

        return jsonify({'message': 'Logged in', 'email': current_user.email, 'name': current_user.name,
                        'access_token': access_token, 'refresh_token': refresh_token, 
                        'role': current_user.role}), 201
    elif current_user.status == "inactive":
        return jsonify({'message': 'Account has been inactivated, contact administrator for more information.'}), 403
    else:
        return jsonify({'message': 'Wrong username or password, please try again.'}), 401

@auth_endpoint.route('/v1/auth/refresh', methods=['POST'])
def token_refresh():
    """Refresh token
    ---
    tags: [Auth]
    responses:
      201:
        description: Token refreshed
    """
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 201

@auth_endpoint.route('/v1/auth/logout/access', methods=['POST'])
@jwt_required()
def user_logout_access():
    """Revoke access token
    ---
    tags: [Auth]
    responses:
      201:
        description: Access token revoked
      500:
        description: Unkown error occurred while revoking token
    """
    jti = get_jwt()["jti"]
    try:
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.add()
        return jsonify({'message': 'Access token has been revoked'}), 201
    except:
        return jsonify({'message': 'Something went wrong'}), 500


@auth_endpoint.route('/v1/auth/logout/refresh', methods=['POST'])
@jwt_required(refresh=True)
def user_logout_refresh():
    """Revoke refresh token
    ---
    tags: [Auth]
    responses:
      201:
        description: Refresh token revoked
      500:
        description: Unkown error occurred while revoking token
    """
    jti = get_jwt()["jti"]
    try:
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.add()
        return jsonify({'message': 'Refresh token has been revoked'}), 201
    except:
        return jsonify({'message': 'Something went wrong'}), 500