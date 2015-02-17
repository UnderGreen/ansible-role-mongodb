#!/usr/bin/python

# (c) 2015, Sergei Antipov, 2GIS LLC
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: mongodb_replication
short_description: Adds or removes a node from a MongoDB Replica Set.
description:
    - Adds or removes host from a MongoDB replica set. Initialize replica set if it needed.
options:
    login_user:
        description:
            - The username used to authenticate with
        required: false
        default: null
    login_password:
        description:
            - The password used to authenticate with
        required: false
        default: null
    login_host:
        description:
            - The host running the database
        required: false
        default: localhost
    login_port:
        description:
            - The port to connect to
        required: false
        default: 27017
    replica_set:
        description:
            - Replica set to connect to (automatically connects to primary for writes)
        required: false
        default: null
    host_name:
        description:
            - The name of the host to add/remove from replica set
        required: true
    host_port:
        description:
            - The port of the host
        required: true
        default: null
    host_type:
        description:
            - The type of the host in replica set
        required: false
        default: replica
        choices: [ "replica", "arbiter" ]
    ssl:
        description:
            - Whether to use an SSL connection when connecting to the database
        default: False
    state:
        state:
        description:
            - The database user state
        required: false
        default: present
        choices: [ "present", "absent" ]
notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
author: Sergei Antipov
'''

EXAMPLES = '''
# Add 'mongo1.dev:27017' host into replica set as replica (Replica will be initiated if it not exists)
- mongodb_replication: replica_set=replSet host_name=mongo1.dev host_port=27017 state=present

# Add 'mongo2.dev:30000' host into replica set as arbiter
- mongodb_replication: replica_set=replSet host_name=mongo2.dev host_port=30000 host_type=arbiter state=present

# Add 'mongo3.dev:27017' host into replica set as replica and authorization params
- mongodb_replication: replica_set=replSet login_host=mongo1.dev login_user=siteRootAdmin login_password=123456 host_name=mongo3.dev host_port=27017 state=present

# Add 'mongo4.dev:27017' host into replica set as replica via SSL
- mongodb_replication: replica_set=replSet host_name=mongo4.dev host_port=27017 ssl=True state=present

