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

   

        
    path('cancel_transaction/', CancelTransactionView.as_view(), name='cancel_transaction'),

    path('product-details/<int:id>/', ProductDetailsView.as_view(), name='product-details'),
    path('product-details-by-name/<str:name>/', ProductDetailsNameView.as_view(), name='product-details-by-name'),
    path('save_invoice/', save_invoice, name='save_draft'),
    path('save_invoice_purchase/', save_invoice_purchase, name='save_invoice_purchase'),
    path('transaction/', TransactionView.as_view(), name='transaction'),
    path('purchaselist/', PurchaseListView.as_view(), name='purchaselist'),
    path('new_edit_invoice/', EditInvoiceView.as_view(), name='new_edit_invoice'),
    path('new_return_invoice/', EditRetunView.as_view(), name='new_return_invoice'),

    path('delivery_add/', DeliveryInvoiceView.as_view(), name='delivery_add'),
    path('delivery_add_purchase/', DeliveryPurchaseInvoiceView.as_view(), name='delivery_add_purchase'),
    path('get-deliverydata/', get_delivery_data, name='get_delivery_data'),
    path('get_delivery_data_purchase/', get_delivery_data_purchase, name='get_delivery_data_purchase'),

    path('new_edit_invoice_purchase/', EditInvoicePurchaseView.as_view(), name='new_edit_invoice_purchase'),
    path('new_ordersheet/', NewOrderSheet.as_view(), name='new_ordersheet'),
    path('get-customer-data/', get_customer_data, name='get_customer_data'),
    path('generate_invoice_pdf/', generate_invoice_pdf, name='generate_invoice_pdf'),
    path('generate_return_invoice_pdf/', generate_return_invoice_pdf, name='generate_return_invoice_pdf'),
    path('update_save_invoice/', update_save_invoice, name='update_save_invoice'),
    path('return_save_invoice/', return_save_invoice, name='return_save_invoice'),
    path('update_save_invoice_purchase/', update_save_invoice_purchase, name='update_save_invoice_purchase'),
    path('update_delivery_status/', update_delivery_status, name='update_delivery_status'),
    path('delete_pos_purchase/', delete_pos_purchase, name='delete_pos_purchase'),
    path('delete_invoice_transacrtion_cancel/', delete_invoice_transacrtion_cancel, name='delete_invoice_transacrtion_cancel'),
    path('delete_invoice_transacrtion/', delete_invoice_transaction, name='delete_invoice_transacrtion'),
    path('generate_invoice_pdf_purchase/', generate_invoice_pdf_purchase, name='generate_invoice_pdf_purchase'),

    path('delete_delivery_product/', delete_delivery_product, name='delete_delivery_product'),


    path('delivery_invoice/', delivery_invoice, name='delivery_invoice'),
    path('delivery_invoice_purchase/', delivery_invoice_purchase, name='delivery_invoice_purchase'),
    path('delivery_show/', DeliveryshowView.as_view(), name='delivery_show'),
    path('delivery_show_purchase/', PurchaseDeliveryshowView.as_view(), name='delivery_show_purchase'),

    path('customer/create/', create_or_update_customer, name='create_customer'),
    path('customer/<int:customer_id>/update/', create_or_update_customer, name='update_customer'),
    path('customer/list/', customer_list, name='customer_list'),
    path('customer/delete/<int:customer_id>/', delete_customer, name='delete_customer'),

    path('generate_return_delivery_invoice_pdf/', generate_return_delivery_invoice_pdf, name='generate_return_delivery_invoice_pdf'),

    path('party/create/', create_or_update_party, name='create_party'),
    path('party/<int:party_id>/update/', create_or_update_party, name='update_party'),
    path('party/list/', party_list, name='party_list'),
    path('party/delete/<int:party_id>/', delete_party, name='delete_party'),

    path('product/create/', create_or_update_product, name='create_product'),
    path('product/<int:product_id>/update/', create_or_update_product, name='update_product'),
    path('product/list/', product_list, name='product_list'),
    path('product/delete/<int:product_id>/', delete_product, name='delete_product'),

    path("order_Stock/", Order_Stock.as_view(), name="order_Stock"),

    path('employee/create/', create_or_update_employee, name='create_employee'),
    path('employee/<int:employee_id>/update/', create_or_update_employee, name='update_employee'),
    path('employee/list/', employee_list, name='employee_list'),
    path('employee/delete/<int:employee_id>/', delete_employee, name='delete_employee'),

    path('voucher/create/', create_or_update_voucher, name='create_voucher'),
    path('voucher/<int:voucher_id>/update/', create_or_update_voucher, name='update_voucher'),
    path('voucher/list/', voucher_list, name='voucher_list'),
    path('voucher/delete/<int:voucher_id>/', delete_voucher, name='delete_voucher'),
    path('customer/details/account/<int:customer_id>/', customer_details_account, name='customerDetailsaccount'),
    # path('get_product_details/<int:product_id>/', get_product_details, name='get_product_details'),
    # path('generate_barcode/<int:product_id>/', generate_barcode_view, name='generate_barcode'),
    path('sale_cancelation/', Salecancel_view.as_view(), name='sale_cancelation'),
    path('product_ledger/', ProductLedgerView.as_view(), name='product_ledger'),
]






