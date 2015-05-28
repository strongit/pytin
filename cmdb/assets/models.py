import netaddr

from resources.models import Resource, ResourceOption


class RegionResource(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class PortConnection(Resource):
    """
    Connection between the ports in the network
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "swport:%s <-> srvport:%s (%s Mbit)" % (self.parent.id, self.linked_port_id, self.link_speed_mbit)

    @property
    def linked_port_id(self):
        return self.get_option_value('linked_port_id', default=0)

    @linked_port_id.setter
    def linked_port_id(self, value):
        self.set_option('linked_port_id', value, format=ResourceOption.FORMAT_INT)

    @property
    def link_speed_mbit(self):
        return self.get_option_value('link_speed_mbit', default=1000)

    @link_speed_mbit.setter
    def link_speed_mbit(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('link_speed_mbit', value, format=ResourceOption.FORMAT_INT)


class SwitchPort(Resource):
    """
    Network switch port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s:%s" % (self.parent.id, self.number)

    @property
    def number(self):
        return self.get_option_value('number', default=0)

    @number.setter
    def number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value, format=ResourceOption.FORMAT_INT)


class ServerPort(SwitchPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.mac

    @property
    def mac(self):
        return self.get_option_value('mac', default="000000000000")

    @mac.setter
    def mac(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        _mac = netaddr.EUI(value, dialect=netaddr.mac_bare)

        self.set_option('mac', str(_mac).upper())


class InventoryResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s (SN: %s)" % (self.label, self.serial)

    @property
    def label(self):
        return self.get_option_value('label', default="no label")

    @label.setter
    def label(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('label', value)

    @property
    def serial(self):
        return self.get_option_value('serial', default=str(self.id))

    @serial.setter
    def serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value.lower())


class Switch(InventoryResource):
    """
    Switch object
    """

    class Meta:
        proxy = True


class GatewaySwitch(InventoryResource):
    """
    Gateway device (BGP, announce networks)
    """

    class Meta:
        proxy = True


class Server(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class VirtualServer(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class Rack(InventoryResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True
