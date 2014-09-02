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
  - mongodb-org

mongodb_conf:
  auth: "false"
  bind_ip: 127.0.0.1
  cpu: "true"
  dbpath: /var/lib/mongodb/
  # diaglog: 0 # deprecated
  logappend: "true"
  logpath: /var/log/mongodb/mongod.log
  noauth: "true"
  nohints: "false"
  nohttpinterface: "false"
  nojournal: "true"
  noprealloc: "false"
  noscripting: "false"
  notablescan: "false"
  objcheck: "false"
  port: 27017
  quota: "false"
  # replSet: "" # Set for enable replication
  verbose: "true"
  vvvv: "true"


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
