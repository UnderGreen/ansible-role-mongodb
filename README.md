# Ansible role for MongoDB [![Build Status](https://travis-ci.org/UnderGreen/ansible-role-mongodb.svg?branch=master)](https://travis-ci.org/UnderGreen/ansible-role-mongodb)

Ansible role which manages [MongoDB](http://www.mongodb.org/).

- Install and configure the MongoDB;
- Configure mongodb users
- Configure replication
- Provide handlers for restart and reload;
- Setup MMS automation agent;

MongoDB support matrix:

| Distribution   | < MongoDB 3.2 |    MongoDB 3.4     |    MongoDB 3.6     |    MongoDB 4.0     |   MongoDB 4.2      |   MongoDB 4.4      |
| -------------- | :-----------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: |
| Ubuntu 14.04   |  :no_entry:   | :white_check_mark: | :white_check_mark: | :white_check_mark: |        :x:         | :interrobang:      |
| Ubuntu 16.04   |  :no_entry:   | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :interrobang:      |
| Ubuntu 18.04   |  :no_entry:   |        :x:         |        :x:         | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Ubuntu 20.04   |  :no_entry:   |        :x:         |        :x:         | :interrobang:      | :interrobang:      | :white_check_mark: |
| Debian 8.x     |  :no_entry:   | :white_check_mark: | :white_check_mark: | :white_check_mark: |        :x:         | :white_check_mark: |
| Debian 9.x     |  :no_entry:   |        :x:         | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| RHEL 6.x       |  :no_entry:   | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :interrobang:      |
| RHEL 7.x       |  :no_entry:   | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| RHEL 8.x       |  :no_entry:   | :interrobang:      | :interrobang:      | :interrobang:      | :white_check_mark: | :white_check_mark: |
| Amazon Linux 2 |  :no_entry:   | :white_check_mark: |        :x:         | :white_check_mark: | :white_check_mark: | :white_check_mark: |
- :white_check_mark: - fully tested, should works fine
- :interrobang: - maybe works, not tested
- :x: - don't have official support
- :no_entry: - MongoDB has reached EOL

#### Variables

```yaml
# You can use this variable to control installation source of MongoDB
# 'mongodb' will be installed from Debian/Ubuntu repos
# 'mongodb-org' will be installed from MongoDB official repos
mongodb_package: mongodb-org

# You can control installed version via this param.
# Should be '3.4', '3.6', '4.0', '4.2' or '4.4'. This role doesn't support MongoDB < 3.4.
# I will recommend you to use latest version of MongoDB.
mongodb_version: "4.4"

mongodb_pymongo_from_pip: true # Install latest PyMongo via PIP or package manager
mongodb_pymongo_pip_version: 3.10.1 # Choose PyMong version to install from pip. If not set use latest
mongodb_user_update_password: "on_create" # MongoDB user password update default policy
mongodb_manage_service: true
mongodb_manage_systemd_unit: true

# Disable transparent hugepages on systemd debian based installations
# https://docs.mongodb.com/manual/tutorial/transparent-huge-pages/
mongodb_disable_transparent_hugepages: false

# OS tuning
vm_swappiness:
vm_dirty_ratio:
vm_dirty_background_ratio:

# You can enable or disable NUMA support
mongodb_use_numa: true

mongodb_user: "{{ 'mongod' if ('RedHat' == ansible_os_family) else 'mongodb' }}"
mongodb_uid:
mongodb_gid:
mongodb_daemon_name: "{{ 'mongod' if ('mongodb-org' in mongodb_package) else 'mongodb' }}"
## net Options
mongodb_net_bindip: 127.0.0.1 # Comma separated list of ip addresses to listen on
mongodb_net_http_enabled: false # Enable http interface
mongodb_net_ipv6: false # Enable IPv6 support (disabled by default)
mongodb_net_maxconns: 65536 # Max number of simultaneous connections
mongodb_net_port: 27017 # Specify port number

## processManagement Options
mongodb_processmanagement_fork: false # Fork server process

## security Options
# Disable or enable security. Possible values: 'disabled', 'enabled'
mongodb_security_authorization: "disabled"
mongodb_security_keyfile: /etc/mongodb-keyfile # Specify path to keyfile with password for inter-process authentication

## storage Options
mongodb_storage_dbpath: /data/db # Directory for datafiles
mongodb_storage_dirperdb: false # Use one directory per DB

# The storage engine for the mongod database
mongodb_storage_engine: "wiredTiger"
# mmapv1 specific options
mongodb_storage_quota_enforced: false # Limits each database to a certain number of files
mongodb_storage_quota_maxfiles: 8 # Number of quota files per DB
mongodb_storage_smallfiles: false # Very useful for non-data nodes

mongodb_storage_journal_enabled: true # Enable journaling
mongodb_storage_prealloc: true # Disable data file preallocation

# WiredTiger Options
mongodb_wiredtiger_cache_size: 1 # Cache size for wiredTiger in GB

## systemLog Options
## The destination to which MongoDB sends all log output. Specify either 'file' or 'syslog'.
## If you specify 'file', you must also specify mongodb_systemlog_path.
mongodb_systemlog_destination: "file"
mongodb_systemlog_logappend: true # Append to logpath instead of over-writing
mongodb_systemlog_path: /var/log/mongodb/{{ mongodb_daemon_name }}.log # Log file to send write to instead of stdout

## replication Options
mongodb_replication_replset: # Enable replication <setname>[/<optionalseedhostlist>]
mongodb_replication_replindexprefetch: "all" # specify index prefetching behavior (if secondary) [none|_id_only|all]
mongodb_replication_oplogsize: 1024 # specifies a maximum size in megabytes for the replication operation log

## setParameter options
# Configure setParameter option.
# Example :
mongodb_set_parameters:
  {
    "enableLocalhostAuthBypass": "true",
    "authenticationMechanisms": "SCRAM-SHA-1,MONGODB-CR",
  }

## Extend config with arbitrary values
# Example :
mongodb_config:
  replication:
    - "enableMajorityReadConcern: false"

# MMS Agent
mongodb_mms_agent_pkg: https://cloud.mongodb.com/download/agent/monitoring/mongodb-mms-monitoring-agent_7.2.0.488-1_amd64.ubuntu1604.deb
mongodb_mms_group_id: ""
mongodb_mms_api_key: ""
mongodb_mms_base_url: https://mms.mongodb.com

# Log rotation
mongodb_logrotate: true # Rotate mongodb logs.
mongodb_logrotate_options:
  - compress
  - copytruncate
  - daily
  - dateext
  - rotate 7
  - size 10M

# Password for inter-process authentication
# If not defined, it will be generated at runtime with the command 'openssl rand -base64 756'
# Be careful if you perform the function to configure different servers in different executions, different keys will be generated 
# therefore, the service will not be able to authenticate, in which case you need to specify the key to have exactly the same
# If mongodb_keyfile_force_renew is true and the keyfile alredy exist in the host, the keyfile will be replaced with mongodb_keyfile_content when defined or with a new runtime generate key
mongodb_keyfile_force_renew: false
mongodb_keyfile_content: 

# names and passwords for administrative users
mongodb_user_admin_name: siteUserAdmin
mongodb_user_admin_password: passw0rd

mongodb_root_admin_name: siteRootAdmin
mongodb_root_admin_password: passw0rd

mongodb_root_backup_name: backupuser
mongodb_root_backup_password: passw0rd
```

#### Usage

Add `undergreen.mongodb` to your roles and set vars in your playbook file.

Example vars for authorization:

```yaml
mongodb_security_authorization: "enabled"
mongodb_users:
  - {
    name: testUser,
    password: passw0rd,
    roles: readWrite,
    database: app_development
}
```

Example vars for oplog user:

```yaml
mongodb_oplog_users:
  - {
    user: oplog,
    password: passw0rd
}
```

Required vars to change on production:

```yaml
mongodb_user_admin_password
mongodb_root_admin_password
mongodb_root_backup_password

# if you use replication and authorization
mongodb_security_keyfile
```

Example vars for replication:

```yaml
# It's a 'master' node
mongodb_login_host: 192.168.56.2

# mongodb_replication_params should be configured on each replica set node
mongodb_replication_params:
  - {
      host_name: 192.168.56.2,
      host_port: "{{ mongodb_net_port }}",
      host_type: replica,
    }
  # host_type can be replica(default) and arbiter
```

And inventory file for replica set:

```ini
[mongo_master]
192.158.56.2 mongodb_master=True # it is't a really master of MongoDB replica set,
                                 # use this variable for replica set init only
								 # or when master is moved from initial master node

[mongo_replicas]
192.168.56.3
192.168.56.4

[mongo:children]
mongo_master
mongo_replicas
```

Licensed under the GPLv2 License. See the [LICENSE.md](LICENSE.md) file for details.

#### Feedback, bug-reports, requests, ...

Are [welcome](https://github.com/UnderGreen/ansible-role-mongodb/issues)!
