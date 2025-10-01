
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
import uuid
from django.db.models import Sum
from django.db import IntegrityError
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

from .forms import PurchaseShipmentForm,PurchaseDispatchItemForm
from .models import  PurchaseDispatchItem, PurchaseOrderItem,PurchaseShipment,PurchaseDispatchItem
from purchase.models import  QualityControl,PurchaseOrder
from inventory.models import Warehouse,Location

from messaging.views import create_notification
from django.core.paginator import Paginator
from core.forms import CommonFilterForm



@login_required
def create_purchase_shipment(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)

    if not purchase_order.approver_approval_status:
        messages.error(request, 'You cannot proceed due to pending permission.')
        return redirect('purchase:purchase_order_list')

    if request.method == 'POST':
        form = PurchaseShipmentForm(request.POST)
        if form.is_valid():
            try:
                shipment = form.save(commit=False)
                shipment.user = request.user
                shipment.purchase_order = purchase_order
                shipment.save()
                messages.success(request, f"Shipment {shipment.shipment_id} created successfully!")
                return redirect('logistics:purchase_shipment_detail', shipment_id=shipment.id)
            except Exception as e:
                messages.error(request, f"Error creating shipment: {e}")
    else:
        form = PurchaseShipmentForm()

    return render(request, 'logistics/purchase/create_shipment.html', {
        'form': form,
        'purchase_order': purchase_order,
    })



