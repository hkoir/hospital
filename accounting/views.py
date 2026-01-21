from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import FiscalYear, Account, JournalEntry
from .forms import FiscalYearForm, AccountForm, JournalEntryForm, JournalEntryLineFormSet
from django.db.models import Sum
from .models import Account, JournalEntryLine, FiscalYear
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required




def fiscalyear_list(request):
    years = FiscalYear.objects.all().order_by('-year_start')
    return render(request, 'accounting/fiscalyear_list.html', {'years': years})

def fiscalyear_create(request):
    if request.method == 'POST':
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounting:fiscalyear_list')
    else:
        form = FiscalYearForm()
    return render(request, 'accounting/fiscalyear_form.html', {'form': form})


# Account Views
def account_list(request):
    accounts = Account.objects.all().order_by('code')
    return render(request, 'accounting/account_list.html', {'accounts': accounts})

def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounting:account_list')
    else:
        form = AccountForm()
    return render(request, 'accounting/account_form.html', {'form': form})



def journalentry_list(request):
    entries = JournalEntry.objects.all().order_by('-date')
    return render(request, 'accounting/journalentry_list.html', {'entries': entries})




@transaction.atomic
def journalentry_create(request):
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            formset = JournalEntryLineFormSet(request.POST, instance=entry)

            if formset.is_valid():
                entry.save()
                formset.save()
                if not entry.is_balanced():
                    transaction.set_rollback(True)
                    form.add_error(None, "Debits and Credits must balance.")
                else:
                    return redirect('accounting:journalentry_list')
        else:
            formset = JournalEntryLineFormSet(request.POST)
    else:
        form = JournalEntryForm()
        formset = JournalEntryLineFormSet()

    return render(request, 'accounting/journalentry_form.html', {
        'form': form,
        'formset': formset,
    })


def journalentry_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk)
    return render(request, 'accounting/journalentry_detail.html', {'entry': entry})





def get_all_children(account):
    children = []
    for child in Account.objects.filter(parent=account):
        children.append(child)
        children += get_all_children(child)
    return children


def get_account_balance_by_fy(account, fiscal_year):  
    lines = JournalEntryLine.objects.filter(
        account=account,
        entry__date__gte=fiscal_year.year_start,
        entry__date__lte=fiscal_year.year_end
    )
    debit_total = lines.aggregate(total=Sum('debit'))['total'] or 0
    credit_total = lines.aggregate(total=Sum('credit'))['total'] or 0

    if account.type in ['ASSET', 'EXPENSE']:
        return debit_total - credit_total
    else:  # INCOME, LIABILITY, EQUITY
        return credit_total - debit_total

def get_direct_balance(account, fiscal_year):
    """Get balance of an account only (without children)."""
    lines = JournalEntryLine.objects.filter(
        account=account,
        entry__date__gte=fiscal_year.year_start,
        entry__date__lte=fiscal_year.year_end
    )
    debit_total = lines.aggregate(total=Sum('debit'))['total'] or 0
    credit_total = lines.aggregate(total=Sum('credit'))['total'] or 0

    if account.type in ['ASSET', 'EXPENSE']:
        return debit_total - credit_total
    else:
        return credit_total - debit_total


def build_account_tree(account, fiscal_years, level=0, parent_number=""):
    node = {
        "account": account,
        "balances": {},       # Direct balance
        "total_balances": {}, # Includes children
        "children": [],
        "level": level,
        "number": parent_number
    }

    # Direct balances
    for fy in fiscal_years:
        node['balances'][fy.id] = get_direct_balance(account, fy)

    # Recursively build children
    children = Account.objects.filter(parent=account).order_by("id")
    for idx, child in enumerate(children, start=1):
        child_number = f"{parent_number}.{idx}" if parent_number else str(idx)
        child_node = build_account_tree(child, fiscal_years, level + 1, child_number)
        node['children'].append(child_node)

    for fy in fiscal_years:
        total = node['balances'][fy.id] + sum(child['total_balances'][fy.id] for child in node['children'])
        node['total_balances'][fy.id] = total

    return node



