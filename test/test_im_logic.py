#! /usr/bin/env python
#
# IM - Infrastructure Manager
# Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import unittest
import sys
from mock import Mock

sys.path.append("..")
sys.path.append(".")

from IM.config import Config
# To load the ThreadPool class
Config.MAX_SIMULTANEOUS_LAUNCHES = 2

from IM.VirtualMachine import VirtualMachine
from IM.InfrastructureManager import InfrastructureManager as IM
from IM.auth import Authentication
from radl.radl import RADL, system, deploy, Feature, SoftFeatures
from radl.radl_parse import parse_radl
from IM.CloudInfo import CloudInfo
from IM.connectors.CloudConnector import CloudConnector
from IM.tosca.Tosca import Tosca


class TestIM(unittest.TestCase):

    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)

    def setUp(self):

        IM._reinit()
        # Patch save_data
        IM.save_data = staticmethod(lambda *args: None)

    def tearDown(self):
        IM.stop()

    @staticmethod
    def getAuth(im_users=[], vmrc_users=[], clouds=[]):
        return Authentication([
            {'id': 'im%s' % i, 'type': 'InfrastructureManager', 'username': 'user%s' % i,
             'password': 'pass%s' % i} for i in im_users] + [
            {'id': 'vmrc%s' % i, 'type': 'VMRC', 'username': 'vmrcuser%s' % i,
             'password': 'pass%s' % i, 'host': 'hostname'} for i in vmrc_users] + [
            {'id': 'cloud%s' % i, 'type': c, 'username': 'user%s' % i,
             'password': 'pass%s' % i} for c, i in clouds])

    def register_cloudconnector(self, name, cloud_connector):
        sys.modules['IM.connectors.' + name] = type('MyConnector', (object,),
                                                    {name + 'CloudConnector': cloud_connector})

    def gen_launch_res(self, inf, radl, requested_radl, num_vm, auth_data):
        res = []
        for _ in range(num_vm):
            cloud = CloudInfo()
            cloud.type = "Dummy"
            vm = VirtualMachine(inf, "1234", cloud, radl, requested_radl)
            res.append((True, vm))
        return res

    def get_cloud_connector_mock(self, name="MyMock0"):
        cloud = type(name, (CloudConnector, object), {})
        cloud.launch = Mock(side_effect=self.gen_launch_res)
        return cloud

    def test_inf_creation0(self):
        """Create infrastructure with empty RADL."""

        auth0 = self.getAuth([0])
        infId = IM.CreateInfrastructure("", auth0)
        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_auth(self):
        """Create infrastructure with empty RADL."""

        auth0, auth1 = self.getAuth([0]), self.getAuth([1])
        infId0 = IM.CreateInfrastructure("", auth0)
        infId1 = IM.CreateInfrastructure("", auth1)
        with self.assertRaises(Exception) as ex:
            IM.DestroyInfrastructure(infId0, auth1)
        self.assertEqual(str(ex.exception),
                         "Invalid infrastructure ID or access not granted.")
        with self.assertRaises(Exception) as ex:
            IM.DestroyInfrastructure(infId1, auth0)
        self.assertEqual(str(ex.exception),
                         "Invalid infrastructure ID or access not granted.")
        IM.DestroyInfrastructure(infId0, auth0)
        IM.DestroyInfrastructure(infId1, auth1)

    def test_inf_addresources_without_credentials(self):
        """Deploy single virtual machine without credentials to check that it raises the correct exception."""

        radl = RADL()
        radl.add(
            system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure("", auth0)

        with self.assertRaises(Exception) as ex:
            IM.AddResource(infId, str(radl), auth0)

        self.assertIn("No username", ex.exception.message)

        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_addresources0(self):
        """Deploy single virtual machines and test reference."""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure("", auth0)

        vms = IM.AddResource(infId, str(radl), auth0)
        self.assertEqual(vms, [0])

        # Test references
        radl = RADL()
        radl.add(system("s0", reference=True))
        radl.add(deploy("s0", 1))
        vms = IM.AddResource(infId, str(radl), auth0)
        self.assertEqual(vms, [1])

        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_addresources1(self):
        """Deploy n independent virtual machines."""

        n = 80  # Machines to deploy
        Config.MAX_SIMULTANEOUS_LAUNCHES = n / 2  # Test the pool
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", n))
        cloud = self.get_cloud_connector_mock()
        self.register_cloudconnector("Mock", cloud)
        auth0 = self.getAuth([0], [], [("Mock", 0)])
        infId = IM.CreateInfrastructure("", auth0)
        vms = IM.AddResource(infId, str(radl), auth0)
        self.assertEqual(len(vms), n)
        self.assertEqual(cloud.launch.call_count, n)
        for call, _ in cloud.launch.call_args_list:
            self.assertEqual(call[3], 1)
        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_addresources2(self):
        """Deploy independent virtual machines in two cloud providers."""

        n0, n1 = 2, 5  # Machines to deploy
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(system("s1", [Feature("disk.0.image.url", "=", "mock1://wind.ows.suc.kz"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.private_key", "=", "private_key")]))
        radl.add(deploy("s0", n0))
        radl.add(deploy("s1", n1))

        Config.MAX_SIMULTANEOUS_LAUNCHES = 10

        def concreteSystem(s, cloud_id):
            url = s.getValue("disk.0.image.url")
            return [s.clone()] if url.partition(":")[0] == cloud_id else []
        cloud0 = self.get_cloud_connector_mock("MyMock0")
        cloud0.concreteSystem = lambda _0, s, _1: concreteSystem(s, "mock0")
        self.register_cloudconnector("Mock0", cloud0)
        cloud1 = self.get_cloud_connector_mock("MyMock1")
        cloud1.concreteSystem = lambda _0, s, _1: concreteSystem(s, "mock1")
        self.register_cloudconnector("Mock1", cloud1)
        auth0 = self.getAuth([0], [], [("Mock0", 0), ("Mock1", 1)])
        infId = IM.CreateInfrastructure("", auth0)
        vms = IM.AddResource(infId, str(radl), auth0)
        self.assertEqual(len(vms), n0 + n1)
        self.assertEqual(cloud0.launch.call_count, n0)
        self.assertEqual(cloud1.launch.call_count, n1)
        for call, _ in cloud0.launch.call_args_list + cloud1.launch.call_args_list:
            self.assertEqual(call[3], 1)
        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_addresources3(self):
        """Test cloud selection."""

        n0, n1 = 2, 5  # Machines to deploy
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               SoftFeatures(
                                   10, [Feature("memory.size", "<=", 500)]),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(system("s1", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               SoftFeatures(
                                   10, [Feature("memory.size", ">=", 800)]),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", n0))
        radl.add(deploy("s1", n1))

        Config.MAX_SIMULTANEOUS_LAUNCHES = 10

        def concreteSystem(s, mem):
            return [system(s.name, [Feature("memory.size", "=", mem)])]
        cloud0 = self.get_cloud_connector_mock("MyMock0")
        cloud0.concreteSystem = lambda _0, s, _1: concreteSystem(s, 500)
        self.register_cloudconnector("Mock0", cloud0)
        cloud1 = self.get_cloud_connector_mock("MyMock1")
        cloud1.concreteSystem = lambda _0, s, _1: concreteSystem(s, 1000)
        self.register_cloudconnector("Mock1", cloud1)
        auth0 = self.getAuth([0], [0], [("Mock0", 0), ("Mock1", 1)])
        infId = IM.CreateInfrastructure("", auth0)
        vms = IM.AddResource(infId, str(radl), auth0)
        self.assertEqual(len(vms), n0 + n1)
        self.assertEqual(cloud0.launch.call_count, n0)
        self.assertEqual(cloud1.launch.call_count, n1)
        for call, _ in cloud0.launch.call_args_list + cloud1.launch.call_args_list:
            self.assertEqual(call[3], 1)
        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_cloud_order(self):
        """Test cloud selection in base of the auth data order."""

        n0, n1 = 1, 1  # Machines to deploy
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("cpu.count", "=", 1),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", n0))
        radl.add(system("s1", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("cpu.count", "=", 1),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s1", n1))

        cloud0 = self.get_cloud_connector_mock("MyMock0")
        self.register_cloudconnector("Mock0", cloud0)
        cloud1 = self.get_cloud_connector_mock("MyMock1")
        self.register_cloudconnector("Mock1", cloud1)
        auth0 = self.getAuth([0], [0], [("Mock0", 0), ("Mock1", 1)])
        infId = IM.CreateInfrastructure(str(radl), auth0)
        self.assertEqual(cloud0.launch.call_count, n0 + n1)
        IM.DestroyInfrastructure(infId, auth0)

    def test_get_infrastructure_list(self):
        """Get infrastructure List."""

        auth0 = self.getAuth([0])
        infId = IM.CreateInfrastructure("", auth0)
        inf_ids = IM.GetInfrastructureList(auth0)
        self.assertEqual(inf_ids, [infId])
        IM.DestroyInfrastructure(infId, auth0)

    def test_reconfigure(self):
        """Reconfigure."""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)

        reconf_radl = """configure test (\n@begin\n---\n  - tasks:\n      - debug: msg="RECONFIGURERADL"\n@end\n)"""
        IM.Reconfigure(infId, reconf_radl, auth0)
        IM.Reconfigure(infId, reconf_radl, auth0, ['0'])

        IM.DestroyInfrastructure(infId, auth0)

    def test_inf_removeresources(self):
        """Deploy 4 VMs and remove 2"""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 4))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)
        cont = IM.RemoveResource(infId, ['0', '1'], auth0)
        self.assertEqual(cont, 2)
        vms = IM.GetInfrastructureInfo(infId, auth0)
        self.assertEqual(sorted(vms), ['2', '3'])

        IM.DestroyInfrastructure(infId, auth0)

    def test_get_vm_info(self):
        """
        Test GetVMInfo and GetVMProperty and GetVMContMsg and GetInfrastructureRADL and
        GetInfrastructureContMsg and GetInfrastructureState.
        """
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)

        radl_info = IM.GetVMInfo(infId, "0", auth0)
        parsed_radl_info = parse_radl(str(radl_info))
        self.assertEqual(parsed_radl_info.systems[0].getValue("state"), "running")

        state = IM.GetVMProperty(infId, "0", "state", auth0)
        self.assertEqual(state, "running")

        contmsg = IM.GetVMContMsg(infId, "0", auth0)
        self.assertEqual(contmsg, "")

        contmsg = IM.GetInfrastructureContMsg(infId, auth0)

        state = IM.GetInfrastructureState(infId, auth0)
        self.assertEqual(state["state"], "running")
        self.assertEqual(state["vm_states"]["0"], "running")

        radl_info = IM.GetInfrastructureRADL(infId, auth0)
        parsed_radl_info = parse_radl(str(radl_info))
        self.assertEqual(parsed_radl_info.systems[0].getValue("disk.0.os.credentials.username"), "user")

        IM.DestroyInfrastructure(infId, auth0)

    def test_altervm(self):
        """Test AlterVM"""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("cpu.count", "=", 1),
                               Feature("memory.size", "=", 512, "M"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)

        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("cpu.count", "=", 2),
                               Feature("memory.size", "=", 1024, "M"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        radl_info = IM.AlterVM(infId, "0", str(radl), auth0)
        parsed_radl_info = parse_radl(str(radl_info))
        self.assertEqual(parsed_radl_info.systems[0].getValue("cpu.count"), 2)
        self.assertEqual(parsed_radl_info.systems[0].getFeature('memory.size').getValue('M'), 1024)

        IM.DestroyInfrastructure(infId, auth0)

    def test_start_stop(self):
        """Test Start and Stop operations"""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)

        res = IM.StopInfrastructure(infId, auth0)
        self.assertEqual(res, "")
        res = IM.StartInfrastructure(infId, auth0)
        self.assertEqual(res, "")

        res = IM.StartVM(infId, "0", auth0)
        self.assertEqual(res, "")
        res = IM.StopVM(infId, "0", auth0)
        self.assertEqual(res, "")

        IM.DestroyInfrastructure(infId, auth0)

    def test_export_import(self):
        """Test ExportInfrastructure and ImportInfrastructure operations"""
        radl = RADL()
        radl.add(system("s0", [Feature("disk.0.image.url", "=", "mock0://linux.for.ev.er"),
                               Feature("disk.0.os.credentials.username", "=", "user"),
                               Feature("disk.0.os.credentials.password", "=", "pass")]))
        radl.add(deploy("s0", 1))

        auth0 = self.getAuth([0], [], [("Dummy", 0)])
        infId = IM.CreateInfrastructure(str(radl), auth0)

        res = IM.ExportInfrastructure(infId, True, auth0)
        new_inf_id = IM.ImportInfrastructure(res, auth0)

        IM.DestroyInfrastructure(new_inf_id, auth0)

    def test_tosca_to_radl(self):
        """Test TOSCA RADL translation"""
        TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
        with open(TESTS_PATH + '/tosca_create.yml') as f:
            tosca_data = f.read()
        tosca = Tosca(tosca_data)
        _, radl = tosca.to_radl()
        parse_radl(str(radl))

if __name__ == "__main__":
    unittest.main()
