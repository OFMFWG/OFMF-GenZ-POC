#
# Copyright (c) 2017-2021, The Storage Networking Industry Association.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of The Storage Networking Industry Association (SNIA) nor
# the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#  THE POSSIBILITY OF SUCH DAMAGE.
#
#f_connections_api.py

import json, os
import shutil
import requests

import traceback
import logging
import g
import urllib3

from flask import jsonify, request
from flask_restful import Resource
from api_emulator.utils import update_collections_json, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, delete_collection, create_collection, create_agent_path, add_input_body_properties, create_and_patch_agent_object
from .constants import *
from .templates.connections import get_Connections_instance

members =[]
member_ids = []
config = {}
INTERNAL_ERROR = 500

# FabricsConnectionsAPI API
class FabricsConnectionsAPI(Resource):
    def __init__(self, **kwargs):
        logging.info('FabricsConnectionsAPI init called')
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']

    # HTTP GET
    def get(self, fabric, f_connection):
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        return get_json_data (path)

    # HTTP POST
    # - Create the resource (since URI variables are available)
    # - Update the members and members.id lists
    # - Attach the APIs of subordinate resources (do this only once)
    # - Finally, create an instance of the subordiante resources
    def post(self, fabric, f_connection):
        logging.info('FabricsConnectionsAPI POST called')
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection)
        collection_path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')

        # Check if collection exists:
        if not os.path.exists(collection_path):
            FabricsConnectionsCollectionAPI.post (self, fabric)

        if os.path.exists (path):
            resp = 404
            return resp
        try:
            global config
            wildcards = {'f_id':fabric, 'c_id': f_connection, 'rb': g.rest_base}
            config=get_Connections_instance(wildcards)
            config = add_input_body_properties (config)

            # Send commands to Agent:
            agentpath = create_agent_path (g.AGENT, "/redfish/v1/", self.fabrics, fabric, self.f_connections, f_connection)
            logging.info(agentpath)
            agentresponse = requests.post(agentpath, data = config )
            logging.info(agentresponse)

            if agentresponse.status_code == 200:
                # Copy body of response into config:
                config = {}
                # If input body data, then update properties
                if request.data:
                    request_data = json.loads(request.data)
                    # Update the keys of payload in json file.
                    for key, value in request_data.items():
                        config[key] = value

                # Set odata.id and Id to properties for this instance:
                config['@odata.id'] = create_agent_path ("\/", "/redfish/v1/", self.fabrics, fabric, self.f_connections, f_connection)
                config['Id'] = f_connection

                config = create_and_patch_agent_object (config, members, member_ids, path, collection_path)

                # Create Links.Connections in Endpoints (Links.InitiatorEndpoints, Links.TargetEndpoints)

                if 'Links' in config:
                    if 'InitiatorEndpoints' in config['Links']:
                        for ep in config['Links']['InitiatorEndpoints']:
                            # Get endpoint identifier:
                            data = {}
                            endpointPath = ep['@odata.id']
                            epPath = endpointPath.replace ("/redfish/v1/", "Resources/")
                            epPath = create_path(epPath, "index.json")
                            # Create property to patch to endpoint:
                            connectionID = {}
                            connectionID['Links'] = {"Connections": [{ "@odata.id": config.get('@odata.id') }]}
                            # Write additional properties to Endpoint
                            with open(epPath, "r") as data_json:
                                data = json.load(data_json)
                            # Update the keys of payload in json file.
                            data['Links']['Connections'].extend (connectionID['Links']['Connections'])
                            # Write the updated json to file.
                            with open(epPath, 'w') as f:
                                json.dump(data, f, indent=4, sort_keys=True)
                                f.close()

                       # Repeat for TargetEndpoints
                    if 'TargetEndpoints' in config['Links']:
                        for ep in config['Links']['TargetEndpoints']:
                            data = {}
                            # Get endpoint identifier:
                            endpointPath = ep['@odata.id']
                            epPath = endpointPath.replace ("/redfish/v1/", "Resources/")
                            epPath = create_path(epPath, "index.json")
                            # Create property to patch to endpoint:
                            connectionID = {}
                            connectionID['Links'] = {"Connections": [{ "@odata.id": config.get('@odata.id') }]}
                            # Write additional properties to Endpoint
                            with open(epPath, "r") as data_json:
                                data = json.load(data_json)
                            # Update the keys of payload in json file.
                            data['Links']['Connections'].extend (connectionID['Links']['Connections'])
                            # Write the updated json to file.
                            with open(epPath, 'w') as f:
                                json.dump(data, f, indent=4, sort_keys=True)
                                f.close()



                resp = config, 200
            else:
                resp = 404
                return resp

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('FabricsConnectionsAPI POST exit')
        return resp

	# HTTP PATCH
    def patch(self, fabric, f_connection):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        patch_object(path)
        return self.get(fabric, f_connection)

    # HTTP PUT
    def put(self, fabric, f_connection):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, f_connection, 'index.json')
        put_object(path)
        return self.get(fabric, f_connection)

    # HTTP DELETE
    def delete(self, fabric, f_connection):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.fabrics, fabric, self.f_connections, f_connection)
        base_path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        return delete_object(path, base_path)

# Fabrics Connections Collection API
class FabricsConnectionsCollectionAPI(Resource):

    def __init__(self):
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']

    def get(self, fabric):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')
        return get_json_data (path)

    def verify(self, config):
        # TODO: Implement a method to verify that the POST body is valid
        return True,{}

    # HTTP POST Collection
    def post(self, fabric):
        self.root = PATHS['Root']
        self.fabrics = PATHS['Fabrics']['path']
        self.f_connections = PATHS['Fabrics']['f_connection']

        logging.info('FabricsConnectionsCollectionAPI POST called')

        if fabric in members:
            resp = 404
            return resp

        path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        return create_collection (path, 'Connection')

    # HTTP PUT
    def put(self, fabric):
        path = os.path.join(self.root, self.fabrics, fabric, self.f_connections, 'index.json')
        put_object(path)
        return self.get(fabric)

    # HTTP DELETE
    def delete(self, fabric):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.fabrics, fabric, self.f_connections)
        base_path = create_path(self.root, self.fabrics, fabric)
        return delete_collection(path, base_path)
