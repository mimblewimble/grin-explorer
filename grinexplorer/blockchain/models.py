from django.db import models


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

    total_difficulty = models.IntegerField()

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

    switch_commit_hash = models.CharField(max_length=40)

    spent = models.BooleanField()
    
    proof = models.CharField(max_length=1000)

    proof_hash = models.CharField(max_length=64)
    
    merkle_proof = models.CharField(max_length=1000)


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
