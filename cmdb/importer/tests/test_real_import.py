import os

from django.test import TestCase

from assets.models import RegionResource, ServerPort, Server, VirtualServer, GatewaySwitch, PortConnection, Switch, \
    VirtualServerPort
from importer.importlib import GenericCmdbImporter

from importer.providers.vendors.qtech import QtechL3Switch, Qtech3400Switch
from ipman.models import IPNetworkPool, IPAddress


class QSW8300ImportDataTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_import_data(self):
        arp_file_path = os.path.join(self.DATA_DIR, 'arp-table.txt')
        mac_file_path = os.path.join(self.DATA_DIR, 'mac-table.txt')

        cmdb_importer = GenericCmdbImporter()

        # create IP pools and basic structure
        dc_anders = RegionResource.objects.create(name="Anders")
        dc_rtcom = RegionResource.objects.create(name="Rostelecom")

        # create source switch
        anders_gw = GatewaySwitch.objects.create(name="baxet-gw-q", parent=dc_anders)

        # arp table provider
        qtech_switch = QtechL3Switch()
        qtech_switch.from_arp_dump(arp_file_path)

        switch_ports = list(qtech_switch.ports)

        self.assertEqual(12, len(switch_ports))

        # Add our IP pools
        pool_list = [IPNetworkPool.objects.create(network='46.17.40.0/23', parent=dc_anders),
                     IPNetworkPool.objects.create(network='46.17.44.0/23', parent=dc_anders),
                     IPNetworkPool.objects.create(network='176.32.34.0/23', parent=dc_anders),
                     IPNetworkPool.objects.create(network='176.32.36.0/24', parent=dc_anders),
                     IPNetworkPool.objects.create(network='176.32.37.0/24', parent=dc_anders),
                     IPNetworkPool.objects.create(network='176.32.38.0/24', parent=dc_anders),
                     IPNetworkPool.objects.create(network='176.32.39.0/24', parent=dc_anders),
                     IPNetworkPool.objects.create(network='2a00:b700::/48', parent=dc_anders),
                     IPNetworkPool.objects.create(network='46.17.46.0/23', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='46.29.160.0/23', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='176.32.32.0/23', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='46.29.162.0/23', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='46.29.164.0/22', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='185.22.152.0/22', parent=dc_rtcom),
                     IPNetworkPool.objects.create(network='2a00:b700:1::/48', parent=dc_rtcom)]

        # Double the proccess, to test data update process
        cmdb_importer.import_switch(anders_gw.id, qtech_switch)
        cmdb_importer.import_switch(anders_gw.id, qtech_switch)

        # -1 IP: 87.251.133.9, /30 peering network address
        self.assertEqual(1328, len(IPAddress.active.filter()))

        for pool in pool_list:
            print "%s - %d" % (pool, pool.usage)

        # count servers
        self.assertEqual(71, len(Server.active.filter()))
        self.assertEqual(39, len(VirtualServer.active.filter()))
        self.assertEqual(71, len(ServerPort.active.filter()))
        self.assertEqual(0, len(ServerPort.active.filter(parent=None)))
        self.assertEqual(39, len(VirtualServerPort.active.filter()))
        self.assertEqual(10, len(PortConnection.active.filter()))

        # import MAC data from mac table
        anders_sw1 = Switch.objects.create(name="baxet-sw-1", parent=dc_anders)
        qtech3400_switch = Qtech3400Switch()
        qtech3400_switch.from_mac_dump(mac_file_path)

        # double call, to check update
        cmdb_importer.import_switch(anders_sw1.id, qtech3400_switch)
        cmdb_importer.import_switch(anders_sw1.id, qtech3400_switch)

        # count servers
        self.assertEqual(76, len(Server.active.filter()))
        self.assertEqual(41, len(VirtualServer.active.filter()))
        self.assertEqual(76, len(ServerPort.active.filter()))
        self.assertEqual(0, len(ServerPort.active.filter(parent=None)))
        self.assertEqual(41, len(VirtualServerPort.active.filter()))
        self.assertEqual(54, len(PortConnection.active.filter()))

        # Linked VPS
        self.assertEqual(3, len(VirtualServer.active.filter(parent=619)))
        self.assertEqual(4, len(VirtualServer.active.filter(parent=740)))

        # Guessed roles
        self.assertEqual(3, len(Server.active.filter(guessed_role='hypervisor')))
        for srv in Server.active.filter(guessed_role='hypervisor'):
            print srv.id
            for srv_port in srv:
                print "    %s" % srv_port

        srv_port = ServerPort.active.filter(mac='001517E69D70')[0]
        self.assertEqual(4, len(VirtualServer.active.filter(parent=srv_port.parent)))
