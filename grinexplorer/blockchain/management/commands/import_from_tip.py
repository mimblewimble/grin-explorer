import json
from enum import Enum

import requests

from django.core.management.base import BaseCommand

from blockchain.models import Block, Input, Output, Kernel


class Status(Enum):
    CREATED = 0
    ALREADY_EXISTS = 1


class Command(BaseCommand):
    help = "Import the Blockchain starting from the current tip"

    def add_arguments(self, parser):
        parser.add_argument("url", type=str)
        parser.add_argument(
            '--full-scan',
            dest='full-scan',
            default=False,
            help="Continue scanning even if Block already exists",
        )

    def handle(self, *args, **options):
        self.API_BASE = "%s/v1/" % options["url"]

        resp = requests.get(self.API_BASE + "chain")

        try:
            data = resp.json()
        except json.decoder.JSONDecodeError:
            print("Decoding JSON failed (make sure to disable api_secret_path in grin-server.toml")
            print("resp=%r" % resp.text)
            exit()

        height = data["height"]
        tip = data["last_block_pushed"]
        self.stdout.write("height={}, tip={}\n\n".format(height, tip))

        hash = tip
        parent = None
        while True:
            (status, block_hash, prev_hash) = self.fetch_and_store_block(hash, parent)

            if not options["full-scan"] and status == Status.ALREADY_EXISTS:
                self.stdout.write("== exiting early")
                break

            if prev_hash == "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff":
                break

            # continue along the chain
            hash = prev_hash
            parent = block_hash

    def fetch_and_store_block(self, hash, parent_hash):
        resp = requests.get(self.API_BASE + "blocks/" + hash)
        try:
            block_data = resp.json()
        except json.decoder.JSONDecodeError:
            print("Decoding JSON failed (make sure to set `archive_mode=true` in grin-server.toml")
            print("resp=%r" % resp.text)
            exit()

        try:
            block = Block.objects.get(hash=hash)
            self.stdout.write("Block {} already exists @ {}".format(block.hash, block.height))

            if parent_hash is not None:
                parent = Block.objects.get(hash=parent_hash)

                if parent.previous is None:
                    assert parent.height == block.height + 1
                    parent.previous = block
                    parent.save(update_fields=["previous"])
                    self.stdout.write("Stored block {} as previous of block {}".format(block.hash[:6], parent.hash[:6]))

            return (Status.ALREADY_EXISTS, block.hash, block_data["header"]["previous"])
        except Block.DoesNotExist:
            pass

        assert hash == block_data["header"]["hash"]

        # we can't set the `previous` PK now because it doesn't exist yet. We'll
        # set it in the next call of this function, when the previous Block is saved
        previous = block_data["header"].pop("previous")

        block = Block.objects.create(
            previous=None,
            **block_data["header"],
        )
        for input_data in block_data["inputs"]:
            Input.objects.create(
                block=block,
                data=input_data,
            )

        for output_data in block_data["outputs"]:
            Output.objects.create(
                block=block,
                **output_data,
            )

        for kernel_data in block_data["kernels"]:
            Kernel.objects.create(
                block=block,
                **kernel_data,
            )

        self.stdout.write("Stored block {} @ {}".format(block.hash, block.height))
        # set parent's `previous` PK to this Block
        if parent_hash is not None:
            parent = Block.objects.get(hash=parent_hash)
            assert parent.height == block.height + 1
            parent.previous = block
            parent.save(update_fields=["previous"])
            self.stdout.write("  Marked block {} as previous of block {}".format(block.hash[:6], parent.hash[:6]))


        return (Status.CREATED, block.hash, previous)
