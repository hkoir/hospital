from decimal import Decimal
from datetime import date
from accounting.models import JournalEntry, JournalEntryLine, FiscalYear, Account

import logging
logger = logging.getLogger(__name__)


def create_journal_entry_for_purchase(purchase_payment, description="", vat_amount=0, ait_amount=0, created_by=None):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    total_amount = Decimal(purchase_payment.total_amount)
    vat_amount = Decimal(vat_amount or 0)
    ait_amount = Decimal(ait_amount or 0)
    net_payable = total_amount + vat_amount - ait_amount

    # Create journal entry
    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description or f"Purchase entry for {purchase_payment.purchase_invoice.purchase_shipment.purchase_order.supplier.name}",
        reference=f"PUR-{purchase_payment.id}",
        created_by=created_by
    )

    # Get accounts
    try:
        expense_account = Account.objects.get(code="5110")      # purchase Expenses
        inventory_account = Account.objects.get(code="1300")    # Inventory
        cash_account = Account.objects.get(code="1110")         # Cash
        accounts_payable = Account.objects.get(code="2110")     # Accounts Payable - Trade
        input_vat = Account.objects.get(code="1610")            # Input VAT Recoverable
        ait_payable = Account.objects.get(code="2200")          # AIT Payable
    except Account.DoesNotExist as e:
        raise ValueError(f"Missing required account: {e}")

    # Determine debit account (Inventory or Expense)
    purchase_account = inventory_account if purchase_payment.purchase_invoice.purchase_shipment.purchase_order.is_inventory else expense_account

    # Debit: Purchase amount
    JournalEntryLine.objects.create(
        entry=entry,
        account=purchase_account,
        description="Goods/Services purchased",
        debit=total_amount,
        credit=0
    )

    # Debit: Input VAT (if any)
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=input_vat,
            description="Input VAT Recoverable",
            debit=vat_amount,
            credit=0
        )

    # Credit: AIT Payable (if any)
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable,
            description="AIT deducted at source",
            debit=0,
            credit=ait_amount
        )

    # Credit: Payment account (Cash/Bank) or Accounts Payable
    if purchase_payment.payment_method == "CASH":
        payment_account = cash_account
    elif purchase_payment.payment_method == "BANK" and purchase_payment.bank_account:
        # Use bank account as payment account
        payment_account, _ = Account.objects.get_or_create(
            code=f"BANK-{purchase_payment.bank_account.id}",
            defaults={'name': purchase_payment.bank_account.name, 'type': 'ASSET'}
        )
    else:
        payment_account = accounts_payable

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description="Payment made or payable",
        debit=0,
        credit=net_payable
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")
    return entry

from decimal import Decimal
from datetime import date
from accounting.models import JournalEntry, JournalEntryLine, FiscalYear, Account


def create_journal_entry_for_direct_purchase(
        supplier_name,
        total_amount,
        vat_amount=0,
        ait_amount=0,
        payment_method="CASH",  # CASH / BANK / CREDIT
        bank_account_code=None,  # only required if payment_method == BANK
        description="",
        created_by=None
    ):
 
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    total_amount = Decimal(total_amount)
    vat_amount = Decimal(vat_amount or 0)
    ait_amount = Decimal(ait_amount or 0)
    net_payable = total_amount + vat_amount - ait_amount

    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description or f"Direct purchase from {supplier_name}",
        reference=f"PUR-{date.today().strftime('%Y%m%d')}-{supplier_name}",
        created_by=created_by
    )

    # Get required accounts
    try:
        expense_account = Account.objects.get(code="5110")      # Purchase Expense
        inventory_account = Account.objects.get(code="1300")    # Inventory
        cash_account = Account.objects.get(code="1110")         # Cash on Hand
        accounts_payable = Account.objects.get(code="2110")     # Accounts Payable
        input_vat = Account.objects.get(code="1610")            # Input VAT Recoverable
        ait_payable = Account.objects.get(code="2220")          # AIT Payable
    except Account.DoesNotExist as e:
        raise ValueError(f"Missing required account: {e}")

    # Determine debit account: Inventory or Expense (assume inventory purchase)
    purchase_account = inventory_account

    # Debit: Purchase amount
    JournalEntryLine.objects.create(
        entry=entry,
        account=purchase_account,
        description=f"Purchase from {supplier_name}",
        debit=total_amount,
        credit=0
    )

    # Debit: VAT
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=input_vat,
            description="Input VAT",
            debit=vat_amount,
            credit=0
        )

    # Credit: AIT
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable,
            description="AIT Deducted at Source",
            debit=0,
            credit=ait_amount
        )

    # Credit: Payment account
    if payment_method.upper() == "CASH":
        payment_account = cash_account
    elif payment_method.upper() == "BANK":
        if not bank_account_code:
            raise ValueError("Bank account code required for BANK payment method")
        payment_account, _ = Account.objects.get_or_create(
            code=bank_account_code,
            defaults={"name": f"Bank Account {bank_account_code}", "type": "ASSET"}
        )
    else:
        payment_account = accounts_payable  # Credit purchase on account

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description=f"Payment via {payment_method}",
        debit=0,
        credit=net_payable
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry




def create_journal_entry_for_direct_purchase_invoice(payment, description="", created_by=None):

    if not hasattr(payment, 'purchase_invoice') or not payment.purchase_invoice:
        raise ValueError("Payment must be linked to a purchase invoice.")

    invoice = payment.purchase_invoice
    supplier_name = getattr(invoice, 'supplier_name', f"Invoice-{invoice.id}")

    # Ensure totals are calculated
    invoice.calculate_totals()

    subtotal = Decimal(invoice.subtotal or 0)
    vat_amount = Decimal(invoice.vat_amount or 0)
    ait_amount = Decimal(invoice.ait_amount or 0)
    net_due_amount = Decimal(invoice.net_due_amount or 0)

    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description or f"Direct purchase from {supplier_name}",
        reference=f"PUR-{invoice.id}-{payment.id}",
        created_by=created_by
    )

    # Accounts
    try:
        inventory_account = Account.objects.get(code="1300")
        cash_account = Account.objects.get(code="1110")
        accounts_payable = Account.objects.get(code="2110")
        input_vat = Account.objects.get(code="1610")
        ait_payable = Account.objects.get(code="2220")
    except Account.DoesNotExist as e:
        raise ValueError(f"Missing required account: {e}")

    # Debit: Inventory / Purchase
    JournalEntryLine.objects.create(
        entry=entry,
        account=inventory_account,
        description=f"Purchase from {supplier_name}",
        debit=subtotal,
        credit=0
    )

    # Debit: Input VAT
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=input_vat,
            description="Input VAT",
            debit=vat_amount,
            credit=0
        )

    # Credit: AIT
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable,
            description="AIT deducted at source",
            debit=0,
            credit=ait_amount
        )

    # Credit: Payment / Accounts Payable
    payment_method = getattr(payment, 'payment_method', 'CASH').upper()
    if payment_method == "CASH":
        payment_account = cash_account
    elif payment_method == "BANK":
        bank_account_code = getattr(payment, 'bank_account_code', None)
        if not bank_account_code:
            raise ValueError("Bank account code required for BANK payment method")
        payment_account, _ = Account.objects.get_or_create(
            code=bank_account_code,
            defaults={"name": f"Bank Account {bank_account_code}", "type": "ASSET"}
        )
    else:
        payment_account = accounts_payable

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description=f"Payment via {payment_method}",
        debit=0,
        credit=net_due_amount
    )

    # Validate
    if not entry.is_balanced():
        debits = sum([line.debit for line in entry.lines.all()])
        credits = sum([line.credit for line in entry.lines.all()])
        raise ValueError(f"Journal entry {entry.id} is not balanced! Debits={debits}, Credits={credits}")

    return entry


