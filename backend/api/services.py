from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import (
    AuditLog, InventoryMovement, Notification, Order, OrderItem, Product,
    StockBalance, Warehouse,
)

TWOPLACES = Decimal('0.01')


def decimal(value, default='0'):
    try:
        return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except (TypeError, ValueError, ArithmeticError):
        return Decimal(default).quantize(TWOPLACES)


def request_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or None


def audit(request, action, entity, entity_id, summary, changes=None):
    company = getattr(request, 'company', None)
    if not company:
        return None
    return AuditLog.objects.create(
        company=company,
        actor=getattr(request, 'api_user', None),
        action=action,
        entity_type=entity,
        entity_id=str(entity_id),
        summary=summary[:240],
        changes=changes or {},
        ip_address=request_ip(request),
    )


def notify(company, title, message, level='info', module='', entity_id='', user=None):
    return Notification.objects.create(
        company=company, user=user, title=title[:140], message=message[:300],
        level=level, module=module, entity_id=str(entity_id or ''),
    )


def recompute_product_stock(product):
    total = StockBalance.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    Product.objects.filter(pk=product.pk).update(stock=total)
    product.stock = total
    return total


@transaction.atomic
def apply_stock(company, warehouse, product, quantity_delta, movement_type, reference, actor=None, notes=''):
    quantity_delta = decimal(quantity_delta)
    balance, _ = StockBalance.objects.select_for_update().get_or_create(
        warehouse=warehouse, product=product, defaults={'quantity': 0, 'reserved': 0}
    )
    new_quantity = balance.quantity + quantity_delta
    if new_quantity < 0:
        raise ValueError(f'Insufficient stock for {product.sku} in {warehouse.name}.')
    balance.quantity = new_quantity
    balance.save(update_fields=['quantity'])
    InventoryMovement.objects.create(
        company=company, warehouse=warehouse, product=product, movement_type=movement_type,
        quantity=quantity_delta, reference=reference, notes=notes, created_by=actor,
    )
    recompute_product_stock(product)
    return balance


@transaction.atomic
def reserve_order_stock(order, actor=None):
    if order.stock_reserved:
        return
    if not order.warehouse:
        raise ValueError('Order requires a warehouse before stock can be reserved.')
    locked = []
    for item in order.items.select_related('product').all():
        balance, _ = StockBalance.objects.select_for_update().get_or_create(
            warehouse=order.warehouse, product=item.product, defaults={'quantity': 0, 'reserved': 0}
        )
        available = balance.quantity - balance.reserved
        if available < item.quantity:
            raise ValueError(f'Only {available} {item.product.unit} available for {item.product.sku}.')
        locked.append((balance, item))
    for balance, item in locked:
        balance.reserved += item.quantity
        balance.save(update_fields=['reserved'])
        InventoryMovement.objects.create(
            company=order.company, warehouse=order.warehouse, product=item.product,
            movement_type=InventoryMovement.MovementType.RESERVATION, quantity=item.quantity,
            reference=order.order_no, notes='Reserved for confirmed sales order', created_by=actor,
        )
    order.stock_reserved = True
    order.save(update_fields=['stock_reserved', 'updated_at'])


@transaction.atomic
def release_order_stock(order, actor=None):
    if not order.stock_reserved or not order.warehouse:
        return
    for item in order.items.select_related('product').all():
        balance = StockBalance.objects.select_for_update().filter(warehouse=order.warehouse, product=item.product).first()
        if not balance:
            continue
        balance.reserved = max(Decimal('0'), balance.reserved - item.quantity)
        balance.save(update_fields=['reserved'])
        InventoryMovement.objects.create(
            company=order.company, warehouse=order.warehouse, product=item.product,
            movement_type=InventoryMovement.MovementType.RELEASE, quantity=-item.quantity,
            reference=order.order_no, notes='Reservation released', created_by=actor,
        )
    order.stock_reserved = False
    order.save(update_fields=['stock_reserved', 'updated_at'])


@transaction.atomic
def dispatch_order(order, actor=None):
    if order.status == Order.Status.DISPATCHED:
        return
    if not order.stock_reserved:
        reserve_order_stock(order, actor)
    for item in order.items.select_related('product').all():
        balance = StockBalance.objects.select_for_update().get(warehouse=order.warehouse, product=item.product)
        if balance.quantity < item.quantity:
            raise ValueError(f'Insufficient stock for {item.product.sku}.')
        balance.quantity -= item.quantity
        balance.reserved = max(Decimal('0'), balance.reserved - item.quantity)
        balance.save(update_fields=['quantity', 'reserved'])
        InventoryMovement.objects.create(
            company=order.company, warehouse=order.warehouse, product=item.product,
            movement_type=InventoryMovement.MovementType.SALE, quantity=-item.quantity,
            reference=order.order_no, notes='Sales order dispatched', created_by=actor,
        )
        recompute_product_stock(item.product)
    order.stock_reserved = False
    order.status = Order.Status.DISPATCHED
    order.save(update_fields=['stock_reserved', 'status', 'updated_at'])


def calculate_line(product, quantity, unit_price=None, discount_percent=0, gst_rate=None):
    qty = decimal(quantity)
    price = decimal(unit_price if unit_price is not None else product.sell_price)
    discount = decimal(discount_percent)
    gst = decimal(gst_rate if gst_rate is not None else product.gst_rate)
    gross = qty * price
    taxable = (gross * (Decimal('100') - discount) / Decimal('100')).quantize(TWOPLACES)
    tax = (taxable * gst / Decimal('100')).quantize(TWOPLACES)
    return {
        'quantity': qty, 'unit_price': price, 'discount_percent': discount, 'gst_rate': gst,
        'taxable': taxable, 'tax': tax, 'total': taxable + tax,
    }


def create_order_items(order, items):
    subtotal = Decimal('0')
    tax = Decimal('0')
    for row in items:
        product = Product.objects.get(pk=row['product_id'], company=order.company, is_active=True)
        line = calculate_line(product, row.get('quantity', 1), row.get('unit_price'), row.get('discount_percent', 0), row.get('gst_rate'))
        OrderItem.objects.create(
            order=order, product=product, quantity=line['quantity'], unit_price=line['unit_price'],
            discount_percent=line['discount_percent'], gst_rate=line['gst_rate'],
            taxable_amount=line['taxable'], tax_amount=line['tax'], line_total=line['total'],
        )
        subtotal += line['taxable']
        tax += line['tax']
    order.subtotal = subtotal
    order.tax = tax
    order.total = subtotal + tax - order.discount
    order.save(update_fields=['subtotal', 'tax', 'total', 'updated_at'])
    return order
