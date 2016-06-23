# Copyright 2016 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import time
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test
from tempest.lis import manager
from oslo_log import log as logging
from tempest.scenario import utils as test_utils

CONF = config.CONF

LOG = logging.getLogger(__name__)


class LinuxNext(manager.LisBase):

    def setUp(self):
        super(LinuxNext, self).setUp()
        # Setup image and flavor the test instance
        # Support both configured and injected values
        if not hasattr(self, 'image_ref'):
            self.image_ref = CONF.compute.image_ref
        if not hasattr(self, 'flavor_ref'):
            self.flavor_ref = CONF.compute.flavor_ref

        self.image_utils = test_utils.ImageUtils(self.manager)
        if not self.image_utils.is_flavor_enough(self.flavor_ref,
                                                 self.image_ref):
            raise self.skipException(
                '{image} does not fit in {flavor}'.format(
                    image=self.image_ref, flavor=self.flavor_ref
                )
            )
        self.disks = []
        self.file_system = 'ext4'
        self.sector_size = 512
        self.size = '20GB'
        self.disk_type = 'vhdx'
        self.position = ('SCSI', 1, 1)
        self.host_name = ""
        self.instance_name = ""
        self.run_ssh = CONF.validation.run_validation and \
            self.image_utils.is_sshable_image(self.image_ref)
        self.ssh_user = CONF.validation.image_ssh_user
        LOG.debug('Starting test for i:{image}, f:{flavor}. '
                  'Run ssh: {ssh}, user: {ssh_user}'.format(
                      image=self.image_ref, flavor=self.flavor_ref,
                      ssh=self.run_ssh, ssh_user=self.ssh_user))

    def install_linux_next(self):
        try:
            script_name = 'install_linux_next.sh'
            script_path = '/scripts/' + script_name
            destination = '/tmp/'
            my_path = os.path.abspath(
                os.path.normpath(os.path.dirname(__file__)))
            full_script_path = my_path + script_path
            cmd_params = []
            self.linux_client.execute_script(
                script_name, cmd_params, full_script_path, destination)

        except lib_exc.SSHExecCommandFailed as exc:

            LOG.exception(exc)
            self._log_console_output()
            raise exc

        except Exception as exc:
            LOG.exception(exc)
            self._log_console_output()
            raise exc

    def check_lis_modules(self):
        try:
            script_name = 'LIS_verifyHyperVIC.sh'
            script_path = '/../core/scripts/' + script_name
            destination = '/tmp/'
            my_path = os.path.abspath(
                os.path.normpath(os.path.dirname(__file__)))
            full_script_path = my_path + script_path
            cmd_params = []
            self.linux_client.execute_script(
                script_name, cmd_params, full_script_path, destination)

        except lib_exc.SSHExecCommandFailed as exc:

            LOG.exception(exc)
            self._log_console_output()
            raise exc

        except Exception as exc:
            LOG.exception(exc)
            self._log_console_output()
            raise exc

    def linux_next_daemons(self):
        try:
            script_name = 'linux_next_daemons.sh'
            script_path = '/scripts/' + script_name
            destination = '/tmp/'
            my_path = os.path.abspath(
                os.path.normpath(os.path.dirname(__file__)))
            full_script_path = my_path + script_path
            cmd_params = []
            self.linux_client.execute_script(
                script_name, cmd_params, full_script_path, destination)

        except lib_exc.SSHExecCommandFailed as exc:

            LOG.exception(exc)
            self._log_console_output()
            raise exc

        except Exception as exc:
            LOG.exception(exc)
            self._log_console_output()
            raise exc

    @test.attr(type=['smoke', 'core', 'next'])
    @test.services('compute', 'network')
    def test_linux_next(self):
        self.spawn_vm()
        self.stop_vm(self.server_id)
        vcpu_count = self.get_cpu_settings(self.instance_name)
        memory_assigned = self.get_ram_settings(self.instance_name)
        self.change_cpu(self.instance_name, 12)
        self.set_ram_settings(self.instance_name, 8192)
        position = ('SCSI', 0, 1)
        self.add_disk(self.instance_name, self.disk_type,
                      position, 'Dynamic', self.sector_size, self.size)
        self.start_vm(self.server_id)
        self._initiate_linux_client(self.floating_ip['floatingip']['floating_ip_address'],
                                    self.ssh_user, self.keypair['private_key'])
        self.format_disk(1, 'ext4')
        self.linux_client.mount('sdb1')
        self.install_linux_next()

        self.stop_vm(self.server_id)
        self.start_vm(self.server_id)
        self._initiate_linux_client(self.floating_ip['floatingip']['floating_ip_address'],
                                    self.ssh_user, self.keypair['private_key'])
        self.linux_client.mount('sdb1')
        self.linux_next_daemons()
        self.stop_vm(self.server_id)
        self.change_cpu(self.instance_name, vcpu_count)
        self.set_ram_settings(self.instance_name, memory_assigned)
        for disk in self.disks:
            self.detach_disk(self.instance_name, disk)
        snapshot_image = self.create_server_snapshot_nocleanup(
            server=self.instance)
        # boot a second instance from the snapshot
        self.image_ref = snapshot_image['id']
        self.servers_client.delete_server(self.instance['id'])
        self.spawn_vm()
        self.verify_lis(self.instance_name, 'Heartbeat')
        self._initiate_linux_client(self.floating_ip['floatingip']['floating_ip_address'],
                                    self.ssh_user, self.keypair['private_key'])
        self.check_lis_modules()
        self.servers_client.delete_server(self.instance['id'])
