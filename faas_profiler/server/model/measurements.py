

from marshmallow import Schema, fields

#
# Common
#


class CommonWallTimeSchema(Schema):
    wall_time = fields.Float()

#
# Information
#


class InformationEnvironmentSchema(Schema):
    runtime = fields.Str()
    platform = fields.Str()
    interpreter_path = fields.Str()
    byte_order = fields.Str()
    packages = fields.List(fields.Str())


class InformationOperatingSystemSchema(Schema):
    boot_time = fields.DateTime()
    system = fields.Str()
    node_name = fields.Str()
    release = fields.Str()
    machine = fields.Str()

#
# Memory
#


class MemoryUsageSchema(Schema):
    average_usage: fields.Float()
    measuring_points: fields.List(
        fields.Dict(
            timestamp=fields.Float(),
            data=fields.Float()
        ))

#
# CPU
#


class CPUUsage(Schema):
    average_usage: fields.Float()
    measuring_points: fields.List(
        fields.Dict(
            timestamp=fields.Float(),
            data=fields.Float()
        ))

#
# Network
#


class NetworkConnections(Schema):
    connections = fields.List(
        fields.Dict(
            socket_descriptor=fields.Int(required=True),
            family=fields.Str(),
            local_address=fields.Str(),
            remote_address=fields.Str()
        ))


class NetworkIOCounters(Schema):
    interfaces = fields.List(
        fields.Dict(
            interface=fields.Str(required=True),
            bytes_sent=fields.Int(),
            bytes_recv=fields.Int(),
            packets_sent=fields.Int(),
            packets_recv=fields.Int()
        ),
        missing=[]
    )
    total = fields.Dict(
        bytes_sent=fields.Int(),
        bytes_recv=fields.Int(),
        packets_sent=fields.Int(),
        packets_recv=fields.Int()
    )
