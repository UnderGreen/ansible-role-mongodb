Stouts.mongo
============

[![Build Status](https://travis-ci.org/Stouts/Stouts.nginx.png)](https://travis-ci.org/Stouts/Stouts.mongodb)

Ansible role which manage [MongoDB](http://www.mongodb.org/)

* Install and configure;
* Provide hanlers for restart and reload;

#### Variables

```yaml
mongodb_enabled: yes
mongodb_packages:
  - python-selinux
  - python-pymongo
  - mongodb-10gen

# Configuration
# A list of hashes that are used to configure MongoDB. Any valid configuration parameters can be defined here.
mongodb_conf:
  dbpath: /var/lib/mongodb/
  logpath: /var/log/mongodb/mongod.log
  logappend: "true"
  port: 27017
  bind_ip: 127.0.0.1
  nojournal: "true"
  # auth: "true"
  noauth: "true"
  cpu: "true"
  verbose: "true"
  vvvv: "true"
  quota: "false"
  auth: "false"
  objcheck: "false"
  # diaglog: 0 # deprecated
  nohints: "false"
  nohttpinterface: "false"
  noscripting: "false"
  notablescan: "false"
  noprealloc: "false"
  # replSet: "" # Set for enable replication

# Log rotation
mongodb_logrotate: yes                             # Rotate mongodb logs.
mongodb_logrotate_options:
  - compress
  - copytruncate
  - daily
  - dateext
  - rotate 7
  - size 10M
```

#### Usage

Add `Stouts.mongodb` to your roles and set vars in your playbook file.

Example:

```yaml

- hosts: all

  roles:
    - Stouts.mongodb

  vars:
    port: 27400
```

#### License

Licensed under the MIT License. See the LICENSE file for details.

#### Feedback, bug-reports, requests, ...

Are [welcome](https://github.com/Stouts/Stouts.mongodb/issues)!
