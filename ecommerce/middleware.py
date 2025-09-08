from django.shortcuts import redirect

class PreventDirectAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of protected pages
        protected_paths = ['/orders/checkout/', '/orders/success/']

        for path in protected_paths:
            if request.path == path:
                if request.session.get('has_completed_order', False):
                    return redirect('shop:product_list')
        return self.get_response(request)

