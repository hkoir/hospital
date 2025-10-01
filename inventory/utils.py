

MEDICINE_CATEGORY_CHOICES = [
    ('Analgesics', 'Analgesics (Pain Relievers)'),
    ('Antipyretics', 'Antipyretics (Fever Reducers)'),
    ('Antibiotics', 'Antibiotics'),
    ('Antiseptics', 'Antiseptics'),
    ('Antidepressants', 'Antidepressants'),
    ('Antidiabetics', 'Antidiabetics'),
    ('Antihistamines', 'Antihistamines (Allergy Medications)'),
    ('Antihypertensives', 'Antihypertensives (Blood Pressure Medications)'),
    ('Anticoagulants', 'Anticoagulants (Blood Thinners)'),
    ('Antifungals', 'Antifungals'),
    ('Antivirals', 'Antivirals'),
    ('Bronchodilators', 'Bronchodilators (Asthma/COPD Medications)'),
    ('Corticosteroids', 'Corticosteroids'),
    ('Diuretics', 'Diuretics'),
    ('Gastrointestinal', 'Gastrointestinal Medications'),
    ('Hormonal', 'Hormonal Medications'),
    ('Immunosuppressants', 'Immunosuppressants'),
    ('Muscle Relaxants', 'Muscle Relaxants'),
    ('Neurological', 'Neurological Medications'),
    ('Ophthalmic', 'Ophthalmic Medications (Eye Drops)'),
    ('Psychotropic', 'Psychotropic Medications'),
    ('Sedatives', 'Sedatives & Hypnotics'),
    ('Vaccines', 'Vaccines'),
    ('Vitamins', 'Vitamins & Supplements'),
    ('Others', 'Others'),
]






from django.db import models
from django.db.models import F,Q,Sum,Case, When
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)
from django import forms

from product.models import Product,Category
from core.models import Employee
from finance.models import PurchaseInvoice
from logistics.models import PurchaseShipment
from purchase.models import PurchaseOrder, PurchaseRequestOrder
# from inventory.models import InventoryTransaction,Warehouse,TransferOrder

from messaging.models import Notification




def create_notification(user,notification_type, message):   
    Notification.objects.create(user=user, message=message,notification_type=notification_type)
    

def mark_notification_as_read(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
    except Notification.DoesNotExist:
        pass  




# for purchase update ######################################################################
def update_purchase_order(purchase_order_id):
    try:
        with transaction.atomic():
            purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)         
            print(f"Updating Purchase Order ID: {purchase_order_id}")
            
            shipments = purchase_order.purchase_shipment.all()
            
            if shipments.exists(): 
                all_shipments_delivered = (
                    shipments.filter(status__in=['DELIVERED','REACHED','OBI']).count()
                    == shipments.count()
                )
                if all_shipments_delivered:
                    print("All shipments delivered. Updating status to DELIVERED.")
                    purchase_order.status = 'DELIVERED'
                    purchase_order.save()
                else:
                    print("Not all shipments delivered. Status remains unchanged.")
            else:
                print("No shipments found for this purchase order. Status remains unchanged.")
    except Exception as e:
        print(f"Error updating purchase order {purchase_order_id}: {e}")



def update_purchase_request_order(request_order_id):
    try:
        with transaction.atomic():
            request_order = PurchaseRequestOrder.objects.get(id=request_order_id)
            total_requested_product = request_order.purchase_request_order.aggregate(total_requested_product=Sum('quantity'))['total_requested_product'] or 0

            total_dispatch_quantity = 0

            for purchase_order in request_order.purchase_order_request_order.all():
                for shipment in purchase_order.purchase_shipment.all():
                    dispatch_sum = shipment.shipment_dispatch_item.aggregate(total_dispatch=Sum('dispatch_quantity'))['total_dispatch'] or 0
                    total_dispatch_quantity += dispatch_sum

            if total_dispatch_quantity == total_requested_product:
                request_order.status = 'DELIVERED'
            elif 0 < total_dispatch_quantity < total_requested_product:
                request_order.status = 'PARTIAL_DELIVERED'
            elif total_dispatch_quantity == 0:
                request_order.status = 'IN_PROCESS'

            request_order.save()

    except Exception as e:
        print(f"Error updating sale request order: {e}")
       
    