def create_journal_entry_for_sale(sale_payment, description="", vat_amount=0, ait_amount=0, created_by=None):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    total_amount = Decimal(sale_payment.total_amount)
    vat_amount = Decimal(vat_amount or 0)
    ait_amount = Decimal(ait_amount or 0)
    net_receivable = total_amount + vat_amount - ait_amount

    # Create Journal Entry
    entry = JournalEntry.objects.create(
        date=timezone.now().date(),
        fiscal_year=fiscal_year,
        description=description or f"Sale entry for invoice {sale_payment.sale_invoice.id}",
        reference=f"SALE-{sale_payment.id}",
        created_by=created_by
    )

    # Get accounts (update codes based on your new chart of accounts)
    try:
        revenue_account = Account.objects.get(code="4110")   # Domestic Sales / Product Revenue
        cash_account = Account.objects.get(code="1110")      # Cash on Hand
        bank_account = Account.objects.get(code="1131")      # Bank Account
        accounts_receivable = Account.objects.get(code="1141")  # Accounts Receivable - Trade
        output_vat = Account.objects.get(code="2131")       # Output VAT Payable
        ait_payable = Account.objects.get(code="2132")      # AIT Payable
    except Account.DoesNotExist as e:
        raise ValueError(f"Required account not found: {e}")

    # Credit: Revenue
    JournalEntryLine.objects.create(
        entry=entry,
        account=revenue_account,
        description="Sales Revenue",
        debit=0,
        credit=total_amount
    )

    # Credit: VAT Payable
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=output_vat,
            description="Output VAT on Sale",
            debit=0,
            credit=vat_amount
        )

    # Debit: AIT Receivable (if any)
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable,
            description="AIT withheld",
            debit=ait_amount,
            credit=0
        )

    # Debit: Cash/Bank or Accounts Receivable
    if sale_payment.payment_method.upper() == "CASH":
        payment_account = cash_account
    elif sale_payment.payment_method.upper() == "BANK":
        payment_account = bank_account
    else:
        payment_account = accounts_receivable

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description="Cash/Bank received or Accounts Receivable",
        debit=net_receivable,
        credit=0
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry




#### below function apply to all payment models associated with invoice ################################
# Function name could be def create_journal_entry_for_integrated_invoice()

from django.db.models import Sum

def get_account(code):
    try:
        return Account.objects.get(code=code)
    except Account.DoesNotExist:
        raise ValueError(f"Missing Account Code: {code}. Please create it first.")
    

def create_journal_entry(payment, breakdown, description="", created_by=None, entry_type="HOSPITAL"):
    fiscal_year = FiscalYear.get_active() 

    invoice = payment.invoice
    if not invoice:
        raise ValueError("Payment has no linked invoice.")
        
    description = description or f"{entry_type} journal entry for Invoice {invoice.id}"

    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description,
        reference=f"HOSP-PAY-{payment.id}",
        created_by=created_by
    )

    cash_account = get_account("1110")
    bank_account = get_account("1131")
    ar_account = get_account("1210")

    vat_account = get_account("1610")
    ait_account = get_account("1620")

    revenue_accounts = {
        "Consultation": get_account("4100"),
        "Lab": get_account("4200"),
        "Medicine": get_account("4300"),
        "Ward": get_account("4400"),
        "OT": get_account("4500"),
        "Emergency": get_account("4100"),
    }

    if payment.payment_method == "Cash":
        debit_account = cash_account
    elif payment.payment_method in ["Card", "Bank"]:
        debit_account = bank_account
    else:
        debit_account = ar_account    

    for item in breakdown:
        received = Decimal(item.get("amount_received", 0))
        net_amount = Decimal(item.get("net_amount", 0))
        vat_amount = Decimal(item.get("vat_amount", 0))
        ait_amount = Decimal(item.get("ait_amount", 0))       
        revenue_type = item.get("revenue_type", "Consultation")

        service_type = revenue_type

        service_policy = None
        if service_type:
            from core.models import ServiceTaxPolicy
            service_policy = ServiceTaxPolicy.objects.filter(
                name=service_type, is_active=True
            ).first()
        if not service_policy:
            from core.models import TaxPolicy
            service_policy = TaxPolicy.objects.filter(is_active=True).first()

        ait_type = service_policy.ait_type
        
      
        JournalEntryLine.objects.create(
            entry=entry,
            account=debit_account,
            debit=received,
            credit=Decimal("0.00"),
            description=f"Payment Received ({revenue_type})"
        )
   
        rev_account = revenue_accounts.get(revenue_type, revenue_accounts["Consultation"])
        rev_line = JournalEntryLine.objects.create(
            entry=entry,
            account=rev_account,
            credit=net_amount,
            debit=Decimal("0.00"),
            description=f"Revenue: {revenue_type}"
        )    
  
        if vat_amount > 0:
            JournalEntryLine.objects.create(
                entry=entry,
                account=vat_account,
                credit=vat_amount,
                debit=Decimal("0.00"),
                description=f"VAT ({revenue_type})"
            )
 
        if ait_amount > 0:           
            JournalEntryLine.objects.create(
                entry=entry,
                account=ait_account,
                debit=Decimal("0.00"),
                credit=ait_amount,
                description=f"AIT Payable ({revenue_type})"
            )

    return entry


