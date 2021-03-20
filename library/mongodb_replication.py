#!/usr/bin/python

# (c) 2015-2021, Sergei Antipov
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: mongodb_replication
short_description: Adds or removes a node from a MongoDB Replica Set.
description:
    - Adds or removes host from a MongoDB replica set. Initialize replica set if it needed.
version_added: "2.4"
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
    login_database:
        description:
            - The database where login credentials are stored
        required: false
        default: admin
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
    ssl_cert_reqs:
        description:
            - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided.
        required: false
        default: "CERT_REQUIRED"
        choices: ["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"]
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
    - Requires the pymongo Python package on the remote host, version 3.2+. It
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

import os
import ssl as ssl_lib
import time
import traceback
from datetime import datetime as dtdatetime
from distutils.version import LooseVersion

try:
    from pymongo.errors import ConnectionFailure, OperationFailure, AutoReconnect, ServerSelectionTimeoutError
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
except ImportError:
    try:  # for older PyMongo 2.2
        from pymongo import Connection as MongoClient
    except ImportError:
        pymongo_found = False
    else:
        pymongo_found = True
else:
    pymongo_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_native

# =========================================
# MongoDB module specific support methods.
#


def check_compatibility(module, client):
    """Check the compatibility between the driver and the database.
       See: https://docs.mongodb.com/ecosystem/drivers/driver-compatibility-reference/#python-driver-compatibility
    Args:
        module: Ansible module.
        client (cursor): Mongodb cursor on admin database.
    """
    loose_srv_version = LooseVersion(client.server_info()['version'])
    loose_driver_version = LooseVersion(PyMongoVersion)

    if loose_srv_version >= LooseVersion('4.0') and loose_driver_version < LooseVersion('3.7'):
        module.fail_json(msg=' (Note: you must use pymongo 3.7+ with MongoDB >= 4.0)')

    elif loose_srv_version >= LooseVersion('3.6') and loose_driver_version < LooseVersion('3.6'):
        module.fail_json(msg=' (Note: you must use pymongo 3.6+ with MongoDB >= 3.6)')

    elif loose_srv_version >= LooseVersion('3.2') and loose_driver_version < LooseVersion('3.2'):
        module.fail_json(msg=' (Note: you must use pymongo 3.2+ with MongoDB >= 3.2)')

    elif loose_srv_version >= LooseVersion('3.0') and loose_driver_version <= LooseVersion('2.8'):
        module.fail_json(msg=' (Note: you must use pymongo 2.8+ with MongoDB 3.0)')

    elif loose_srv_version >= LooseVersion('2.6') and loose_driver_version <= LooseVersion('2.7'):
        module.fail_json(msg=' (Note: you must use pymongo 2.7+ with MongoDB 2.6)')

    elif LooseVersion(PyMongoVersion) <= LooseVersion('2.5'):
        module.fail_json(msg=' (Note: you must be on mongodb 2.4+ and pymongo 2.5+ to use the roles param)')


def check_members(state, module, client, host_name, host_port, host_type):
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
    start_time = dtdatetime.now()
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
            max_id = max(cfg['members'], key=lambda x: x['_id'])
            new_host = {'_id': max_id['_id'] + 1, 'host': "{0}:{1}".format(host_name, host_port)}
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
        except (OperationFailure, AutoReconnect) as e:
            if (dtdatetime.now() - start_time).seconds > timeout:
                module.fail_json(msg='reached timeout while waiting for rs.reconfig(): %s' % to_native(e), exception=traceback.format_exc())
            time.sleep(5)


def remove_host(module, client, host_name, timeout=180):
    start_time = dtdatetime.now()
    while True:
        try:
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
        except (OperationFailure, AutoReconnect) as e:
            if (dtdatetime.now() - start_time).seconds > timeout:
                module.fail_json(msg='reached timeout while waiting for rs.reconfig(): %s' % to_native(e), exception=traceback.format_exc())
            time.sleep(5)


def load_mongocnf():
    config = configparser.RawConfigParser()
    mongocnf = os.path.expanduser('~/.mongodb.cnf')

    try:
        config.readfp(open(mongocnf))
        creds = dict(
            user=config.get('client', 'user'),
            password=config.get('client', 'pass')
        )
    except (configparser.NoOptionError, IOError):
        return False

    return creds


