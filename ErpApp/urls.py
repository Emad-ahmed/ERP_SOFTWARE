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
    path('new_edit_invoice_purchase', EditInvoicePurchaseView.as_view(), name='new_edit_invoice_purchase'),
    path('new_ordersheet/', NewOrderSheet.as_view(), name='new_ordersheet'),
    path('get-customer-data/', get_customer_data, name='get_customer_data'),
    path('generate_invoice_pdf/', generate_invoice_pdf, name='generate_invoice_pdf'),
    path('update_save_invoice/', update_save_invoice, name='update_save_invoice'),
    path('update_save_invoice_purchase/', update_save_invoice_purchase, name='update_save_invoice_purchase'),
    path('update_delivery_status/', update_delivery_status, name='update_delivery_status'),
    path('delete_pos_purchase/', delete_pos_purchase, name='delete_pos_purchase'),
    path('generate_invoice_pdf_purchase/', generate_invoice_pdf_purchase, name='generate_invoice_pdf_purchase'),

    path('customer/create/', create_or_update_customer, name='create_customer'),
    path('customer/<int:customer_id>/update/', create_or_update_customer, name='update_customer'),
    path('customer/list/', customer_list, name='customer_list'),
    path('customer/delete/<int:customer_id>/', delete_customer, name='delete_customer'),


    path('party/create/', create_or_update_party, name='create_party'),
    path('party/<int:party_id>/update/', create_or_update_party, name='update_party'),
    path('party/list/', party_list, name='party_list'),
    path('party/delete/<int:party_id>/', delete_party, name='delete_party'),


    path('item/create/', create_or_update_item, name='create_item'),
    path('item/<int:item_id>/update/', create_or_update_item, name='update_item'),
    path('item/list/', item_list, name='item_list'),
    path('item/delete/<int:item_id>/', delete_item, name='delete_item'),

    path('product/create/', create_or_update_product, name='create_product'),
    path('product/<int:product_id>/update/', create_or_update_product, name='update_product'),
    path('product/list/', product_list, name='product_list'),
    path('product/delete/<int:product_id>/', delete_product, name='delete_product'),

    
    path('employee/create/', create_or_update_employee, name='create_employee'),
    path('employee/<int:employee_id>/update/', create_or_update_employee, name='update_employee'),
    path('employee/list/', employee_list, name='employee_list'),
    path('employee/delete/<int:employee_id>/', delete_employee, name='delete_employee')
    
]






