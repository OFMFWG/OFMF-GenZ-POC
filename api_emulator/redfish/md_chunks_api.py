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

# c_memory_api.py

import json, os
import traceback
import logging
import shutil
import requests

import g
import urllib3

from flask import jsonify, request
from flask_restful import Resource
from api_emulator.utils import update_collections_json, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, delete_collection, create_collection
from .constants import *
from .templates.md_chunks import get_MDChunks_instance

members =[]
member_ids = []
config = {}
INTERNAL_ERROR = 500

# MemoryDomainAPI API
class MDChunksAPI(Resource):
    def __init__(self, **kwargs):
        logging.info('MDChunksAPI init called')
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']
        self.md_chunks = PATHS['Chassis']['md_chunks']


    # HTTP GET
    def get(self, chassis, memory_domain, md_chunks):
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        return get_json_data (path)

    # HTTP POST
    # - Create the resource (since URI variables are available)
    # - Update the members and members.id lists
    # - Attach the APIs of subordinate resources (do this only once)
    # - Finally, create an instance of the subordiante resources
    def post(self, chassis, memory_domain, md_chunks):
        logging.info('MDChunksAPI POST called')
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks)
        collection_path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')

        # Check if collection exists:
        if not os.path.exists(collection_path):
            MDChunksCollectionAPI.post (self, chassis, memory_domain)

        if md_chunks in members:
            resp = 404
            return resp
        try:
            global config
            global AGENT
            wildcards = {'c_id':chassis, 'md_id': memory_domain, 'mc_id': md_chunks, 'rb': g.rest_base}
            config=get_MDChunks_instance(wildcards)

            # Send commands to Agent:
            agentpath = create_path ("http://localhost:5050/redfish/v1/", self.chassis, chassis, self.memory_domains,  memory_domain, self.md_chunks, md_chunks)
            logging.info(agentpath)
            agentresponse = requests.post(agentpath, data = config )
            logging.info(agentresponse)

            if agentresponse == 200:
                objectinfo =  requests.get(agentpath)

                # Set odata.id and Id to properties for this instance:
                config['@odata.id'] = create_path ("/redfish/v1/", self.chassis, chassis, self.memory_domains,  memory_domain, self.md_chunks, md_chunks)
                config['Id'] = md_chunks

                config = create_and_patch_object (config, members, member_ids, path, collection_path)
                # Create sub-collections:
                resp = config, 200
            else:
                resp = 404
                return resp

        except Exception:
            traceback.print_exc()
            resp = INTERNAL_ERROR
        logging.info('MDChunksAPI POST exit')
        return resp

	# HTTP PATCH
    def patch(self, chassis, memory_domain, md_chunks):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        patch_object(path)
        return self.get(chassis, memory_domain)

    # HTTP PUT
    def put(self, chassis, memory_domain, md_chunks):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks, 'index.json')
        put_object(path)
        return self.get(chassis, memory_domain)

    # HTTP DELETE
    def delete(self, chassis, memory_domain, md_chunks):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, md_chunks)
        base_path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        return delete_object(path, base_path)


# MemoryDomains Collection API
class MDChunksCollectionAPI(Resource):

    def __init__(self):
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']
        self.md_chunks = PATHS['Chassis']['md_chunks']

    def get(self, chassis, memory_domain):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')
        return get_json_data (path)

    def verify(self, config):
        # TODO: Implement a method to verify that the POST body is valid
        return True,{}

    # HTTP POST Collection
    def post(self, chassis, memory_domain):
        self.root = PATHS['Root']
        self.chassis = PATHS['Chassis']['path']
        self.memory_domains = PATHS['Chassis']['memory_domain']

        logging.info('MDChunksCollectionAPI POST called')

        if memory_domain in members:
            resp = 404
            return resp

        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        return create_collection (path, 'MemoryChunk')

    # HTTP PUT
    def put(self, chassis, memory_domain):
        path = os.path.join(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks, 'index.json')
        put_object(path)
        return self.get(chassis)

    # HTTP DELETE
    def delete(self, chassis, memory_domain):
        #Set path to object, then call delete_object:
        path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain, self.md_chunks)
        base_path = create_path(self.root, self.chassis, chassis, self.memory_domains, memory_domain)
        return delete_collection(path, base_path)
