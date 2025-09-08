from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart = Cart(request)
    cart.add(product=product, quantity=quantity, update_quantity=True)
    return redirect('cart:cart_detail')



def cart_remove(request, product_id):
    """Remove an item from the cart."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    """Display the shopping cart."""
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