def balance_sheet_view(request):
    fiscal_years = FiscalYear.objects.order_by('year_start')
    group_order = ['ASSET', 'LIABILITY', 'EQUITY']
    parent_order = {
        'ASSET': ['Current Assets', 'Non-Current Assets'],
        'LIABILITY': ['Current Liabilities', 'Non-Current Liabilities'],
        'EQUITY': ['Shareholder Capital', 'Retained Earnings']
    }

    report_tree = []
    total_assets = {fy.id: 0 for fy in fiscal_years}
    total_liabilities = {fy.id: 0 for fy in fiscal_years}
    total_equity = {fy.id: 0 for fy in fiscal_years}
    net_profit = {fy.id: 0 for fy in fiscal_years}

    # Compute net profit per fiscal year from P&L
    income_accounts = Account.objects.filter(parent__isnull=True, type='INCOME')
    expense_accounts = Account.objects.filter(parent__isnull=True, type='EXPENSE')

    for fy in fiscal_years:
        total_income = sum(build_account_tree(acct, [fy])['total_balances'][fy.id] for acct in income_accounts)
        total_expense = sum(build_account_tree(acct, [fy])['total_balances'][fy.id] for acct in expense_accounts)
        net_profit[fy.id] = total_income - total_expense

    # Build report tree and totals
    for gtype in group_order:
        parents = Account.objects.filter(parent__isnull=True, type=gtype)
        ordered_parents = []

        for name in parent_order.get(gtype, []):
            p = parents.filter(name=name).first()
            if p:
                ordered_parents.append(p)
        for p in parents.exclude(name__in=parent_order.get(gtype, [])):
            ordered_parents.append(p)

        for parent in ordered_parents:
            node = build_account_tree(parent, fiscal_years)

            for fy in fiscal_years:
                if gtype == 'ASSET':
                    total_assets[fy.id] += node['total_balances'][fy.id]
                elif gtype == 'LIABILITY':
                    total_liabilities[fy.id] += node['total_balances'][fy.id]
                else:  # EQUITY
                    total_equity[fy.id] += node['total_balances'][fy.id]

            report_tree.append(node)

    # Total Liabilities & Equity includes net profit
    total_liabilities_equity = {
        fy.id: total_liabilities[fy.id] + total_equity[fy.id] + net_profit[fy.id]
        for fy in fiscal_years
    }

    return render(request, 'accounting/balance_sheet.html', {
        'report_tree': report_tree,
        'fiscal_years': fiscal_years,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'net_profit': net_profit,
        'total_liabilities_equity': total_liabilities_equity,
    })




