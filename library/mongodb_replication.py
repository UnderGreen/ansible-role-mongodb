#!/usr/bin/python

# (c) 2015-2016, Sergei Antipov, 2GIS LLC
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
version_added: "2.2"
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
            - The port of the host, which should be added/deleted from RS
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
    build_indexes:
        description:
            - Determines whether the mongod builds indexes on this member.
        required: false
        default: true
    hidden:
        description:
            - When this value is true, the replica set hides this instance,
              and does not include the member in the output of db.isMaster()
              or isMaster
        required: false
        default: false
    priority:
        description:
            - A number that indicates the relative eligibility of a member
              to become a primary
        required: false
        default: 1.0
    slave_delay:
        description:
            - The number of seconds behind the primary that this replica set
              member should lag
        required: false
        default: 0
    votes:
        description:
            - The number of votes a server will cast in a replica set election
        default: 1
    state:
        state:
        description:
            - The replica set member state
        required: false
        default: present
        choices: [ "present", "absent" ]
notes:
    - Requires the pymongo Python package on the remote host, version 3.0+. It
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
author: "Sergei Antipov @UnderGreen"
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

RETURN = '''
host_name:
  description: The name of the host to add/remove from replica set
  returned: success
  type: string
  sample: "mongo3.dev"
host_port:
  description: The port of the host, which should be added/deleted from RS
  returned: success
  type: int
  sample: 27017
host_type:
  description: The type of the host in replica set
  returned: success
  type: string
  sample: "replica"
'''
import ConfigParser
import time
from distutils.version import LooseVersion
try:
    from pymongo.errors import ConnectionFailure
    from pymongo.errors import OperationFailure
    from pymongo.errors import ConfigurationError
    from pymongo.errors import AutoReconnect
    from pymongo.errors import ServerSelectionTimeoutError
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
def check_compatibility(module, client):
    if LooseVersion(PyMongoVersion) <= LooseVersion('3.0'):
        module.fail_json(msg='Note: you must use pymongo 3.0+')
    srv_info = client.server_info()
    if LooseVersion(srv_info['version']) >= LooseVersion('3.2') and LooseVersion(PyMongoVersion) <= LooseVersion('3.2'):
        module.fail_json(msg=' (Note: you must use pymongo 3.2+ with MongoDB >= 3.2)')

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

def add_host(module, client, host_name, host_port, host_type, timeout=180, **kwargs):
    while True:
        try:
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

            if not kwargs['build_indexes']:
                new_host['buildIndexes'] = False

            if kwargs['hidden']:
                new_host['hidden'] = True

            if kwargs['priority'] != 1.0:
                new_host['priority'] = kwargs['priority']

            if kwargs['slave_delay'] != 0:
                new_host['slaveDelay'] = kwargs['slave_delay']

            if kwargs['votes'] != 1:
                new_host['votes'] = kwargs['votes']

            cfg['members'].append(new_host)
            admin_db.command('replSetReconfig', cfg)
            return
        except (OperationFailure, AutoReconnect), e:
            timeout = timeout - 5
            if timeout <= 0:
                module.fail_json(msg='reached timeout while waiting for rs.reconfig(): %s' % str(e))
            time.sleep(5)

def remove_host(module, client, host_name, timeout=180):
    while True:
        try:
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
        except (OperationFailure, AutoReconnect), e:
            timeout = timeout - 5
            if timeout <= 0:
                module.fail_json(msg='reached timeout while waiting for rs.reconfig(): %s' % str(e))
            time.sleep(5)

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

def wait_for_ok_and_master(module, client, timeout = 60):
    while True:
        status = client.admin.command('replSetGetStatus', check=False)
        if status['ok'] == 1 and status['myState'] == 1:
            return

        timeout = timeout - 1
        if timeout == 0:
            module.fail_json(msg='reached timeout while waiting for rs.status() to become ok=1')

        time.sleep(1)

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
            ssl=dict(default='false'),
            build_indexes = dict(type='bool', default='yes'),
            hidden = dict(type='bool', default='no'),
            priority = dict(default='1.0'),
            slave_delay = dict(type='int', default='0'),
            votes = dict(type='int', default='1'),
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
    priority = float(module.params['priority'])

    replica_set_created = False

    try:
        if replica_set is None:
            module.fail_json(msg='replica_set parameter is required')
        else:
            client = MongoClient(login_host, int(login_port), replicaSet=replica_set,
                                 ssl=ssl, serverSelectionTimeoutMS=5000)

        authenticate(client, login_user, login_password)
        client['admin'].command('replSetGetStatus')

    except ServerSelectionTimeoutError:
        try:
            client = MongoClient(login_host, int(login_port), ssl=ssl)
            authenticate(client, login_user, login_password)
            if state == 'present':
                new_host = { '_id': 0, 'host': "{0}:{1}".format(host_name, host_port) }
                if priority != 1.0: new_host['priority'] = priority
                config = { '_id': "{0}".format(replica_set), 'members': [new_host] }
                client['admin'].command('replSetInitiate', config)
                wait_for_ok_and_master(module, client)
                replica_set_created = True
                module.exit_json(changed=True, host_name=host_name, host_port=host_port, host_type=host_type)
        except OperationFailure, e:
            module.fail_json(msg='Unable to initiate replica set: %s' % str(e))
    except ConnectionFailure, e:
        module.fail_json(msg='unable to connect to database: %s' % str(e))

    check_compatibility(module, client)
    check_members(state, module, client, host_name, host_port, host_type)

    if state == 'present':
        if host_name is None and not replica_set_created:
            module.fail_json(msg='host_name parameter required when adding new host into replica set')

        try:
            if not replica_set_created:
                add_host(module, client, host_name, host_port, host_type,
                        build_indexes   = module.params['build_indexes'],
                        hidden          = module.params['hidden'],
                        priority        = float(module.params['priority']),
                        slave_delay     = module.params['slave_delay'],
                        votes           = module.params['votes'])
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
