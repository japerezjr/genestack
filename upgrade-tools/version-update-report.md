# OpenStack Chart Version Update Report

**Generated:** 2026-02-03 16:17:23
**Source Release:** 2024.1/2024.2
**Target Release:** 2025.1

## Summary

- Total charts in deployment: 46
- Charts updated: 13
- Charts unchanged: 33

## Version Updates

### Core Services

| Chart | Current Version | Target Version |
|-------|----------------|----------------|
| cinder | 2024.2.409+13651f45-628a320c | 2025.1.409+13651f45-628a320c |
| glance | 2024.2.396+13651f45-628a320c | 2025.1.396+13651f45-628a320c |
| horizon | 2024.2.264+13651f45-628a320c | 2025.1.264+13651f45-628a320c |
| keystone | 2024.2.386+13651f45-628a320c | 2025.1.386+13651f45-628a320c |
| libvirt | 2024.2.94+912f85d38 | 2025.1.94+912f85d38 |
| neutron | 2024.2.529+13651f45-628a320c | 2025.1.529+13651f45-628a320c |
| nova | 2024.2.555+13651f45-628a320c | 2025.1.555+13651f45-628a320c |
| placement | 2024.2.62+13651f45-628a320c | 2025.1.62+13651f45-628a320c |

### Optional Services

| Chart | Current Version | Target Version |
|-------|----------------|----------------|
| barbican | 2024.2.208+13651f45-628a320c | 2025.1.208+13651f45-628a320c |
| ceilometer | 2024.2.115+13651f45-628a320c | 2025.1.115+13651f45-628a320c |
| gnocchi | 2024.2.52+22.15d38 | 2025.1.52+22.15d38 |
| heat | 2024.2.294+13651f45-628a320c | 2025.1.294+13651f45-628a320c |
| ironic | 2024.2.121+13651f45-628a320c | 2025.1.121+13651f45-628a320c |

## Upgrade Order Considerations

The following charts have dependencies that must be upgraded first:

- **barbican** depends on: keystone, mariadb-operator
- **ceilometer** depends on: keystone, rabbitmq
- **cinder** depends on: keystone, placement, mariadb-operator, rabbitmq
- **glance** depends on: keystone, mariadb-operator
- **gnocchi** depends on: keystone, ceilometer
- **heat** depends on: keystone, neutron, mariadb-operator
- **horizon** depends on: keystone
- **ironic** depends on: keystone, neutron, mariadb-operator
- **keystone** depends on: mariadb-operator, memcached, rabbitmq
- **neutron** depends on: keystone, mariadb-operator, rabbitmq
- **nova** depends on: keystone, placement, neutron, mariadb-operator, rabbitmq, libvirt
- **placement** depends on: keystone, mariadb-operator