def update_shipment_status(shipment_id):
    try:
        shipment = PurchaseShipment.objects.get(id=shipment_id)
        all_items_delivered = shipment.shipment_dispatch_item.filter(status='DELIVERED').count() == shipment.shipment_dispatch_item.count()
        if all_items_delivered:
            shipment.status = 'DELIVERED'
            shipment.save()
            logger.info(f"Shipment {shipment_id} marked as DELIVERED.")
    except PurchaseShipment.DoesNotExist:
        logger.error(f"Shipment {shipment_id} not found.")




############################################################################


def assign_roles(order, requester, reviewer, approver):
    order.requester = requester
    order.reviewer = reviewer
    order.approver = approver
    order.save()  




def get_warehouse_stock(warehouse, product):
    transactions = InventoryTransaction.objects.filter(
        warehouse=warehouse, product=product
    ).values('transaction_type').annotate(total=Sum('quantity'))

    inbound = sum(t['total'] for t in transactions if t['transaction_type'] in ['INBOUND', 'TRANSFER_IN','MANUFACTURE_IN','REPLACEMENT_IN','EXISTING_ITEM_IN'])
    outbound = sum(t['total'] for t in transactions if t['transaction_type'] in ['OUTBOUND', 'TRANSFER_OUT','REPLACEMENT_OUT','OPERATIONS_OUT','MANUFACTURE_OUT'])

    return inbound - outbound



def calculate_stock_value(product, warehouse): 
    total_purchase = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse, 
        transaction_type='INBOUND',
        purchase_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='MANUFACTURE_IN',
        manufacture_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='MANUFACTURE_OUT',
        manufacture_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_sold = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='OUTBOUND',
        sales_order__isnull=False
    ).exclude(
        Q(remarks__icontains='transfer') |
        Q(remarks__icontains='replacement')
    ).aggregate(total=Sum('quantity'))['total'] or 0


    total_replacement_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='REPLACEMENT_OUT',  
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_replacement_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='REPLACEMENT_IN',  
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_transfer_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='TRANSFER_IN',  
    ).aggregate(total=Sum('quantity'))['total'] or 0


    total_transfer_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='TRANSFER_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_Existing_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='EXISTING_ITEM_IN', 
    ).aggregate(total=Sum('quantity'))['total'] or 0
    total_operations_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='OPERATIONS_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_scrapped_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='SCRAPPED_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_scrapped_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='SCRAPPED_IN', 
    ).aggregate(total=Sum('quantity'))['total'] or 0




    total_available = (
        total_purchase + total_manufacture_in + total_transfer_in + total_Existing_in + total_scrapped_in
        - (total_sold + total_transfer_out + total_replacement_out + total_operations_out + total_manufacture_out + total_scrapped_out)
    )   
    total_stock = total_purchase + total_manufacture_in + total_transfer_in + total_Existing_in
    
    if total_available < 0:
        logger.warning(f"Negative stock detected for {product.name} in {warehouse.name}.")
        total_available = 0 

    return {
        'total_purchase': total_purchase,
        'total_manufacture_in': total_manufacture_in,
        'total_manufacture_out': total_manufacture_out,
        'total_existing_in': total_Existing_in,
        'total_operations_out': total_operations_out,
        'total_sold': total_sold,
        'total_replacement_in': total_replacement_in,
        'total_replacement_out': total_replacement_out,
        'total_transfer_in': total_transfer_in,
        'total_transfer_out': total_transfer_out,
        'total_scrapped_in': total_scrapped_in,
        'total_scrapped_out': total_scrapped_out,
        'total_available': total_available,
        'total_stock':total_stock
    }




