from django.core.exceptions import ValidationError
from inventory.models import Inventory, InventoryTransaction
from django.db import transaction as db_transaction
from inventory.models import Inventory, InventoryTransaction
from accounting.models import JournalEntry, JournalEntryLine, FiscalYear, Account


def process_transaction(transaction, user, target_warehouse=None, target_location=None): 
    product = transaction.product
    warehouse = transaction.warehouse
    location = transaction.location
    batch = transaction.batch
    quantity = transaction.quantity
    transaction_type = transaction.transaction_type


    if not batch:
        raise ValidationError("Batch is required to calculate transaction amount.")

    # Determine amount based on batch
    if transaction_type in ['INBOUND', 'EXISTING_ITEM_IN', 'SCRAPPED_IN']:
        amount = (batch.purchase_price or 0) * quantity
    else:  # OUTBOUND/TRANSFER
        amount = (batch.sale_price or 0) * quantity

    # Get active fiscal year
    fy = FiscalYear.get_active()
    if not fy:
        raise ValidationError("No active Fiscal Year defined.")



    inventory_account = Account.objects.get(code="1310")  # Inventory (asset)
    cogs_account = Account.objects.get(code="5100")       # Cost of Goods Sold
    cash_account = Account.objects.get(code="1110")       # Cash / Bank


    with db_transaction.atomic():
        # --- Lookup or create inventory ---
        inventory = Inventory.objects.filter(
            product=product,
            warehouse=warehouse,
            location=location,
            batch=batch
        ).first()

        # --------------------------
        # Handle INBOUND-like transactions
        # --------------------------
        if transaction_type in ['INBOUND', 'EXISTING_ITEM_IN', 'SCRAPPED_IN']:
            if inventory:
                inventory.quantity += quantity
                inventory.save()
            else:
                inventory = Inventory.objects.create(
                    product=product,
                    warehouse=warehouse,
                    location=location,
                    batch=batch,
                    quantity=quantity,
                    user=user
                )

            # Journal Entry
            journal = JournalEntry.objects.create(
                date=transaction.created_at,
                fiscal_year=fy,
                reference=f"TX-{transaction.id}",
                description=f"INBOUND Inventory: {product}",
                created_by=user
            )
            # Debit Inventory, Credit COGS
            JournalEntryLine.objects.create(entry=journal, account=inventory_account, debit=amount, credit=0)
            JournalEntryLine.objects.create(entry=journal, account=cogs_account, debit=0, credit=amount)

        # --------------------------
        # Handle OUTBOUND-like transactions
        # --------------------------
        elif transaction_type in ['OUTBOUND', 'SCRAPPED_OUT', 'RETURN']:
            if not inventory or inventory.quantity < quantity:
                raise ValidationError("Not enough inventory to perform this transaction.")
            inventory.quantity -= quantity
            inventory.save()

            # Adjust batch remaining
            if batch:
                if (batch.remaining_quantity or 0) < quantity:
                    raise ValidationError("Not enough batch quantity.")
                batch.remaining_quantity -= quantity
                batch.save()

            # Journal Entry
            journal = JournalEntry.objects.create(
                date=transaction.created_at,
                fiscal_year=fy,
                reference=f"TX-{transaction.id}",
                description=f"OUTBOUND Inventory: {product}",
                created_by=user
            )
            # Debit COGS, Credit Inventory
            JournalEntryLine.objects.create(entry=journal, account=cogs_account, debit=amount, credit=0)
            JournalEntryLine.objects.create(entry=journal, account=inventory_account, debit=0, credit=amount)

        # --------------------------
        # Handle TRANSFER transactions
        # --------------------------
        elif transaction_type == 'TRANSFER_OUT':
            if not inventory or inventory.quantity < quantity:
                raise ValidationError("Not enough inventory to perform transfer.")
            inventory.quantity -= quantity
            inventory.save()

            if batch:
                if (batch.remaining_quantity or 0) < quantity:
                    raise ValidationError("Not enough batch quantity.")
                batch.remaining_quantity -= quantity
                batch.save()

            # Target inventory
            if not target_warehouse or not target_location:
                raise ValidationError("Target warehouse and location required for transfer.")

            target_inventory, _ = Inventory.objects.get_or_create(
                product=product,
                warehouse=target_warehouse,
                location=target_location,
                batch=batch,
                defaults={'quantity': 0, 'user': user}
            )
            target_inventory.quantity += quantity
            target_inventory.save()
          
            # Auto-create TRANSFER_IN transaction
            InventoryTransaction.objects.create(
                inventory_transaction=target_inventory,
                user=user,
                transaction_type='TRANSFER_IN',
                product=product,
                batch=batch,
                warehouse=target_warehouse,
                location=target_location,
                quantity=quantity,
                remarks=f"Auto-created TRANSFER_IN from {warehouse.name}/{location.name}"
            )

        transaction.inventory_transaction = inventory
        transaction.save()

    return transaction
