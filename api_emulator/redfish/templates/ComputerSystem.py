# Copyright Notice:
# Copyright 2017-2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Interface-Emulator/blob/master/LICENSE.md

# Example Resoruce Template
import copy
import strgen
import json

_TEMPLATE = \
{
    "@odata.id": "{rb}Systems/{s_id}",
    "@odata.type": "#ComputerSystem.v1_3_0.ComputerSystem",
    "Id": "{s_id}",
    "Name": "Gen-Z PoC SoC",
    "SystemType": "Physical",
    "Manufacturer": "Manufacturer Name",
    "Model": "Model Name",
    "SerialNumber": "UNKNOWN",
    "Description": "Description of server",
    "UUID": "00000000-0000-0000-0000-000000000000",
    "Status": {
        "State": "Enabled",
        "Health": "OK",
        "HealthRollup": "OK"
    },
    "FabricAdapters": {
        "@odata.id": "{rb}Systems/{s_id}/FabricAdapters"
    },
}

def get_ComputerSystem_instance(wildcards):
    """
    Instantiate and format the template

    Arguments:
        wildcard - A dictionary of wildcards strings and their repalcement values

    """
    c = copy.deepcopy(_TEMPLATE)
    d = json.dumps(c)
    g = d.replace('{s_id}', 'NUv')
    g = g.replace('{rb}', 'NUb')
    g = g.replace('{{', '~~!')
    g = g.replace('}}', '!!~')
    g = g.replace('{', '~!')
    g = g.replace('}', '!~')
    g = g.replace('NUv', '{s_id}')
    g = g.replace('NUb', '{rb}')
    g = g.format(**wildcards)
    g = g.replace('~~!', '{{')
    g = g.replace('!!~', '}}')
    g = g.replace('~!', '{')
    g = g.replace('!~', '}')
    return json.loads(g)


