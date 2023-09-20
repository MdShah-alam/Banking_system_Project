from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_list_or_404 , redirect , get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView , ListView
from transactions.constants import DEPOSIT , WITHDRAWAL , LOAN , LOAN_PAID
from datetime import datetime
from django.db.models import Sum
from transactions.forms import (
    DepositeForm ,
    WithdrawForm,
    LoanRequestForm
)
from transactions.models import Transaction

class TransactionReportView(LoginRequiredMixin , ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_date = {}
    balance = 0
    
    def get_queryset(self):
        QuerySet = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
        # Handle date parsing errors here
                start_date = end_date = None

            if start_date and end_date:
                QuerySet = QuerySet.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
                self.balance = Transaction.objects.filter(
                    timestamp__date__gte=start_date, timestamp__date__lte=end_date
                ).aggregate(Sum('amount'))['amount__sum']
            else:
                self.balance = self.request.user.account.balance
        return QuerySet.distinct()
    # def get_queryset(self):
    #     QuerySet = super().get_queryset().filter(
    #         account = self.request.user.account
    #     )
    #     start_date_str = self.request.GET.get('start_date')
    #     end_date_str = self.request.GET.get('end_date')
        
    #     if start_date_str and end_date_str:
    #         start_date = datetime.strptime(start_date_str , '%Y-%m-%d').date()
    #         end_date = datetime.strptime(end_date_str , '%Y-%m-%d').date()
    #         QuerySet = QuerySet.filter(timestamp__date__gte = start_date , timestamp__date__lte = end_date)
    #         self.balance = Transaction.objects.filter(
    #             timestamp__date__gte = start_date , timestamp__date__lte = end_date
    #         ).aaggregate(Sum('amount'))['amount_sum']
    #     else:
    #         self.balance = self.request.user.account.balance
            
    #     return QuerySet.distinct()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account':self.request.user.account,
            # 'form':TransactionDateRangeForm(self.request.GET or None)
        })
        return context
    
class TransacationCreateMixin(LoginRequiredMixin , CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs
    def get_context_data(self , **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title
        })
        return context
    
class DepositeMoneyView(TransacationCreateMixin):
    form_class = DepositeForm
    title = 'Deposit'
    def get_initial(self):
        initial = {'transaction_type' : DEPOSIT}
        return initial
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        if not account.initial_deposite_date:
            now = timezone.now()
            account.initial_deposite_date = now
        account.balance += amount
        account.save(
            update_fields = [
                'initial_deposite_date',
                'balance'
            ]
        )
        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        return super().form_valid(form)
    
class WithdrawMoneyView(TransacationCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'
    
    def get_initial(self):
        initial = {'transaction_type' : WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        if self.request.user.account.balance >= amount:
            self.request.user.account.balance -= form.cleaned_data.get('amount')
            self.request.user.account.save(update_fields = ['balance'])
        
            messages.success(
                self.request,
                f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
            )
        else:
            messages.error(self.request , f'Insufficient balance')
        return super().form_valid(form)
    
class LoanRequestView(TransacationCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'
    
    def get_initial(self):
        initial = {'transaction_type' : LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account = self.request.user.account , transaction_type = 3 , loan_approved = True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}". format(float(amount))}$ submitted successfully'
        )
        return super().form_valid(form)
    
class PayLoanView(LoginRequiredMixin , View):
    def get(self , request , loan_id):
        loan = get_object_or_404(Transaction , id = loan_id)
        if loan.loan_approved:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('transactions:loan_list')
            else:
                messages.error(
                    self.request,
                    f'Loan amount is greater than available balance'
                )
        return redirect('transaction:loan_list')
    
class LoanListView(LoginRequiredMixin , ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        user_account = self.request.user.account
        QuerySet = Transaction.objects.filter(account = user_account , transaction_type = 3)
        print(QuerySet)
        return QuerySet

