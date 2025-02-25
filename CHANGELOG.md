# Changelog

## unreleased

## v2.5.0

* bump protocol to 25
* `device_type` in heartbeat now shows protocol version
* add flash rgb led command
* add `command` to cli

## v2.4.0

* add `CommandMessage` to protocol
* bump protocol version to 24
* add `clear-errors` command to cli


## v2.3.0

* include firmware in library
* use firmware code for mock


## v2.2.0

* bump protocol to version 23
* refactor protocol messages, to make it simpler, remove parameters.
* refactor `get_can_bus` function to accept named parameter
* add dbc file generation
    - `invoke create-dbc` tool
    - `rox_icu.dbc.get_dbc()` - path to file
    - `rox_icu.can_utils.create_dbc(node_id=10)` - build dbc, return database


## v2.1.0

* change can config env variable to `ICU_CAN_CHANNEL` and `ICU_CAN_INTERFACE`

## v2.0.0

* update protocol to version 12
* add generic device parameters


## v1.0.0

* update can protocol to version 11.
* update tooling to work with can protocol 11
* add mqtt interface to mock.


## v0.5.0

* add `icu inspect`
* fix `icu output` bug using wrong message