def calculate_stock_value2(product, warehouse=None): 
    filters = {'product': product}
    if warehouse:
        if isinstance(warehouse, Warehouse):  
            filters['warehouse'] = warehouse
        else:
            logger.error("Invalid warehouse instance provided.")
            raise ValueError("Invalid warehouse instance provided.")


    total_purchase = InventoryTransaction.objects.filter(
        transaction_type='INBOUND',
        purchase_order__isnull=False,
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_in = InventoryTransaction.objects.filter(
        transaction_type='MANUFACTURE_IN',
        manufacture_order__isnull=False,
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_out = InventoryTransaction.objects.filter(
        transaction_type='MANUFACTURE_OUT',
        manufacture_order__isnull=False,
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_sold = InventoryTransaction.objects.filter(
        transaction_type='OUTBOUND',
        sales_order__isnull=False,
        **filters
    ).exclude(
        Q(remarks__icontains='transfer') |
        Q(remarks__icontains='replacement')
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_replacement_out = InventoryTransaction.objects.filter(
        transaction_type='REPLACEMENT_OUT',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_replacement_in = InventoryTransaction.objects.filter(
        transaction_type='REPLACEMENT_IN',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_transfer_in = InventoryTransaction.objects.filter(
        transaction_type='TRANSFER_IN',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_transfer_out = InventoryTransaction.objects.filter(
        transaction_type='TRANSFER_OUT',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_existing_in = InventoryTransaction.objects.filter(
        transaction_type='EXISTING_ITEM_IN',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_operations_out = InventoryTransaction.objects.filter(
        transaction_type='OPERATIONS_OUT',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    
    total_scrapped_out = InventoryTransaction.objects.filter(
        transaction_type='SCRAPPED_OUT',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_scrapped_in = InventoryTransaction.objects.filter(
        transaction_type='SCRAPPED_IN',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_pos_sales = InventoryTransaction.objects.filter(
        transaction_type='POS_SALES',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_online_sales = InventoryTransaction.objects.filter(
        transaction_type='ONLINE_SALES',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_local_purchase = InventoryTransaction.objects.filter(
        transaction_type='LOCAL_PURCHASE',
        **filters
    ).aggregate(total=Sum('quantity'))['total'] or 0


    total_available = (
        total_purchase + total_local_purchase + total_manufacture_in + total_transfer_in + total_existing_in + total_scrapped_in
        - (total_sold + total_transfer_out + total_replacement_out + total_operations_out + total_manufacture_out + total_scrapped_out +total_pos_sales + total_online_sales)
    )

    total_stock = total_purchase + total_local_purchase + total_manufacture_in + total_transfer_in + total_existing_in
    
    if total_available < 0:
        logger.warning(
            f"Negative stock detected for {product.name} in "
            f"{warehouse.name if warehouse else 'all warehouses'}"
        )
        total_available = 0

    return {
        'total_purchase': total_purchase,
        'total_manufacture_in': total_manufacture_in,
        'total_manufacture_out': total_manufacture_out,
        'total_existing_in': total_existing_in,
        'total_operations_out': total_operations_out,
        'total_sold': total_sold,
        'total_replacement_out': total_replacement_out,
        'total_replacement_in': total_replacement_in,
        'total_transfer_in': total_transfer_in,
        'total_transfer_out': total_transfer_out,
        'total_scrapped_in': total_scrapped_in,
        'total_scrapped_out': total_scrapped_out,
        'total_available': total_available,
        'total_stock': total_stock,

        'total_pos_sales': total_pos_sales,
        'total_online_sales': total_online_sales,
        'total_local_purchase': total_local_purchase,
    }

def calculate_batch_stock_value(product, warehouse, valuation_method="FIFO"):
    total_purchase = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse, 
        transaction_type='INBOUND',
        purchase_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_local_purchase = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse, 
        transaction_type='LOCAL_PURCHASE',
        local_purchase_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='MANUFACTURE_IN',
        manufacture_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_manufacture_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='MANUFACTURE_OUT',
        manufacture_order__isnull=False
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_sold = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='OUTBOUND',
        sales_order__isnull=False
    ).exclude(
        Q(remarks__icontains='transfer') |
        Q(remarks__icontains='replacement')
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_pos_sales = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='POS_SALES',
        pos_sale_order__isnull=False
    ).exclude(
        Q(remarks__icontains='transfer') |
        Q(remarks__icontains='replacement')
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_online_sales = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='ONLINE_SALES',
        online_sale_order__isnull=False
    ).exclude(
        Q(remarks__icontains='transfer') |
        Q(remarks__icontains='replacement')
    ).aggregate(total=Sum('quantity'))['total'] or 0


    total_replacement_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='REPLACEMENT_OUT',  
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_replacement_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,  
        transaction_type='REPLACEMENT_IN',  
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_transfer_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='TRANSFER_IN',  
    ).aggregate(total=Sum('quantity'))['total'] or 0


    total_transfer_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='TRANSFER_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_Existing_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='EXISTING_ITEM_IN', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_operations_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='OPERATIONS_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_scrapped_out = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='SCRAPPED_OUT', 
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_scrapped_in = InventoryTransaction.objects.filter(
        product=product,
        warehouse=warehouse,
        transaction_type='SCRAPPED_IN', 
    ).aggregate(total=Sum('quantity'))['total'] or 0




    total_available = (
        total_purchase + total_manufacture_in + total_transfer_in + total_Existing_in + total_scrapped_in + total_local_purchase
        - (total_sold + total_transfer_out + total_replacement_out + total_operations_out + total_manufacture_out + total_scrapped_out + total_pos_sales + total_online_sales)
    )   
    total_stock =  total_purchase +  total_local_purchase + total_manufacture_in + total_transfer_in + total_Existing_in + total_scrapped_in

    order_by = "created_at" if valuation_method == "FIFO" else "-created_at"

    latest_transaction = (
        InventoryTransaction.objects.filter(
            product=product,
            warehouse=warehouse,
            transaction_type__in=['INBOUND', 'LOCAL_PURCHASE']
        )
        .select_related("batch")
        .order_by(order_by)
        .first()
    )

    if latest_transaction and latest_transaction.batch and latest_transaction.batch.unit_price is not None:
        unit_cost = latest_transaction.batch.purchase_price
    else:
        # fallback to product base price if no transaction found
        unit_cost = 0.0

    stock_value = total_available * float(unit_cost)      

    return {
        'total_purchase': total_purchase,
        'total_local_purchase': total_local_purchase,
        'total_manufacture_in': total_manufacture_in,
        'total_manufacture_out': total_manufacture_out,
        'total_existing_in': total_Existing_in,
        'total_operations_out': total_operations_out,
        'total_sold': total_sold,
        'total_pos_sales': total_pos_sales,
        'total_online_sales': total_online_sales,
        'total_replacement_out': total_replacement_out,
        'total_replacement_in': total_replacement_in,
        'total_transfer_in': total_transfer_in,
        'total_transfer_out': total_transfer_out,
        'total_scrapped_in': total_scrapped_in,
        'total_scrapped_out': total_scrapped_out,
        'total_available': total_available,
        'total_stock': total_stock,
        'stock_value': stock_value
    }



######################### Performance evaluation service ######################








from typing import Optional

def get_latest_purchase(batch) -> Optional[object]:
    """
    Returns the latest purchase item for a given batch, considering both
    local shop purchases and corporate purchases. Returns None if no purchase exists.
    """
    local_purchase_item = getattr(batch, 'purchase_products', None)
    corporate_purchase_item = getattr(batch, 'batch_purchase_order_item', None)

    # Get latest for each type if available
    local_latest = local_purchase_item.order_by('-created_at').first() if local_purchase_item else None
    corporate_latest = corporate_purchase_item.order_by('-created_at').first() if corporate_purchase_item else None

    # Determine the latest overall
    if local_latest and corporate_latest:
        return local_latest if local_latest.created_at > corporate_latest.created_at else corporate_latest
    return local_latest or corporate_latest




