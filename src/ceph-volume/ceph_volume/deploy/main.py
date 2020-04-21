# -*- coding: utf-8 -*-

import argparse
import json
import logging
import sys

from ceph.deployment.drive_group import DriveGroupSpec
from ceph.deployment.drive_selection.selector import DriveSelection
from ceph.deployment.translate import to_ceph_volume
from ceph.deployment.inventory import Device
from ceph_volume.inventory import Inventory
from ceph_volume.devices.lvm.batch import Batch

logger = logging.getLogger(__name__)

class Deploy(object):

    help = "Deploy OSDs according to a drive groups specification"

    def __init__(self, argv):
        logger.error(f'argv: {argv}')
        self.argv = argv

    def main(self):
        parser = argparse.ArgumentParser(
            prog='ceph-volume deploy',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=self.help,
        )
        parser.add_argument(
            'path',
            nargs='?',
            default=None,
            help=('Path to file containing drive group spec'),
        )
        parser.add_argument(
            '--dry-run',
            default=False,
            action='store_true',
            help=('dry run, only print the batch command that would be run'),
        )
        self.args = parser.parse_args(self.argv)
        commands = ''
        if self.args.path:
            with open(self.args.path, 'r') as f:
                commands = self.from_json(f)
        else:
            commands = self.from_json(sys.stdin)
        cmd = commands.run()
        logger.info('running {}'.format(cmd))
        args = cmd.split(' ')[2:]
        if self.args.dry_run:
            print(cmd)
        else:
            b = Batch(args)
            b.main()

    def from_json(self, file_):
        dg = {}
        dg = json.load(file_)
        dg_spec = DriveGroupSpec._from_json_impl(dg)
        dg_spec.validate()
        i = Inventory([])
        i.main()
        inventory = i.get_report()
        devices = [Device.from_json(i) for i in inventory]
        selection = DriveSelection(dg_spec, devices)
        return to_ceph_volume(selection)
