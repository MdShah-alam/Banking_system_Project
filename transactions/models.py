from django.db import models

# Create your models here.

from accounts.models import UserBankAccount
from .constants import TRANSACTION_TYPE_CHOICES

class Transaction(models.Model):
    account = models.ForeignKey(UserBankAccount , related_name= 'transaction' , on_delete= models.CASCADE , null=True , blank=True)
    amount = models.DecimalField(decimal_places= 2 , max_digits=10 , null=False)
    balance_after_transaction = models.DecimalField(decimal_places= 2 , max_digits=10 , null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    loan_approved = models.BooleanField(default = False)
    transaction_type = models.PositiveIntegerField(choices=TRANSACTION_TYPE_CHOICES , null= True)
    class Meta:
        ordering = ['timestamp']
