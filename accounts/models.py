from decimal import Decimal
from django.contrib.auth.models import AbstractBaseUser , PermissionsMixin

from django.core.validators import (MinValueValidator , MaxValueValidator)
from django.db import models
from .managers import UserManager
from .constant import GENDER_CHOICE

class User(AbstractBaseUser):
    username = None
    email = models.EmailField(unique=True , null=False , blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.email
    
    @property
    def balance(self):
        if hasattr(self , 'account'):
            return self.account.balance
        return 0
    
class BankAccountType(models.Model):
    name = models.CharField(max_length=30)
    maximum_withdrawal_amount = models.DecimalField(decimal_places=2 , max_digits= 10)
    def __str__(self):
        return self.name
    
class UserBankAccount(models.Model):
    user = models.OneToOneField(User , related_name='account' , on_delete= models.CASCADE)
    account_type = models.ForeignKey(BankAccountType , related_name='accounts' , on_delete=models.CASCADE)
    account_no = models.PositiveIntegerField(unique=True)
    gender = models.CharField(max_length=1 , choices = GENDER_CHOICE)
    brith_date = models.DateField(null=True , blank=True)
    balance = models.DecimalField(default=0 , max_digits=10 , decimal_places= 2)
    initial_deposite_date = models.DateTimeField(null=True , blank=True)
    def __str__(self):
        return str(self.account_no)
    
class UserAddress(models.Model):
    user = models.OneToOneField(User , related_name='address' , on_delete=models.CASCADE)
    street_address = models.CharField(max_length=1000)
    city = models.CharField(max_length=20)
    postal_code = models.PositiveIntegerField()
    country = models.CharField(max_length=50)
    def __str__(self) -> str:
        return self.user.email
