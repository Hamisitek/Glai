from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Review
from django.core.paginator import Paginator


def product_list(request):
    request.session['has_completed_order'] = False  # Allow new order session
    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '')
    categories = Category.objects.all()

    products = Product.objects.all()
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Paginate with 6 products per page
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop/product_list.html', {
        'page_obj': page_obj, 
        'categories': categories, 
        'search_query': search_query
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()  # Fetch all reviews related to the product

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
    })

def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        name = request.POST.get('name')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if name and rating and comment:
            Review.objects.create(product=product, name=name, rating=rating, comment=comment)
            return redirect('product_detail', product_id=product.id)  # Reload product page

    return redirect('product_detail', product_id=product.id)


def about(request):
    return render(request, 'shop/about.html')
