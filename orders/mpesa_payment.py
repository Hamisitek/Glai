# orders/mpesa_payment.py
from portalsdk import APIContext, APIMethodType, APIRequest
from time import sleep
import json

# -------------------------
# CONFIGURATION
# -------------------------
SANDBOX_API_KEY = "aVPKo3ZIPU21B8EgdhLegm0wAVNPuGUq"
SANDBOX_PUBLIC_KEY = """MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEArv9yxA69XQKBo24BaF/D+
fvlqmGdYjqLQ5WtNBb5tquqGvAvG3WMFETVUSow/LizQalxj2ElMVrUmzu5mGGkxK08bWEX
F7a1DEvtVJs6nppIlFJc2SnrU14AOrIrB28ogm58JjAl5BOQawOXD5dfSk7MaAA82pVHoIq
Eu0FxA8BOKU+RGTihRU+ptw1j4bsAJYiPbSX6i71gfPvwHPYamM0bfI4CmlsUUR3KvCG24r
B6FNPcRBhM3jDuv8ae2kC33w9hEq8qNB55uw51vK7hyXoAa+U7IqP1y6nBdlN25gkxEA8yr
sl1678cspeXr+3ciRyqoRgj9RD/ONbJhhxFvt1cLBh+qwK2eqISfBb06eRnNeC71oBokDm3
zyCnkOtMDGl7IvnMfZfEPFCfg5QgJVk1msPpRvQxmEsrX9MQRyFVzgy2CWNIb7c+jPapyrN
woUbANlN8adU1m6yOuoX7F49x+OjiG2se0EJ6nafeKUXw/+hiJZvELUYgzKUtMAZVTNZfT8
jjb58j8GVtuS+6TM2AutbejaCV84ZK58E2CRJqhmjQibEUO6KPdD7oTlEkFy52Y1uOOBXgY
pqMzufNPmfdqqqSM4dU70PO8ogyKGiLAIxCetMjjm6FCMEA3Kc8K0Ig7/XtFm9By6VxTJK1
Mg36TlHaZKP6VzVLXMtesJECAwEAAQ=="""
SESSION_PATH = "/sandbox/ipg/v2/vodacomTZN/getSession/"
C2B_PATH = "/sandbox/ipg/v2/vodacomTZN/c2bPayment/singleStage/"

# -------------------------
# HELPER FUNCTION: SAFE EXECUTE
# -------------------------
def safe_execute(api_request):
    """
    Wrap APIRequest.execute() to avoid JSON decode errors in sandbox.
    Returns raw response object; parse JSON manually after.
    """
    original_json_loads = json.loads
    json.loads = lambda s: s  # monkey patch
    try:
        result = api_request.execute()
    finally:
        json.loads = original_json_loads
    return result

# -------------------------
# SESSION KEY
# -------------------------
def get_session_key():
    api_context = APIContext()
    api_context.api_key = SANDBOX_API_KEY
    api_context.public_key = SANDBOX_PUBLIC_KEY
    api_context.ssl = True
    api_context.method_type = APIMethodType.GET
    api_context.address = "openapi.m-pesa.com"
    api_context.port = 443
    api_context.path = SESSION_PATH
    api_context.add_header("Origin", "*")

    api_request = APIRequest(api_context)
    result = safe_execute(api_request)

    # Parse manually
    session_data = json.loads(result.body)
    session_id = session_data["output_SessionID"]
    return session_id

# -------------------------
# C2B PAYMENT
# -------------------------
def initiate_c2b_payment(session_key, msisdn, amount, transaction_reference="TX12345", purchased_items="Test Product"):
    """
    Initiates a sandbox C2B payment. MSISDN and amount are required.
    """
    sleep(25)  # session activation in sandbox

    api_context = APIContext()
    api_context.api_key = session_key
    api_context.public_key = SANDBOX_PUBLIC_KEY
    api_context.ssl = True
    api_context.method_type = APIMethodType.POST
    api_context.address = "openapi.m-pesa.com"
    api_context.port = 443
    api_context.path = C2B_PATH
    api_context.add_header("Origin", "*")

    # Add parameters
    api_context.add_parameter("input_Amount", str(amount))
    api_context.add_parameter("input_Country", "TZN")
    api_context.add_parameter("input_Currency", "TZS")
    api_context.add_parameter("input_CustomerMSISDN", msisdn)
    api_context.add_parameter("input_ServiceProviderCode", "000000")                     
    api_context.add_parameter("input_ThirdPartyConversationID", "test123")
    api_context.add_parameter("input_TransactionReference", transaction_reference)
    api_context.add_parameter("input_PurchasedItemsDesc", purchased_items)

    api_request = APIRequest(api_context)
    result = safe_execute(api_request)

    # Manual JSON parse
    body_data = json.loads(result.body)
    return body_data

# Optional standalone test
if __name__ == "__main__":
    session_key = get_session_key()
    test_response = initiate_c2b_payment(session_key, msisdn="255746441776", amount=100)
    print(test_response)

