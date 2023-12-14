from django.urls import path
from .views import *

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('home', HomeView.as_view(), name='home'),
    path('new_invoice', NewInvoice.as_view(), name='new_invoice'),
    path('new_purchase_list/', NewPurchase.as_view(), name='new_purchase_list'),
    path('customer-list/', CustomerListView.as_view(), name='customer-list'),
    path('party-list/', PartyListView.as_view(), name='party-list'),
    path('product-list/', ProductListView.as_view(), name='product-list'),
    path('item-list/', ItemListView.as_view(), name='item-list'),
    path('product-details/<int:id>/', ProductDetailsView.as_view(), name='product-details'),
    path('product-details-by-name/<str:name>/', ProductDetailsNameView.as_view(), name='product-details-by-name'),
    path('save_invoice/', save_invoice, name='save_draft'),
    path('save_invoice_purchase/', save_invoice_purchase, name='save_invoice_purchase'),
    path('transaction/', TransactionView.as_view(), name='transaction'),
    path('purchaselist/', PurchaseListView.as_view(), name='purchaselist'),
    path('new_edit_invoice', EditInvoiceView.as_view(), name='new_edit_invoice'),
    path('new_ordersheet/', NewOrderSheet.as_view(), name='new_ordersheet'),
    path('get-customer-data/', get_customer_data, name='get_customer_data'),
    path('generate_invoice_pdf/', generate_invoice_pdf, name='generate_invoice_pdf'),
    path('update_save_invoice/', update_save_invoice, name='update_save_invoice'),
    path('update_delivery_status/', update_delivery_status, name='update_delivery_status'),
    path('generate_invoice_pdf_purchase/', generate_invoice_pdf_purchase, name='generate_invoice_pdf_purchase'),
]






