import os
import sys
import ipaddress
import importlib


from unittest import TestCase

import tests.mock_tables.dbconnector
import tests.mock_tables.multi_asic

from ax_interface.mib import MIBTable
from ax_interface.pdu import PDUHeader
from ax_interface.pdu_implementations import GetPDU, GetNextPDU
from ax_interface import ValueType
from ax_interface.encodings import ObjectIdentifier
from ax_interface.constants import PduTypes
from sonic_ax_impl.mibs.ietf import rfc4363
from sonic_ax_impl.mibs.ietf import rfc4292
from sonic_ax_impl.main import SonicMIB

class TestForwardMIB(TestCase):
    @classmethod
    def setUpClass(cls):
        tests.mock_tables.dbconnector.load_namespace_config()
        importlib.reload(rfc4292)
        cls.lut = MIBTable(rfc4292.IpCidrRouteTable)
        for updater in cls.lut.updater_instances:
            updater.update_data()
            updater.reinit_data()
            updater.update_data()

    def test_update(self):
        for updater in self.lut.updater_instances:
            updater.update_data()
            updater.reinit_data()
            updater.update_data()

    def test_network_order(self):
        ip = ipaddress.ip_address("0.1.2.3")
        ipb = ip.packed
        ips = ".".join(str(int(x)) for x in list(ipb))
        self.assertEqual(ips, "0.1.2.3")

    def test_getnextpdu_first_default(self):
        # oid.include = 1
        oid = ObjectIdentifier(10, 0, 1, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        # self.assertEqual(n, 7)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.IP_ADDRESS)
        self.assertEqual(str(value0.name), '.1.3.6.1.2.1.4.24.4.1.1.0.0.0.0.0.0.0.0.0.10.0.0.1')
        self.assertEqual(str(value0.data), ipaddress.ip_address("0.0.0.0").packed.decode())

    def test_getpdu(self):
        oid = ObjectIdentifier(24, 0, 1, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 9))
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.IP_ADDRESS)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(str(value0.data), ipaddress.ip_address("0.0.0.0").packed.decode())

    def test_getnextpdu(self):
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=(
                ObjectIdentifier(21, 0, 0, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 0)),
            )
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.IP_ADDRESS)
        self.assertEqual(str(value0.data), ipaddress.ip_address("0.0.0.0").packed.decode())

    def test_getnextpdu_exactmatch(self):
        oid = ObjectIdentifier(24, 0, 1, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 3))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.IP_ADDRESS)
        print("test_getnextpdu_exactmatch: ", str(oid))
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(str(value0.data), ipaddress.ip_address("0.0.0.0").packed.decode())

    def test_getpdu_noinstance(self):
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=(
                ObjectIdentifier(20, 0, 0, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1)),
            )
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.NO_SUCH_INSTANCE)

    #test to ensure internal asic route is not present in SNMP output
    def test_getpdu_internal_noinstance(self):
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=(
                ObjectIdentifier(20, 0, 0, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 0, 0, 0, 0, 0, 10, 10, 0, 5)),
            )
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.NO_SUCH_INSTANCE)

    def test_getnextpdu_empty(self):
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=(
                ObjectIdentifier(12, 0, 0, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 1, 255)),
            )
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        n = len(response.values)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.END_OF_MIB_VIEW)

    def test_getpdu_loopback_status(self):
        loip_tuple = (10, 1, 0, 32) # ref: appl_db.json
        lomask_tuple = (255, 255, 255, 255)
        emptyip_tuple = (0, 0, 0, 0)

        oid = ObjectIdentifier(24, 0, 1, 0
            , (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 16) + loip_tuple + lomask_tuple + (0,) + emptyip_tuple
            )
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.INTEGER)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(value0.data, 1)

    def test_getnextpdu_first_default_status(self):
        oid = ObjectIdentifier(10, 0, 1, 0, (1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 16))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)

        n = len(response.values)
        # self.assertEqual(n, 7)
        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.INTEGER)
        self.assertEqual(str(value0.name), '.1.3.6.1.2.1.4.24.4.1.16.0.0.0.0.0.0.0.0.0.10.0.0.1')
        self.assertEqual(value0.data, 1)

    @classmethod
    def tearDownClass(cls):
        tests.mock_tables.dbconnector.clean_up_config()