############## Journal entry only for referral as expenses as liability ##########################

from django.utils import timezone

def create_referral_commission_expense_journal(
        invoice, 
        commission_amount, 
        created_by=None):

    fiscal_year = FiscalYear.get_active()
    date = timezone.now().date()
    try:      
        expense_account = Account.objects.get(code="5240")  # Referral Commission Expense (or create a new one if needed)
        payable_account = Account.objects.get(code="2620")  #Referral commission payable

    except Account.DoesNotExist as e:
        raise ValueError(f"Required account not found: {e}") 
        

    entry = JournalEntry.objects.create(
        date=date,
        fiscal_year=fiscal_year,
        reference=f"REF-COMM-{invoice.id}",
        description=f"Referral commission expense for Invoice {invoice.id}",
        created_by=created_by,
    )
  
    JournalEntryLine.objects.create(
        entry=entry,
        account=expense_account,
        description="Referral Commission Expense",
        debit=commission_amount,
        credit=0
    )

    JournalEntryLine.objects.create(
        entry=entry,
        account=payable_account,
        description="Referral Commission Payable",
        debit=0,
        credit=commission_amount
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry


  


##### Journal entry when referral commission paid out ##########################

def create_referral_commission_payment_journal(
        referral_transaction, 
        payment_amount,        
        created_by=None):      
    fiscal_year = FiscalYear.get_active()
    date = timezone.now().date()

    bank_account_code = "1130"
    payable_account = Account.objects.get(code="2110")        
    cash_or_bank_account = Account.objects.get(code=bank_account_code)  

    entry = JournalEntry.objects.create(
        date=date,
        fiscal_year=fiscal_year,
        reference=f"REF-PAY-{referral_transaction.id}",
        description=f"Referral commission payout for {referral_transaction.referral_source}",
        created_by=created_by,
    )

    JournalEntryLine.objects.create(
        entry=entry,
        account=payable_account,
        description="Clear Referral Commission Payable",
        debit=Decimal(payment_amount),
        credit=0
    )

    JournalEntryLine.objects.create(
        entry=entry,
        account=cash_or_bank_account,
        description="Referral Commission Payment",
        debit=0,
        credit=Decimal(payment_amount)
    )
    from finance.models import AllExpenses   
    try:
        AllExpenses.objects.create(
            user=created_by,
            expense_head="Referral Commission",
            expense_type="REFERRAL_COMMISSION",
            amount=Decimal(payment_amount),
        )
    except Exception as e:
        print("Failed to create AllExpenses:", e)


    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry




def create_doctor_service_payment_journal(
        doctor_payment,
        payment_amount,
        created_by=None):

    fiscal_year = FiscalYear.get_active()
    date = timezone.now().date()

    payable_account = Account.objects.get(code="2110")  # Doctor Payable
    cash_account = Account.objects.get(code="1131")     # Cash/Bank

    entry = JournalEntry.objects.create(
        date=date,
        fiscal_year=fiscal_year,
        reference=f"DOC-PAY-{doctor_payment.id}",
        description=f"Doctor payout for Dr. {doctor_payment.doctor.name}",
        created_by=created_by,
    )

    # Debit Payable (reduce liability)
    JournalEntryLine.objects.create(
        entry=entry,
        account=payable_account,
        description="Doctor Payable Cleared",
        debit=payment_amount,
        credit=0
    )

    # Credit Cash/Bank
    JournalEntryLine.objects.create(
        entry=entry,
        account=cash_account,
        description="Doctor Payment",
        debit=0,
        credit=payment_amount
    )

    from finance.models import AllExpenses
    AllExpenses.objects.create(
        expense_head="Doctor Service Payment",
        expense_type="DOCTOR_PAYMENT",
        amount=payment_amount,
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry

