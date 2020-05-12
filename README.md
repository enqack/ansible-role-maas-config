MAAS Control
=========

Performs post install configuration of MAAS.


Requirements
------------

Roles:
  mrlesmithjr.maas


Role Variables
--------------

    vault_maas_libvirt_password: [password]


Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }


After this role is applied copy the maas user public key from each rack controller to each other rack controller.

    sudo -H -u maas ssh-copy-id maas_libvirt@[rack_host]
    

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
