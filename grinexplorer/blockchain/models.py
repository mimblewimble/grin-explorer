from django.db import models
from django.contrib.postgres.fields import ArrayField

class Block(models.Model):
    hash = models.CharField(
        max_length=64,
        db_index=True,
        primary_key=True,
    )

    version = models.IntegerField()

    height = models.IntegerField(
        db_index=True,
    )

    previous = models.ForeignKey(
        related_name="children_set",
        to="Block",
        on_delete=models.PROTECT,
        db_index=True,
        null=True,
    )

    timestamp = models.DateTimeField()

    output_root = models.CharField(max_length=64)

    range_proof_root = models.CharField(max_length=64)

    kernel_root = models.CharField(max_length=64)

    nonce = models.TextField()

    cuckoo_size = models.IntegerField()

    cuckoo_solution = ArrayField(models.IntegerField())

    difficulty = models.IntegerField()

    # sum of the target difficulties, not the sum of the actual block difficulties
    total_difficulty = models.IntegerField()

    total_kernel_offset = models.CharField(max_length=64)

    @property
    def difficulty(self):
        return 0xffffffffffffffff // int(self.hash[:16], 16) * (self.cuckoo_size-1)*2**(self.cuckoo_size-30)

    @property
    def target_difficulty(self):
        if self.previous is None:
            return None

        return self.total_difficulty - self.previous.total_difficulty

    @property
    def reward(self):
        return 60

    @property
    def fees(self):
        return sum(self.kernel_set.all().values_list("fee", flat=True))


class Input(models.Model):
    block = models.ForeignKey(
        to=Block,
        on_delete=models.PROTECT,
        db_index=True,
    )

    data = models.CharField(max_length=66)


class Output(models.Model):
    OUTPUT_TYPE = (
        ("Transaction", "Transaction"),
        ("Coinbase", "Coinbase"),
    )

    block = models.ForeignKey(
        to=Block,
        on_delete=models.PROTECT,
        db_index=True,
    )

    output_type = models.TextField(
        choices=OUTPUT_TYPE
    )

    commit = models.CharField(max_length=66)

    spent = models.BooleanField()

    proof = models.TextField(null=True)

    proof_hash = models.CharField(max_length=64)

    merkle_proof = models.TextField(null=True)


class Kernel(models.Model):
    block = models.ForeignKey(
        to=Block,
        on_delete=models.PROTECT,
        db_index=True,
    )

    features = models.TextField()

    fee = models.IntegerField()

    lock_height = models.IntegerField()

    excess = models.CharField(max_length=66)

    excess_sig = models.CharField(max_length=142)
