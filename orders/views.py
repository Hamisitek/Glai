# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from cart.cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem, Payment, Bank
from .mpesa_payment import initiate_c2b_payment, get_session_key
import uuid
import logging
import json

logger = logging.getLogger(__name__)


def checkout(request):
    cart = Cart(request)
    if not cart.cart:
        return redirect('shop:product_list')

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        payment_method = request.POST.get('payment_method')
        bank_name = request.POST.get('bank_name') if payment_method == 'bank' else None

        if form.is_valid():
            with transaction.atomic():
                # Create Order
                order = Order.objects.create(
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    address=form.cleaned_data['address'],
                    phone=form.cleaned_data['phone'],
                    payment_method=payment_method,
                    bank_name=bank_name
                )

                # Add items
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        price=item['price'],
                        quantity=item['quantity']
                    )

                # Create payment record
                payment = Payment.objects.create(
                    order=order,
                    method=payment_method,
                    amount=order.get_total_price(),
                    status='pending'
                )

                # Clear cart
                cart.clear()

            # --- M-Pesa Payment ---
            if payment_method == "mpesa":
                transaction_reference = str(uuid.uuid4())[:20]
                msisdn = form.cleaned_data['phone']
                purchased_items = ", ".join([item.product.name for item in OrderItem.objects.filter(order=order)])

                try:
                    session_key = get_session_key()
                    response = initiate_c2b_payment(
                        session_key=session_key,
                        msisdn=msisdn,
                        amount=order.get_total_price()
                    )

                    # Update payment
                    payment.response = response
                    payment.transaction_id = transaction_reference
                    payment.status = 'awaiting_confirmation'
                    payment.save()

                    # Determine status for display
                    last_digit = order.phone[-1] if order.phone else "0"
                    if last_digit == "1":
                        payment_status_text = "Transaction Successful"
                        payment_status_class = "status-success"
                        instruction_text = "Follow instructions on your phone to finalize the order."
                    else:
                        payment_status_text = "Transaction Pending / Failed"
                        payment_status_class = "status-failed"
                        instruction_text = "Payment failed or is pending. Please try again or contact support."

                    context = {
                        "order": order,
                        "payment": payment,
                        "items": OrderItem.objects.filter(order=order),
                        "payment_status_text": payment_status_text,
                        "payment_status_class": payment_status_class,
                        "instruction_text": instruction_text,
                    }
                    return render(request, "orders/mpesa_pending.html", context)

                except Exception as e:
                    logger.error(f"M-Pesa payment error: {str(e)}")
                    return render(request, "orders/payment_error.html", {
                        "order": order,
                        "error": f"M-Pesa payment failed: {str(e)}"
                    })

            # Bank payment
            elif payment_method == "bank":
                selected_bank = Bank.objects.filter(name__iexact=bank_name).first() or Bank.objects.first()
                return render(request, "orders/bank_instructions.html", {
                    "order": order,
                    "bank_info": selected_bank
                })

            # Other payments
            elif payment_method in ["mixx", "airtel"]:
                context = {
                    "order": order,
                    "items": OrderItem.objects.filter(order=order),
                    "payment": payment,
                    "payment_method": payment_method,
                    "payment_status_text": "Payment Pending",
                }
                return render(request, f"orders/{payment_method}_pending.html", context)

            else:
                return render(request, "orders/payment_error.html", {
                    "order": order,
                    "error": "Unknown payment method selected."
                })

    else:
        form = CheckoutForm()

    return render(request, "orders/checkout.html", {"form": form})


def track_order(request):
    order = None
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        email = request.POST.get("email")
        try:
            order = Order.objects.get(id=order_id, email=email)
        except Order.DoesNotExist:
            order = None

    return render(request, 'orders/order_tracking.html', {'order': order}) 



def order_success(request):
    order_id = request.session.get('last_order_id')
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).first()

    return render(request, 'orders/order_success.html', {'order': order})

# -------------------
# HTML Preview View
# -------------------
def invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    for item in order_items:
        item.total_price = item.price * item.quantity
    total = sum(item.total_price for item in order_items)

    # Bank info
    bank_info = None
    bank_logo_url = None
    if order.payment_method == 'bank' and order.bank_name:
        bank_info = Bank.objects.filter(name=order.bank_name).first()
        if bank_info and bank_info.logo:
            bank_logo_url = bank_info.logo.url

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'bank_info': bank_info,
        'bank_logo_url': bank_logo_url,
        'company_logo': static('images/logo.jpg'),
        'stamp_image': static('images/stamp_01.jpg'),
        'signature_image': static('images/signature_01.jpg'),
        'now': timezone.now(),
        'pdf': False,  # HTML preview
    }

    return render(request, 'orders/invoice.html', context)

# -------------------
# PDF Download View
# -------------------
from weasyprint import HTML, CSS
from django.templatetags.static import static
from django.conf import settings

def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    for item in order_items:
        item.total_price = item.price * item.quantity
    total = sum(item.total_price for item in order_items)

    bank_info = None
    bank_logo_url = None
    if order.payment_method == 'bank' and order.bank_name:
        bank_info = Bank.objects.filter(name=order.bank_name).first()
        if bank_info and bank_info.logo and os.path.exists(bank_info.logo.path):
            bank_logo_url = f'file://{bank_info.logo.path}'

    # Convert static paths into absolute file:// paths for PDF
    def abs_static(path):
        return f'file://{os.path.join(settings.BASE_DIR, "static", path)}'

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'bank_info': bank_info,
        'bank_logo_url': bank_logo_url,
        'company_logo': abs_static('images/logo.jpg'),
        'stamp_image': abs_static('images/stamp_01.jpg'),
        'signature_image': abs_static('images/signature_01.jpg'),
        'now': timezone.now(),
        'pdf': True,
    }

    # Render HTML with context
    html_string = render_to_string('orders/invoice.html', context)

    # Generate PDF (absolute base_url required so images/css resolve)
    pdf_file = HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response

# --------------------#
# Mpesa Callback View #
#  -------------------#

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Payment, Order
import json


@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f"MPESA CALLBACK RECEIVED: {data}")

        transaction_ref = data.get("input_TransactionReference")
        status_code = data.get("output_ResponseCode")

        if not transaction_ref:
            logger.warning("Transaction reference missing in callback")
            return JsonResponse({"status": "error", "message": "Missing transaction reference"}, status=400)

        payment = Payment.objects.filter(transaction_id=transaction_ref).first()
        if not payment:
            logger.warning(f"No payment found for transaction {transaction_ref}")
            return JsonResponse({"status": "error", "message": "Payment record not found"}, status=404)

        payment.response = data
        if status_code == "INS-0":
            payment.status = "success"
            payment.order.status = "paid"
            payment.order.save()
        else:
            payment.status = "failed"
        payment.save()

        return JsonResponse({"status": "received"})

    except json.JSONDecodeError:
        logger.error("Invalid JSON received in callback")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception("Error processing M-Pesa callback")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