def ledger_view(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    # Include all child accounts
    all_accounts = [account] + get_all_children(account)

    lines = (
        JournalEntryLine.objects
        .filter(account__in=all_accounts)
        .select_related("entry")
        .order_by("entry__date", "id")
    )

    balance = 0
    ledger_rows = []
    for line in lines:
        if account.type in ["ASSET", "EXPENSE"]:
            balance += (line.debit or 0) - (line.credit or 0)
        else:  # Liability, Equity, Income
            balance += (line.credit or 0) - (line.debit or 0)

        ledger_rows.append({
            "date": line.entry.date,
            "description": line.description or line.entry.description,
            "account": line.account.name,  # show which child account
            "debit": line.debit,
            "credit": line.credit,
            "balance": balance,
        })

    return render(request, "accounting/ledger.html", {
        "account": account,
        "ledger_rows": ledger_rows,
    })





def ledger_search_and_view(request):
    query = request.GET.get("query", "").strip()
    account = None
    ledger_rows = []

    if query:
        if query.isdigit():
            account = Account.objects.filter(code=query).first() 
        if not account:
            account = Account.objects.filter(name__icontains=query).first()

        if account:          
            all_accounts = [account] + get_all_children(account)

            lines = (
                JournalEntryLine.objects
                .filter(account__in=all_accounts)
                .select_related("entry")
                .order_by("entry__date", "id")
            )

            balance = 0
            for line in lines:          
                if account.type in ["ASSET", "EXPENSE"]:
                    balance += (line.debit or 0) - (line.credit or 0)
                else: 
                    balance += (line.credit or 0) - (line.debit or 0)

                ledger_rows.append({
                    "date": line.entry.date,
                    "description": line.description or line.entry.description,
                    "account": line.account.name,
                    "debit": line.debit,
                    "credit": line.credit,
                    "balance": balance,
                })

    return render(request, "accounting/ledger_search.html", {
        "query": query,
        "account": account,
        "ledger_rows": ledger_rows,
    })



def trial_balance_view(request):
    report_date = request.GET.get("date")
    if report_date:
        from datetime import datetime
        report_date = datetime.strptime(report_date, "%Y-%m-%d").date()
    else:
        from django.utils.timezone import now
        report_date = now().date()

    accounts = Account.objects.filter(parent__isnull=True).order_by('code')
    report_rows = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        all_accounts = [account] + get_all_children(account)
        lines = JournalEntryLine.objects.filter(account__in=all_accounts, entry__date__lte=report_date)
        debit_total = lines.aggregate(total=Sum('debit'))['total'] or 0
        credit_total = lines.aggregate(total=Sum('credit'))['total'] or 0

        if account.type in ['ASSET', 'EXPENSE']:
            balance_dr = debit_total - credit_total if debit_total > credit_total else 0
            balance_cr = credit_total - debit_total if credit_total > debit_total else 0
        else:  # LIABILITY, EQUITY, INCOME
            balance_cr = credit_total - debit_total if credit_total > debit_total else 0
            balance_dr = debit_total - credit_total if debit_total > credit_total else 0

        if balance_dr == 0 and balance_cr == 0:
            continue

        total_debits += balance_dr
        total_credits += balance_cr

        report_rows.append({
            'account': account,
            'balance': {'debit': balance_dr, 'credit': balance_cr}
        })

    return render(request, 'accounting/trial_balance.html', {
        "report_date": report_date,
        "report_rows": report_rows,
        "total_debits": total_debits,
        "total_credits": total_credits
    })




def profit_loss_view(request):
    fiscal_years = FiscalYear.objects.order_by('year_start')
    accounts = Account.objects.filter(parent__isnull=True, type__in=['INCOME', 'EXPENSE'])

    report = {
        'fiscal_years': fiscal_years,
        'income': [],
        'expenses': [],
        'total_income': {},
        'total_expenses': {},
        'net_profit_before_tax': {},
        'taxes': {},
        'net_profit_after_tax': {}
    }

    for acct in accounts:
        tree = build_account_tree(acct, fiscal_years)
        if acct.type == 'INCOME':
            report['income'].append(tree)
        else:
            report['expenses'].append(tree)

    # 🔧 Here’s the fixed block
    for fy in fiscal_years:
        # normalize income and expense balances
        total_income = sum(
            (a['total_balances'][fy.id])  # flip to positive
            for a in report['income']
        )
        total_expenses = sum(
            abs(a['total_balances'][fy.id])    # always positive
            for a in report['expenses']
        )

        tax_expense = 0
        tax_account = Account.objects.filter(name__icontains='Income Tax Expense').first()
        if tax_account:
            tax_expense = get_direct_balance(tax_account, fy)

        report['total_income'][fy.id] = total_income
        report['total_expenses'][fy.id] = total_expenses
        report['net_profit_before_tax'][fy.id] = total_income - total_expenses
        report['taxes'][fy.id] = tax_expense
        report['net_profit_after_tax'][fy.id] = total_income - total_expenses - tax_expense

    return render(request, 'accounting/profit_loss.html', {'report': report})




def get_all_descendants(account):
    children = []
    for child in account.account_set.all():
        children.append(child)
        children += get_all_descendants(child)
    return children


def get_quarters(fy):
    quarters = []
    start = fy.year_start
    for i in range(4):
        q_start = start + relativedelta(months=3*i)
        q_end = q_start + relativedelta(months=3, days=-1)
        quarters.append((f"Q{i+1}", q_start, q_end))
    quarters.append(("Total", fy.year_start, fy.year_end))
    return quarters


def calculate_balance_bs(account, start_date, end_date, balance_type="bs", include_descendants=True):
    accounts = [account]
    if include_descendants:
        accounts += get_all_descendants(account)

    lines = JournalEntryLine.objects.filter(
        account__in=accounts,
        entry__date__gte=start_date,
        entry__date__lte=end_date
    )
    debit = lines.aggregate(total=Sum("debit"))["total"] or Decimal("0.00")
    credit = lines.aggregate(total=Sum("credit"))["total"] or Decimal("0.00")

    # Balance Sheet logic
    if account.type in ("ASSET", "EXPENSE"):
        return debit - credit
    else:  # LIABILITIES, EQUITY
        return credit - debit


def build_report_tree_bs(accounts, fiscal_years, balance_type="bs", level=0, parent_id=None):
    tree = []
    for acc in accounts:
        node = {
            "account": acc,
            "balances": {},
            "children": [],
            "level": level,
            "parent_id": parent_id,
        }

        for fy in fiscal_years:
            for label, start, end in get_quarters(fy):
                key = f"{fy.id}_{label}"
                node["balances"][key] = calculate_balance_bs(acc, start, end, balance_type, include_descendants=False)

        children = acc.account_set.all()
        if children.exists():
            node["children"] = build_report_tree_bs(children, fiscal_years, balance_type, level=level+1, parent_id=acc.id)
            # Add child balances into parent
            for key in node["balances"]:
                node["balances"][key] += sum(c["balances"][key] for c in node["children"])

        tree.append(node)
    return tree




def balance_sheet_quarterly(request):
    fiscal_years = FiscalYear.objects.order_by("year_start")
    quarters = ["Q1", "Q2", "Q3", "Q4", "Total"]
    total_cols = fiscal_years.count() * len(quarters) + 2

    root_accounts = Account.objects.filter(parent__isnull=True)
    report_tree = build_report_tree_bs(root_accounts, fiscal_years)

    # Totals
    totals = {}
    for fy in fiscal_years:
        totals[fy.id] = {}
        for q in quarters:
            key = f"{fy.id}_{q}"

            # Assets
            assets_total = sum(
                n["balances"].get(key, 0) 
                for n in report_tree 
                if n["account"].type == "ASSET"
            )

            # Liabilities
            liabilities_total = sum(
                n["balances"].get(key, 0) 
                for n in report_tree 
                if n["account"].type == "LIABILITY"
            )

            # Equity (including net profit from Income – Expenses)
            equity_total = sum(
                n["balances"].get(key, 0) 
                for n in report_tree 
                if n["account"].type == "EQUITY"
            )

            # Add net profit from Income – Expenses
            income_total = sum(
                n["balances"].get(key, 0)
                for n in report_tree
                if n["account"].type == "INCOME"
            )
            expense_total = sum(
                n["balances"].get(key, 0)
                for n in report_tree
                if n["account"].type in ("EXPENSE", "COST")
            )
            net_profit = income_total - expense_total
            equity_total += net_profit

            totals[fy.id][q] = {
                "assets": assets_total,
                "liabilities": liabilities_total,
                "equity": equity_total - net_profit,  # pure equity accounts
                "net_profit": net_profit,
                "liabilities_equity": liabilities_total + equity_total
            }

    context = {
        "fiscal_years": fiscal_years,
        "quarters": quarters,
        "total_cols": total_cols,
        "report_tree": report_tree,
        "totals": totals,
        "net_profit": net_profit,
    }
    return render(request, "accounting/balance_sheet_quarterly.html", context)




def get_quarters_pl(fy):
    quarters = []
    start = fy.year_start
    for i in range(4):
        q_start = start + relativedelta(months=3 * i)
        q_end = q_start + relativedelta(months=3, days=-1)
        quarters.append((f"Q{i+1}", q_start, q_end))
    quarters.append(("Total", fy.year_start, fy.year_end))
    return quarters

def calculate_balance_pl(account, start, end, balance_type="pl", include_descendants=True):
    accounts = [account]
    if include_descendants:
        accounts += list(account.account_set.all())
    totals = JournalEntryLine.objects.filter(
        account__in=accounts,
        entry__date__gte=start,
        entry__date__lte=end,
    ).aggregate(debit_sum=Sum("debit"), credit_sum=Sum("credit"))

    debit = totals["debit_sum"] or Decimal("0.00")
    credit = totals["credit_sum"] or Decimal("0.00")

    if balance_type == "pl":
        if account.type in ("EXPENSE", "COST"):
            return debit - credit
        return credit - debit
    return credit - debit


def build_report_tree_pl(accounts, fiscal_years, balance_type="pl", level=0, parent_id=None):
    tree = []
    for acc in accounts:
        node = {
            "account": acc,
            "balances": {},
            "children": [],
            "level": level,
            "parent_id": parent_id,
        }

        for fy in fiscal_years:
            for label, start, end in get_quarters_pl(fy):
                key = f"{fy.id}_{label}"
                node["balances"][key] = calculate_balance_pl(acc, start, end, balance_type, include_descendants=False)

        children = acc.account_set.all()
        if children.exists():
            node["children"] = build_report_tree_pl(children, fiscal_years, balance_type, level=level+1, parent_id=acc.id)
            for key in node["balances"]:
                node["balances"][key] += sum(c["balances"][key] for c in node["children"])

        tree.append(node)
    return tree




def profit_loss_quarterly(request):
    fiscal_years = FiscalYear.objects.all().order_by("year_start")
    quarters = ["Q1", "Q2", "Q3", "Q4", "Total"]
    total_cols = fiscal_years.count() * len(quarters) + 2

    income_accounts = Account.objects.filter(parent__isnull=True, type__in=["INCOME"])
    report_income = build_report_tree_pl(income_accounts, fiscal_years, balance_type="pl")

    expense_accounts = Account.objects.filter(parent__isnull=True, type__in=["EXPENSE", "COST"])
    report_expenses = build_report_tree_pl(expense_accounts, fiscal_years, balance_type="pl")

    TAX_RATE = Decimal("0.25")  # 25%
    totals = {}
    for fy in fiscal_years:
        totals[fy.id] = {}
        for q in quarters:
            key = f"{fy.id}_{q}"
            income_total = sum(n["balances"].get(key, 0) for n in report_income)
            expense_total = sum(n["balances"].get(key, 0) for n in report_expenses)
            net_profit_before_tax = income_total - expense_total
            tax_amount = net_profit_before_tax * TAX_RATE if net_profit_before_tax > 0 else Decimal("0.00")
            net_profit_after_tax = net_profit_before_tax - tax_amount

            totals[fy.id][q] = {
                "income": income_total,
                "expenses": expense_total,
                "net_profit_before_tax": net_profit_before_tax,
                "tax": tax_amount,
                "net_profit_after_tax": net_profit_after_tax,
            }

    context = {
        "fiscal_years": fiscal_years,
        "quarters": quarters,
        "total_cols": total_cols,
        "report_income": report_income,
        "report_expenses": report_expenses,
        "totals": totals,
        "tax_rate": TAX_RATE,
    }
    return render(request, "accounting/profit_loss_quarterly.html", context)
