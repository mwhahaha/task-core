# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""task-core cli"""
import argparse
import logging
import os
import pprint
import sys
from datetime import datetime

from taskflow import engines

from .exceptions import UnavailableException
from .logging import setup_basic_logging
from .manager import TaskManager

LOG = logging.getLogger(__name__)


class Cli:
    """task-core cli"""

    def __init__(self):
        self._parser = argparse.ArgumentParser(description="")

    @property
    def parser(self):
        return self._parser

    def parse_args(self):
        self.parser.add_argument(
            "-s",
            "--services-dir",
            required=True,
            help=("Path to a directory containing service definitions"),
        )
        self.parser.add_argument(
            "-i",
            "--inventory-file",
            required=True,
            help=("Path to an inventory file containing hosts to role mappings"),
        )
        self.parser.add_argument(
            "-r",
            "--roles-file",
            required=True,
            help=("Path to a roles file containing roles to service mappings"),
        )
        self.parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            default=False,
            help=("Enable debug logging"),
        )
        self.parser.add_argument(
            "--noop",
            action="store_true",
            default=False,
            help=("Do not run the deployment, only process the tasks"),
        )
        args = self.parser.parse_args()
        return args


def main():
    """task-core"""
    start = datetime.now()
    cli = Cli()
    args = cli.parse_args()

    setup_basic_logging(args.debug)
    mgr = TaskManager(args.services_dir, args.inventory_file, args.roles_file)
    flow = mgr.create_flow()

    if not args.noop:
        LOG.info("Starting execution...")
        e = engines.load(flow, executor="threaded", engine="parallel", max_workers=5)
        e.run()
        result = e.storage.fetch_all()
        LOG.info("Ran %s tasks...", len(result.keys()))
        LOG.info("Stats: %s", e.statistics)
    else:
        result = None
        try:
            mgr.write_flow_graph(flow, "noop.svg")
            LOG.info("Task graph written out to noop.svg")
        except UnavailableException:
            pass
        LOG.info("Skipping execution due to --noop...")
    end = datetime.now()
    LOG.info("Elapsed time: %s", end - start)
    LOG.info("Done...")
    LOG.debug(result)


def example():
    """task-core-example"""
    start = datetime.now()
    setup_basic_logging(True)

    services_dir = os.path.join(
        sys.prefix, "share", "task-core", "examples", "framework", "services"
    )
    inventory_file = os.path.join(
        sys.prefix, "share", "task-core", "examples", "framework", "inventory.yaml"
    )
    roles_file = os.path.join(
        sys.prefix, "share", "task-core", "examples", "framework", "roles.yaml"
    )
    mgr = TaskManager(services_dir, inventory_file, roles_file)
    flow = mgr.create_flow()

    LOG.info("Running...")
    result = engines.run(flow, engine="parallel")
    LOG.info("Ran %s tasks...", len(result.keys()))
    end = datetime.now()
    LOG.info("Elapsed time: %s", end - start)
    LOG.info("Done...")
    pprint.pprint(result)


if __name__ == "__main__":
    example()
