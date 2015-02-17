Ansible role for MongoDB
============
This repository forked from [Stouts.mongodb](https://github.com/Stouts/Stouts.mongodb).  
Ansible role which manage [MongoDB](http://www.mongodb.org/)

* Install and configure the MongoDB;
* Provide hanlers for restart and reload;
* Setup MMS authomation agent;

#### Variables

```yaml
mongodb_package: mongodb-org

mongodb_additional_packages:
- python-pymongo

mongodb_user: mongodb
mongodb_daemon_name: "{{ 'mongod' if ('mongodb-org' in mongodb_package) else 'mongodb' }}"

mongodb_conf_auth: false                          # Run with security
mongodb_conf_bind_ip: 127.0.0.1                   # Comma separated list of ip addresses to listen on
mongodb_conf_cpu: true                            # Periodically show cpu and iowait utilization
mongodb_conf_dbpath: /data/db                     # Directory for datafiles
mongodb_conf_fork: false                          # Fork server process
mongodb_conf_httpinterface: false                 # Enable http interface
mongodb_conf_ipv6: false                          # Enable IPv6 support (disabled by default)
mongodb_conf_journal: true                        # Enable journaling
mongodb_conf_logappend: true                      # Append to logpath instead of over-writing
mongodb_conf_logpath: /var/log/mongodb/{{ mongodb_daemon_name }}.log # Log file to send write to instead of stdout
mongodb_conf_maxConns: 1000000                    # Max number of simultaneous connections
mongodb_conf_noprealloc: false                    # Disable data file preallocation
mongodb_conf_smallfiles: false                    # Disable smallfiles option
mongodb_conf_noscripting: false                   # Disable scripting engine
mongodb_conf_notablescan: false                   # Do not allow table scans
mongodb_conf_port: 27017                          # Specify port number
mongodb_conf_quota: false                         # Limits each database to a certain number of files
mongodb_conf_quotaFiles: 8                        # Number of quota files
mongodb_conf_syslog: false                        # Log to system's syslog facility instead of file

# Replica set options:
mongodb_conf_replSet:                             # Enable replication <setname>[/<optionalseedhostlist>]
mongodb_conf_replIndexPrefetch: "all"             # specify index prefetching behavior (if secondary) [none|_id_only|all]
mongodb_conf_oplogSize: 512                       # specifies a maximum size in megabytes for the replication operation log
mongodb_conf_keyFile: /etc/mongodb-keyfile        # Specify path to keyfile with password for inter-process authentication

# MMS Agent
mongodb_mms_agent_pkg: https://mms.mongodb.com/download/agent/automation/mongodb-mms-automation-agent-manager_1.4.2.783-1_amd64.deb
mongodb_mms_group_id: ""
mongodb_mms_api_key: ""
mongodb_mms_base_url: https://mms.mongodb.com

# Log rotation
mongodb_logrotate: true                             # Rotate mongodb logs.
mongodb_logrotate_options:
  - compress
  - copytruncate
  - daily
  - dateext
  - rotate 7
  - size 10M

# password for inter-process authentication
# please regenerate this file on production environment with command 'openssl rand -base64 741'
mongodb_keyfile_content: |
  8pYcxvCqoe89kcp33KuTtKVf5MoHGEFjTnudrq5BosvWRoIxLowmdjrmUpVfAivh
  CHjqM6w0zVBytAxH1lW+7teMYe6eDn2S/O/1YlRRiW57bWU3zjliW3VdguJar5i9
  Z+1a8lI+0S9pWynbv9+Ao0aXFjSJYVxAm/w7DJbVRGcPhsPmExiSBDw8szfQ8PAU
  2hwRl7nqPZZMMR+uQThg/zV9rOzHJmkqZtsO4UJSilG9euLCYrzW2hdoPuCrEDhu
  Vsi5+nwAgYR9dP2oWkmGN1dwRe0ixSIM2UzFgpaXZaMOG6VztmFrlVXh8oFDRGM0
  cGrFHcnGF7oUGfWnI2Cekngk64dHA2qD7WxXPbQ/svn9EfTY5aPw5lXzKA87Ds8p
  KHVFUYvmA6wVsxb/riGLwc+XZlb6M9gqHn1XSpsnYRjF6UzfRcRR2WyCxLZELaqu
  iKxLKB5FYqMBH7Sqg3qBCtE53vZ7T1nefq5RFzmykviYP63Uhu/A2EQatrMnaFPl
  TTG5CaPjob45CBSyMrheYRWKqxdWN93BTgiTW7p0U6RB0/OCUbsVX6IG3I9N8Uqt
  l8Kc+7aOmtUqFkwo8w30prIOjStMrokxNsuK9KTUiPu2cj7gwYQ574vV3hQvQPAr
  hhb9ohKr0zoPQt31iTj0FDkJzPepeuzqeq8F51HB56RZKpXdRTfY8G6OaOT68cV5
  vP1O6T/okFKrl41FQ3CyYN5eRHyRTK99zTytrjoP2EbtIZ18z+bg/angRHYNzbgk
  lc3jpiGzs1ZWHD0nxOmHCMhU4usEcFbV6FlOxzlwrsEhHkeiununlCsNHatiDgzp
  ZWLnP/mXKV992/Jhu0Z577DHlh+3JIYx0PceB9yzACJ8MNARHF7QpBkhtuGMGZpF
  T+c73exupZFxItXs1Bnhe3djgE3MKKyYvxNUIbcTJoe7nhVMrwO/7lBSpVLvC4p3
  wR700U0LDaGGQpslGtiE56SemgoP

# names and passwords for administrative users
mongodb_user_admin_name: siteUserAdmin
mongodb_user_admin_password: passw0rd

mongodb_root_admin_name: siteRootAdmin
mongodb_root_admin_password: passw0rd
```

#### Usage

Add `greendayonfire.mongodb` to your roles and set vars in your playbook file.

Example vars for authorization:
```yaml
mongodb_conf_auth: true
mongodb_users:
  - {
    name: testUser,
    password: passw0rd,
    roles: readWrite,
    database: app_development
}
```
Required vars to change on production:
```yaml
mongodb_user_admin_password
mongodb_root_admin_password
```
Example vars for replication:
```yaml
mongodb_login_host: 192.168.56.2      # Mongodb master host

# mongodb_replication_params should be configured on each replica set node
mongodb_replication_params:
  - { host_name: 192.168.56.2, host_port: "{{ mongodb_conf_port }}", host_type: replica }
  # host_type can be replica(default) and arbiter
```

Licensed under the GPLv2 License. See the [LICENSE.md](LICENSE.md) file for details.

#### Feedback, bug-reports, requests, ...

Are [welcome](https://github.com/UnderGreen/ansible-role-mongodb/issues)!
