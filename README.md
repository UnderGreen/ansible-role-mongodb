Stouts.mongo
============

[![Build Status](https://travis-ci.org/Stouts/Stouts.nginx.png)](https://travis-ci.org/Stouts/Stouts.mongodb)

Ansible role which manage [MongoDB](http://www.mongodb.org/)

* Install and configure;
* Provide hanlers for restart and reload;

#### Variables

```yaml
mongodb_packages:
  - python-selinux
  - python-pymongo
  - mongodb-10gen

# Configuration
mongodb_dbpath: /var/lib/mongodb
mongodb_logpath: /var/log/mongodb/mongodb.log
mongodb_port: 27017
mongodb_nojournal: true
mongodb_cpu: true
mongodb_verbose: true
mongodb_quota: false
mongodb_auth: false
mongodb_objcheck: false
mongodb_diaglog: 0
mongodb_nohints: false
mongodb_nohttpinterface: false
mongodb_noscripting: false
mongodb_notablescan: false
mongodb_noprealloc: false
mongodb_replSet: ""                             # Set for enable replication
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
