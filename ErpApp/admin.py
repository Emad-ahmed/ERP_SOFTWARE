from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CustomerList, ActivityLog, Product, ItemName,SetPos,InvoiceProduct,PartyList, SetPosPurchase, Employee, PaymentMethodname, Voucher

from import_export.admin import ImportExportModelAdmin



admin.site.site_header = 'Gulf House Group'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'action')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'timestamp')

    def has_add_permission(self, request):
        return False



class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number')  
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        # Add your additional fieldsets if needed
    )

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(CustomerList)
class CustomerListAdmin(ImportExportModelAdmin):
    list_display = (
        'Debtors_Name', 'Print_As', 'Phone', 'Fax', 'Website', 'Contact_Person',
        'Address', 'Thana', 'City', 'Email', 'Status', 'Branch'
    )
    search_fields = ('Debtors_Name', 'Phone', 'Email')
    list_filter = ('City', 'Branch')
    list_per_page = 20  # Set the number of items displayed per page in the admin list view

    def save_model(self, request, obj, form, change):
        # Customize save_model if needed
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Customize save_related if needed
        super().save_related(request, form, formsets, change)

    # Customize other admin options as needed


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = (
        'item','sku', 'name', 'uom', 'vendor', 'brand', 'category', 'sub_category', 'product_type',
        'variation_name', 'variation_values', 'barcode_type', 'alert_quantity', 'lead_time',
        'reorder_quantity', 'reorder_date', 'expires_in', 'tax', 'purchase_price',
        'transport_cost', 'other_cost', 'cogs', 'profit_margin_base_seeling','profit_margin_mrp', 'base_selling_price',
        'mrp', 'opening_stock', 'inventory_location', 'weight', 'position', 'rack', 'row',
        'image', 'product_description', 'instruction', 'custom_field_1', 'custom_field_2',
        'custom_field_3', 'selling',
    )
    search_fields = ('sku', 'name', 'vendor', 'brand', 'category', 'sub_category')
    list_filter = ('product_type', 'tax', 'inventory_location', 'custom_field_3')

    fieldsets = (
        ('Basic Information', {
            'fields': ('item','name', 'sku', 'uom', 'vendor', 'brand', 'category', 'sub_category', 'product_type',
                       'variation_name', 'variation_values', 'barcode_type'),
        }),
        ('Inventory Information', {
            'fields': ('alert_quantity', 'lead_time', 'reorder_quantity', 'reorder_date', 'expires_in',
                       'tax', 'purchase_price', 'transport_cost', 'other_cost'),
        }),
        ('Pricing Information', {
            'fields': ('cogs', 'profit_margin_base_seeling','profit_margin_mrp', 'base_selling_price', 'mrp'),
        }),
        ('Stock Information', {
            'fields': ('opening_stock','max_order_quantity','min_order_quantity',),
        }),
        ('Location and Position', {
            'fields': ('inventory_location', 'weight', 'position', 'rack', 'row'),
        }),
        ('Additional Information', {
            'fields': ('image', 'product_description', 'instruction', 'custom_field_1', 'custom_field_2',
                       'custom_field_3', 'selling'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make sku, cogs, base_selling_price, and mrp readonly during add operation
        if obj is None:
            return ['sku', 'cogs', 'base_selling_price', 'mrp']
        # Make all fields editable during edit operation
        return []


@admin.register(ItemName)
class ItemnameAdmin(ImportExportModelAdmin):
    pass

@admin.register(SetPos)
class SetPosAdmin(ImportExportModelAdmin):
    pass

@admin.register(SetPosPurchase)
class SetPosPurchaseadmin(ImportExportModelAdmin):
    pass


@admin.register(InvoiceProduct)
class InvoiceProduct(ImportExportModelAdmin):
    pass



@admin.register(PartyList)
class PartyListAdmin(ImportExportModelAdmin):
    list_display = (
        'Party_Name', 'Print_As', 'Phone', 'Fax', 'Website', 'Contact_Person',
        'Address', 'Thana', 'City', 'Email', 'Status', 'Branch'
    )
    search_fields = ('Party_Name', 'Phone', 'Email')
    list_filter = ('City', 'Branch')
    list_per_page = 20  # Set the number of items displayed per page in the admin list view

    def save_model(self, request, obj, form, change):
        # Customize save_model if needed
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Customize save_related if needed
        super().save_related(request, form, formsets, change)

    # Customize other admin options as needed


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'job', 'hired_date', 'termination_date')
    search_fields = ('full_name', 'department', 'job', 'national_id', 'mobile_phone')
    list_filter = ('department', 'job', 'gender')
    ordering = ('full_name',)
    list_per_page = 20


@admin.register(PaymentMethodname)
class PaymentMethodnameAdmin(ImportExportModelAdmin):
    list_display = ('name', 'description', 'info_status')
    search_fields = ('name', 'description', 'info_status')


@admin.register(Voucher)
class VoucherAdmin(ImportExportModelAdmin):
    list_display = ('vouchernumber', 'amount', 'payment_status', 'description', 'date')
    search_fields = ('vouchernumber', 'description', 'date')
    list_filter = ('payment_status', 'date')
    date_hierarchy = 'date'
    ordering = ('-date',)

    # Customize the display of the ForeignKey fields
    raw_id_fields = ('salepos', 'purchasepos', 'account_info')