from django.db import models
from django.contrib.postgres.fields import ArrayField

SECOND_POW_EDGE_BITS = 29
BASE_EDGE_BITS = 24


def graph_weight(edge_bits):
    # Compute weight of a graph as number of siphash bits defining the graph
    return (2 << edge_bits-BASE_EDGE_BITS)*edge_bits


def scaled_difficulty(hash, graph_weight):
    # Difficulty achieved by this proof with given scaling factor
    diff = ((graph_weight) << 64) / int(hash[:16], 16)
    return min(diff, 0xffffffffffffffff)


def from_proof_adjusted(hash, edge_bits):
    # Computes the difficulty from a hash. Divides the maximum target by the
    # provided hash and applies the Cuck(at)oo size adjustment factor
    # scale with natural scaling factor
    return scaled_difficulty(hash, graph_weight(edge_bits))


def from_proof_scaled(hash, secondary_scaling):
    # Same as `from_proof_adjusted` but instead of an adjustment based on
    # cycle size, scales based on a provided factor. Used by dual PoW system
    # to scale one PoW against the other.
    # Scaling between 2 proof of work algos
    return scaled_difficulty(hash, secondary_scaling)


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

    prev_root = models.CharField(max_length=64)

    timestamp = models.DateTimeField(
        db_index=True,
    )

    output_root = models.CharField(max_length=64)

    range_proof_root = models.CharField(max_length=64)

    kernel_root = models.CharField(max_length=64)

    nonce = models.TextField()

    edge_bits = models.IntegerField()

    cuckoo_solution = ArrayField(models.BigIntegerField())

    difficulty = models.BigIntegerField()

    # sum of the target difficulties, not the sum of the actual block difficulties
    total_difficulty = models.BigIntegerField()

    secondary_scaling = models.IntegerField()

    total_kernel_offset = models.CharField(max_length=64)

    output_mmr_size = models.IntegerField()

    kernel_mmr_size = models.IntegerField()

    @property
    def difficulty(self):
        # Maximum difficulty this proof of work can achieve
        # 2 proof of works, Cuckoo29 (for now) and Cuckoo30+, which are scaled
        # differently (scaling not controlled for now)
        if (self.edge_bits == SECOND_POW_EDGE_BITS):
            return int(from_proof_scaled(self.hash, self.secondary_scaling))
        else:
            return int(from_proof_adjusted(self.hash, self.edge_bits))

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
        return sum([x.fee for x in self.kernel_set.all()])


class Input(models.Model):
    block = models.ForeignKey(
        to=Block,
        on_delete=models.PROTECT,
        db_index=True,
    )

    data = models.CharField(
        max_length=66,
        db_index=True,
    )


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

    commit = models.CharField(
        max_length=66,
        db_index=True,
    )

    spent = models.BooleanField()

    proof = models.TextField(null=True)

    proof_hash = models.CharField(max_length=64)

    block_height = models.IntegerField(null=True)

    merkle_proof = models.TextField(null=True)

    mmr_index = models.IntegerField(null=True)

    def occurrences(self):
        return 1

    def spent_at(self):
        return None


class Kernel(models.Model):
    block = models.ForeignKey(
        to=Block,
        on_delete=models.PROTECT,
        db_index=True,
    )

    features = models.TextField()

    fee = models.IntegerField()

    fee_shift = models.IntegerField()

    lock_height = models.IntegerField()

    excess = models.CharField(max_length=66)

    excess_sig = models.CharField(max_length=142)