# Remove 'mongo4.dev:27017' host from the replica set
- mongodb_replication: replica_set=replSet host_name=mongo4.dev host_port=27017 state=absent
'''

import ConfigParser
import time
from distutils.version import LooseVersion
try:
    from pymongo.errors import ConnectionFailure
    from pymongo.errors import OperationFailure
    from pymongo.errors import ConfigurationError
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
    from pymongo import MongoReplicaSetClient
except ImportError:
    pymongo_found = False
else:
    pymongo_found = True

# =========================================
# MongoDB module specific support methods.
#

def check_members(state, module, client, host_name, host_port, host_type):
    admin_db = client['admin']
    local_db = client['local']

    if local_db.system.replset.count() > 1:
        module.fail_json(msg='local.system.replset has unexpected contents')

    cfg = local_db.system.replset.find_one()
    if not cfg:
        module.fail_json(msg='no config object retrievable from local.system.replset')

    for member in cfg['members']:
        if state == 'present':
            if host_type == 'replica':
                if "{0}:{1}".format(host_name, host_port) in member['host']:
                    module.exit_json(changed=False, host_name=host_name, host_port=host_port, host_type=host_type)
            else:
                if "{0}:{1}".format(host_name, host_port) in member['host'] and member['arbiterOnly']:
                    module.exit_json(changed=False, host_name=host_name, host_port=host_port, host_type=host_type)
        else:
            if host_type == 'replica':
                if "{0}:{1}".format(host_name, host_port) not in member['host']:
                    module.exit_json(changed=False, host_name=host_name, host_port=host_port, host_type=host_type)
            else:
                if "{0}:{1}".format(host_name, host_port) not in member['host'] and member['arbiterOnly']:
                    module.exit_json(changed=False, host_name=host_name, host_port=host_port, host_type=host_type)

def add_host(module, client, host_name, host_port, host_type):
    admin_db = client['admin']
    local_db = client['local']

    if local_db.system.replset.count() > 1:
        module.fail_json(msg='local.system.replset has unexpected contents')

    cfg = local_db.system.replset.find_one()
    if not cfg:
        module.fail_json(msg='no config object retrievable from local.system.replset')

    cfg['version'] += 1
    max_id = max(cfg['members'], key=lambda x:x['_id'])
    new_host = { '_id': max_id['_id'] + 1, 'host': "{0}:{1}".format(host_name, host_port) }
    if host_type == 'arbiter':
        new_host['arbiterOnly'] = True

    cfg['members'].append(new_host)
    admin_db.command('replSetReconfig', cfg)

def remove_host(module, client, host_name):
    admin_db = client['admin']
    local_db = client['local']

    if local_db.system.replset.count() > 1:
        module.fail_json(msg='local.system.replset has unexpected contents')

    cfg = local_db.system.replset.find_one()
    if not cfg:
        module.fail_json(msg='no config object retrievable from local.system.replset')

    cfg['version'] += 1

    if len(cfg['members']) == 1:
        module.fail_json(msg="You can't delete last member of replica set")
    for member in cfg['members']:
        if host_name in member['host']:
            cfg['members'].remove(member)
        else:
            fail_msg = "couldn't find member with hostname: {0} in replica set members list".format(host_name)
            module.fail_json(msg=fail_msg)
    admin_db.command('replSetReconfig', cfg)

def load_mongocnf():
    config = ConfigParser.RawConfigParser()
    mongocnf = os.path.expanduser('~/.mongodb.cnf')

    try:
        config.readfp(open(mongocnf))
        creds = dict(
          user=config.get('client', 'user'),
          password=config.get('client', 'pass')
        )
    except (ConfigParser.NoOptionError, IOError):
        return False

    return creds

def authenticate(client, login_user, login_password):
    if login_user is None and login_password is None:
        mongocnf_creds = load_mongocnf()
        if mongocnf_creds is not False:
            login_user = mongocnf_creds['user']
            login_password = mongocnf_creds['password']
        elif login_password is None and login_user is not None:
            module.fail_json(msg='when supplying login arguments, both login_user and login_password must be provided')

    if login_user is not None and login_password is not None:
        client.admin.authenticate(login_user, login_password)
# =========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
            login_user=dict(default=None),
            login_password=dict(default=None),
            login_host=dict(default='localhost'),
            login_port=dict(default='27017'),
            replica_set=dict(default=None),
            host_name=dict(default='localhost'),
            host_port=dict(default='27017'),
            host_type=dict(default='replica', choices=['replica','arbiter']),
            ssl=dict(default=False),
            state=dict(default='present', choices=['absent', 'present']),
        )
    )

    if not pymongo_found:
        module.fail_json(msg='the python pymongo (>= 2.4) module is required')

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    replica_set = module.params['replica_set']
    host_name = module.params['host_name']
    host_port = module.params['host_port']
    host_type = module.params['host_type']
    ssl = module.params['ssl']
    state = module.params['state']

    replica_set_created = False

    try:
        if replica_set is None:
            module.fail_json(msg='replica_set parameter is required')
        else:
            client = MongoReplicaSetClient(login_host, int(login_port), replicaSet=replica_set, ssl=ssl)

        authenticate(client, login_user, login_password)

    except ConnectionFailure, e:
        module.fail_json(msg='unable to connect to database: %s' % str(e))
    except ConfigurationError:
        try:
            client = MongoClient(login_host, int(login_port), ssl=ssl)
            authenticate(client, login_user, login_password)
            if state == 'present':
                config = { '_id': "{0}".format(replica_set), 'members': [{ '_id': 0, 'host': "{0}:{1}".format(host_name, host_port)}] }
                client['admin'].command('replSetInitiate', config)
                time.sleep(3)
                replica_set_created = True
                module.exit_json(changed=True, host_name=host_name, host_port=host_port, host_type=host_type)
        except OperationFailure, e:
            module.fail_json(msg='Unable to initiate replica set: %s' % str(e))

    check_members(state, module, client, host_name, host_port, host_type)

    if state == 'present':
        if host_name is None and not replica_set_created:
            module.fail_json(msg='host_name parameter required when adding new host into replica set')

        try:
            if not replica_set_created:
                add_host(module, client, host_name, host_port, host_type)
        except OperationFailure, e:
            module.fail_json(msg='Unable to add new member to replica set: %s' % str(e))

    elif state == 'absent':
        try:
            remove_host(module, client, host_name)
        except OperationFailure, e:
            module.fail_json(msg='Unable to remove member of replica set: %s' % str(e))

    module.exit_json(changed=True, host_name=host_name, host_port=host_port, host_type=host_type)

# import module snippets
from ansible.module_utils.basic import *
main()