@login_required
def purchase_shipment_list(request):
    purchase_shipment = None
    purchase_shipments = PurchaseShipment.objects.all().order_by('-created_at')
    form = CommonFilterForm(request.GET or None)
    if form.is_valid():
        purchase_shipment = form.cleaned_data['purchase_shipment_id']
        if purchase_shipment:
             purchase_shipments =  purchase_shipments.filter(shipment_id=purchase_shipment)

    paginator = Paginator(purchase_shipments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    form=CommonFilterForm()

    return render(request,'logistics/purchase/shipment_list.html',
        {
            'purchase_shipments':purchase_shipments,
            'form':form,
            'page_obj':page_obj,
            'purchase_shipment':purchase_shipment
        })




@login_required
def purchase_shipment_detail(request, shipment_id):
    shipment = get_object_or_404(PurchaseShipment, id=shipment_id)
    tracking_updates = shipment.purchase_shipment_tracking.all()

    return render(request, 'logistics/purchase/shipment_details.html', {
        'shipment': shipment,
        'tracking_updates': tracking_updates,
    })


@login_required
def create_purchase_dispatch_item(request, dispatch_id):
    purchase_shipment = get_object_or_404(PurchaseShipment, id=dispatch_id)
    if 'dbasket' not in request.session:
        request.session['dbasket'] = []
    form = PurchaseDispatchItemForm(request.POST,purchase_shipment=purchase_shipment)    
    if request.method == 'POST':
        if 'add_to_basket' in request.POST:
            if form.is_valid():

                purchase_shipment = form.cleaned_data['purchase_shipment']
                dispatch_item = form.cleaned_data['dispatch_item']
                dispatch_quantity = form.cleaned_data['dispatch_quantity']
                dispatch_date = form.cleaned_data['dispatch_date']
                delivery_date = form.cleaned_data['delivery_date']

                dispatched_quantity_total = (
                    dispatch_item.order_dispatch_item.aggregate(total=Sum('dispatch_quantity'))['total'] or 0
                )

                total_in_basket = sum(
                    item['quantity'] for item in request.session['basket'] if item['id'] == dispatch_item.id
                )
                if dispatched_quantity_total and dispatch_item:
                
                    if dispatched_quantity_total + total_in_basket + dispatch_quantity > dispatch_item.quantity:
                        messages.error(request, f"Cannot add {dispatch_quantity} units of '{dispatch_item.product.name}' to the dispatch. The total dispatch quantity would exceed the ordered quantity.")
                        return redirect('logistics:create_purchase_dispatch_item', dispatch_id=dispatch_id)

                dispatch_date_str = dispatch_date.strftime('%Y-%m-%d') if dispatch_date else None
                delivery_date_str = delivery_date.strftime('%Y-%m-%d') if delivery_date else None

                dbasket = request.session.get('dbasket', [])
                product_in_basket = next(
                    (item for item in dbasket if item['id'] == dispatch_item.id), 
                    None
                )

                if product_in_basket:
                    product_in_basket['dispatch_quantity'] += dispatch_quantity
                else:
                    dbasket.append({
                        'id': dispatch_item.id,
                        'name': dispatch_item.product.name,
                        'quantity': dispatch_quantity,
                        'dispatch_date': dispatch_date_str,
                        'delivery_date': delivery_date_str,
                        'purchase_shipment_id': purchase_shipment.id
                    })

                request.session['dbasket'] = dbasket
                request.session.modified = True
                messages.success(request, f"Added '{dispatch_item.product.name}' to the purchase basket")
                return redirect('logistics:create_purchase_dispatch_item', dispatch_id=dispatch_id)

            else:
                messages.error(request, "Form is invalid. Please check the details and try again.")
        
        elif 'action' in request.POST:
            action = request.POST['action']
            product_id = int(request.POST.get('product_id', 0))

            if action == 'update':
                new_quantity = int(request.POST.get('quantity', 1))
                for item in request.session['dbasket']:
                    if item['id'] == product_id:
                        item['quantity'] = new_quantity
                        break
            elif action == 'delete':
                request.session['dbasket'] = [
                    item for item in request.session['dbasket'] if item['id'] != product_id
                ]

            request.session.modified = True
            messages.success(request, "Basket updated successfully.")
            return redirect('logistics:create_purchase_dispatch_item', dispatch_id=purchase_shipment.id)

        elif 'confirm_dispatch' in request.POST:
            dbasket = request.session.get('dbasket', [])
            if not dbasket:
                messages.error(request, "The dispatch basket is empty. Add items before confirming.")
                return redirect('logistics:create_purchase_dispatch_item', dispatch_id=purchase_shipment.id)

            return redirect('logistics:confirm_purchase_dispatch_item')

    dbasket = request.session.get('dbasket', [])
    form = PurchaseDispatchItemForm(purchase_shipment=purchase_shipment, initial={'purchase_shipment': purchase_shipment})  
    return render(request, 'logistics/purchase/create_purchase_dispatch_item.html', {
        'form': form,
        'dbasket': dbasket,
        'purchase_shipment': purchase_shipment,
    })


@login_required
def confirm_purchase_dispatch_item(request):
    dbasket = request.session.get('dbasket', [])

    purchase_shipment_id = dbasket[0].get('purchase_shipment_id') if dbasket else None
    if not dbasket or not purchase_shipment_id:
        messages.error(request, "The dispatch basket is empty or Purchase shipment ID is missing. Please add items to the dispatch basket.")       
        return redirect('logistics:dispatch_item_list') 
    purchase_shipment = get_object_or_404(PurchaseShipment, id=purchase_shipment_id)
    purchase_order = purchase_shipment.purchase_order
    supplier= purchase_order.supplier

    if request.method == 'POST':
        try:
            with transaction.atomic():

                for item in dbasket:
                    dispatch_item = get_object_or_404(PurchaseOrderItem, id=item['id'])

                    PurchaseDispatchItem.objects.create(
                        purchase_shipment=purchase_shipment,
                        dispatch_item=dispatch_item,
                        dispatch_quantity=item['quantity'],
                        dispatch_date=item['dispatch_date'],
                        delivery_date=item['delivery_date'],
                        status='IN_PROCESS',
                        user=request.user,
                    )

                create_notification(request.user,message=f'Items for purchase Shipment number:{purchase_shipment.shipment_id} has been dispatched by vendor:{purchase_shipment.purchase_order.supplier}',notification_type='SHIPMENT-NOTIFICATION')

                request.session['dbasket'] = []
                request.session.modified = True


                messages.success(request, "Purchase dispatch confirmed and created successfully.")
                return redirect('logistics:create_purchase_dispatch_item', dispatch_id=purchase_shipment.id)

        except Exception as e:
            messages.error(request, f"An error occurred while confirming the dispatch: {str(e)}")
            return redirect('logistics:create_purchase_dispatch_item', dispatch_id=purchase_shipment.id)

    return render(request, 'logistics/purchase/confirm_purchase_dispatch_item.html', {'dbasket': dbasket,'supplier':supplier})


@login_required
def dispatch_item_list(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    dispatch_items = PurchaseDispatchItem.objects.filter(dispatch_item__purchase_order=purchase_order)

    product_wise_totals = defaultdict(lambda: {
        'order_quantity': 0,
        'dispatch_quantity': 0,
        'good_quantity': 0,
        'bad_quantity': 0
    })

    shipments = {}
    qc_quantities = {} 

    for dispatch_item in dispatch_items:        
        shipment = dispatch_item.purchase_shipment
        product_name = dispatch_item.dispatch_item.product.name
        if shipment not in shipments:
            shipments[shipment] = []
        shipments[shipment].append(dispatch_item)

        product_wise_totals[product_name]['order_quantity'] += dispatch_item.dispatch_item.quantity or 0
        product_wise_totals[product_name]['dispatch_quantity'] += dispatch_item.dispatch_quantity or 0

        qc_entry = QualityControl.objects.filter(purchase_dispatch_item=dispatch_item).first()
        if qc_entry:
            good_quantity = qc_entry.good_quantity or 0
            bad_quantity = qc_entry.bad_quantity or 0

            product_wise_totals[product_name]['good_quantity'] += good_quantity
            product_wise_totals[product_name]['bad_quantity'] += bad_quantity

            qc_quantities[dispatch_item.id] = {
                'good_quantity': good_quantity,
                'bad_quantity': bad_quantity,
                'created_at': qc_entry.created_at
            }
        else:
            product_wise_totals[product_name]['good_quantity'] += 0
            product_wise_totals[product_name]['bad_quantity'] += 0

    context = {
        'purchase_order': purchase_order,
        'shipments': shipments,
        'product_wise_totals': dict(product_wise_totals),
        'qc_quantities': qc_quantities,    }

    return render(request, 'logistics/purchase/dispatch_item_list.html', context)


@login_required
def update_dispatch_status(request, dispatch_item_id):
    dispatch_item = get_object_or_404(PurchaseDispatchItem, id=dispatch_item_id)

    if request.method == 'POST':
        if dispatch_item.status in ['OBI','DELIVERED']:
            messages.info(request,'item has already been updated')
            return redirect('logistics:update_dispatch_status',dispatch_item_id)
        
        new_status = request.POST.get('new_status')
        old_status = dispatch_item.status
        dispatch_item.status = new_status
        if new_status == 'COMPLETED':
            messages.warning(request,'No further updated is needed for this item')
            return redirect('logistics:update_dispatch_status',dispatch_item_id)
        
        dispatch_item.save()  
        create_notification(request.user, message=f'Product: {dispatch_item.dispatch_item.product} status updated from {old_status} to {new_status}',notification_type='SHIPMENT-NOTIFICATION')     

    shipment = dispatch_item.purchase_shipment
    shipment.update_shipment_status()

    try:
        shipment = PurchaseShipment.objects.get(id=shipment.id)
        total_dispatch_items = shipment.shipment_dispatch_item.count()
        reached_items_count = shipment.shipment_dispatch_item.filter(status__in=['REACHED', 'OBI']).count()
        all_items_reached = reached_items_count == total_dispatch_items

        if all_items_reached:
            shipment.status = 'REACHED'
            shipment.purchase_order.status = 'REACHED'
            shipment.purchase_order.purchase_request_order.status = 'REACHED'
            shipment.save()
            shipment.purchase_order.save()

            logger.info(f"Shipment {shipment.id} marked as REACHED.")

            for dispatch_item in shipment.shipment_dispatch_item.filter(status__in=['REACHED', 'OBI']):
                create_notification(request.user, message=f'Item {dispatch_item.dispatch_item.product} has just reached',notification_type='SHIPMENT-NOTIFICATION')

    except PurchaseShipment.DoesNotExist:
        logger.error(f"Shipment {shipment.id} not found.")


    return redirect('logistics:dispatch_item_list', purchase_order_id=shipment.purchase_order.id)




def cancel_dispatch_item(request, dispatch_item_id):
    dispatch_item = get_object_or_404(PurchaseDispatchItem, id=dispatch_item_id)

    if request.method == "POST":
        dispatch_item.status = 'CANCELLED'
        dispatch_item.save()
        messages.success(request, "Dispatch item successfully cancelled.")

        return redirect('logistics:dispatch_item_list', purchase_order_id=dispatch_item.dispatch_item.purchase_order.id)
    return render(request, 'logistics/purchase/cancel_order_item.html', {'dispatch_item': dispatch_item})






from.models import PurchaseShipmentTracking

@login_required
def update_shipment_tracking(request, shipment_id):
    shipment = get_object_or_404(PurchaseShipment, id=shipment_id)
    status_options = ['PENDING','IN_PROCESS','READY_FOR_QC','DISPATCHED','ON_BOARD','IN_TRANSIT','CUSTOM_CLEARANCE_IN_PROCESS', 'REACHED','OBI', 'DELIVERED', 'PARTIAL_DELIVERED', 'CANCELLED']

    if request.method == 'POST':
        status_update = request.POST.get('status_update')
        remarks = request.POST.get('remarks')

        PurchaseShipmentTracking.objects.create(
            purchase_shipment=shipment,
            user=request.user,
            status_update=status_update,
            remarks=remarks
        )
        return redirect('logistics:purchase_shipment_detail', shipment_id=shipment.id)
    return render(request, 'shipment/purchase/update_shipment_tracking.html', {
        'shipment': shipment,
        'status_options':status_options
    })