def wait_for_ok_and_master(module, connection_params, timeout=180):
    start_time = dtdatetime.now()
    while True:
        try:
            client = MongoClient(**connection_params)
            authenticate(module, client, connection_params["username"], connection_params["password"])

            status = client.admin.command('replSetGetStatus', check=False)
            if status['ok'] == 1 and status['myState'] == 1:
                return

        except ServerSelectionTimeoutError:
            pass

        client.close()

        if (dtdatetime.now() - start_time).seconds > timeout:
            module.fail_json(msg='reached timeout while waiting for rs.status() to become ok=1')

        time.sleep(1)


def authenticate(module, client, login_user, login_password):
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
        argument_spec=dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default='localhost'),
            login_port=dict(default='27017'),
            login_database=dict(default="admin"),
            replica_set=dict(default=None),
            host_name=dict(default='localhost'),
            host_port=dict(default='27017'),
            host_type=dict(default='replica', choices=['replica', 'arbiter']),
            ssl=dict(default=False, type='bool'),
            ssl_cert_reqs=dict(default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
            build_indexes=dict(type='bool', default='yes'),
            hidden=dict(type='bool', default='no'),
            priority=dict(default='1.0'),
            slave_delay=dict(type='int', default='0'),
            votes=dict(type='int', default='1'),
            state=dict(default='present', choices=['absent', 'present']),
        )
    )

    if not pymongo_found:
        module.fail_json(msg=missing_required_lib('pymongo'))

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    login_database = module.params['login_database']
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
            connection_params = {
                "host": login_host,
                "port": int(login_port),
                "username": login_user,
                "password": login_password,
                "authsource": login_database,
                "serverselectiontimeoutms": 5000,
                "replicaset": replica_set,
            }

        if ssl:
            connection_params["ssl"] = ssl
            connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

        client = MongoClient(**connection_params)
        authenticate(module, client, login_user, login_password)
        client['admin'].command('replSetGetStatus')

    except ServerSelectionTimeoutError:
        try:
            connection_params = {
                "host": login_host,
                "port": int(login_port),
                "username": login_user,
                "password": login_password,
                "authsource": login_database,
                "serverselectiontimeoutms": 10000,
            }

            if ssl:
                connection_params["ssl"] = ssl
                connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

            client = MongoClient(**connection_params)
            authenticate(module, client, login_user, login_password)
            if state == 'present':
                new_host = {'_id': 0, 'host': "{0}:{1}".format(host_name, host_port)}
                if priority != 1.0:
                    new_host['priority'] = priority
                config = {'_id': "{0}".format(replica_set), 'members': [new_host]}
                client['admin'].command('replSetInitiate', config)
                client.close()
                wait_for_ok_and_master(module, connection_params)
                replica_set_created = True
                module.exit_json(changed=True, host_name=host_name, host_port=host_port, host_type=host_type)
        except OperationFailure as e:
            module.fail_json(msg='Unable to initiate replica set: %s' % to_native(e), exception=traceback.format_exc())
    except ConnectionFailure as e:
        module.fail_json(msg='unable to connect to database: %s' % to_native(e), exception=traceback.format_exc())

    # reconnect again
    client = MongoClient(**connection_params)
    authenticate(module, client, login_user, login_password)
    check_compatibility(module, client)
    check_members(state, module, client, host_name, host_port, host_type)

    if state == 'present':
        if host_name is None and not replica_set_created:
            module.fail_json(msg='host_name parameter required when adding new host into replica set')

        try:
            if not replica_set_created:
                add_host(module, client, host_name, host_port, host_type,
                         build_indexes=module.params['build_indexes'],
                         hidden=module.params['hidden'],
                         priority=float(module.params['priority']),
                         slave_delay=module.params['slave_delay'],
                         votes=module.params['votes'])
        except OperationFailure as e:
            module.fail_json(msg='Unable to add new member to replica set: %s' % to_native(e), exception=traceback.format_exc())

    elif state == 'absent':
        try:
            remove_host(module, client, host_name)
        except OperationFailure as e:
            module.fail_json(msg='Unable to remove member of replica set: %s' % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=True, host_name=host_name, host_port=host_port, host_type=host_type)


if __name__ == '__main__':
    main()
