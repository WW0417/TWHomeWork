#!/bin/bash
ansible-playbook -i ansible/hosts --key-file "./.vagrant/machines/dev/virtualbox/private_key" ansible/refresh.yml
