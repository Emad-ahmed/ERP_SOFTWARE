from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import random
from django.db.models import Max
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.utils import timezone

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

ROLE_CHOICES = [
    ('Sale', 'Sale'),
    ('Purchase', 'Purchase'),
    ('Delivery', 'Delivery'),
    ('Cashier', 'Cashier'),
    ('Financial Manager', 'Financial Manager'),
    ('General Manager', 'General Manager'),
    ('Director', 'Director'),
    ('CEO', 'CEO'),
]

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',  # Set a unique related_name for CustomUser's groups
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_users_permissions',  # Set a unique related_name for CustomUser's user_permissions
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        error_messages={
            'add': 'User cannot be assigned the permission because they do not have the view permission.',
            'remove': 'User cannot have the permission removed because they do not have the view permission.',
        },
    )




class CustomerList(models.Model):
    Debtors_Name = models.CharField(max_length=20, blank=True, null=True)
    Print_As = models.CharField(max_length=20, blank=True, null=True)  # Same column name as Debtors_Name
    Phone = models.CharField(max_length=50, blank=True, null=True)
    Fax = models.CharField(max_length=50, blank=True, null=True)
    Website = models.CharField(max_length=50, blank=True, null=True)
    Contact_Person = models.CharField(max_length=50, blank=True, null=True)
    Address = models.TextField(null=True)
    Thana = models.CharField(max_length=50, blank=True, null=True)
    City = models.CharField(max_length=50, blank=True, null=True)
    Email = models.EmailField(max_length=50, blank=True, null=True)
    Status = models.BooleanField(blank=True, null=True)
    Branch = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.Debtors_Name

    def save(self, *args, **kwargs):
        # Set Print_As to the same value as Debtors_Name before saving
        self.Print_As = self.Debtors_Name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.Debtors_Name} - {self.Phone}"




class ItemName(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name



class Product(models.Model):
    # Basic Information
    item = models.ForeignKey(ItemName, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.PositiveIntegerField(unique=True, blank=True, null=True)
    uom = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    sub_category = models.CharField(max_length=255, null=True, blank=True)
    product_type = models.CharField(max_length=50, choices=[('single', 'Single'), ('group', 'Group')])
    variation_name = models.CharField(max_length=255, blank=True)
    variation_values = models.CharField(max_length=255, blank=True)
    barcode_type = models.CharField(max_length=255, null=True, blank=True)

    # Inventory Information
    alert_quantity = models.IntegerField(default=0, null=True, blank=True)
    lead_time = models.IntegerField(default=0, null=True, blank=True)
    reorder_quantity = models.IntegerField(default=0, null=True, blank=True)
    reorder_date = models.DateField()
    expires_in = models.IntegerField(default=0, null=True, blank=True)
    tax = models.IntegerField(default=0, null=True, blank=True)
    purchase_price = models.FloatField()
    transport_cost = models.FloatField(default=0, null=True, blank=True)
    other_cost = models.FloatField(default=0, null=True, blank=True)

    # Cost of Goods Sold (COGS)
    cogs = models.FloatField(null=True, blank=True)

    profit_margin_base_seeling = models.IntegerField(default=45)
    profit_margin_mrp = models.IntegerField(null=True, blank=True, default=0)

    # Pricing Information
    base_selling_price = models.FloatField(blank=True, null=True)

    def calculate_mrp(self):
        if self.profit_margin_mrp is None or self.profit_margin_mrp == 0:
            # If profit_margin_mrp is None or 0, use the default percentage (0.10)
            return self.base_selling_price + (self.base_selling_price * 0.10)
        else:
            # Use the provided profit_margin_mrp value
            return self.base_selling_price + (self.base_selling_price * (self.profit_margin_mrp / 100))

    mrp = models.FloatField(null=True, blank=True)

    # Stock Information
    opening_stock = models.IntegerField(default=0, null=True, blank=True)

    # Location and Position
    inventory_location = models.CharField(max_length=255)
    weight = models.FloatField(default=0, null=True, blank=True)
    position = models.IntegerField(default=0, null=True, blank=True)
    rack = models.IntegerField(default=0,null=True, blank=True)
    row = models.IntegerField(default=0,null=True, blank=True)

    # Additional Information
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    product_description = models.TextField(null=True, blank=True)
    instruction = models.TextField(null=True, blank=True)
    custom_field_1 = models.CharField(max_length=255, blank=True)
    custom_field_2 = models.CharField(max_length=255, blank=True)
    custom_field_3 = models.CharField(max_length=255, blank=True)
    selling = models.BooleanField(default=False)

    def calculate_base_selling_price(self):
        return self.cogs + (self.cogs * (self.profit_margin_base_seeling  / 100))

    def calculate_cogs(self):
        tax = self.tax or 0
        total_cogs = self.purchase_price + (self.purchase_price * (tax / 100)) + self.other_cost
        return total_cogs
    def __str__(self):
            return self.name
    def save(self, *args, **kwargs):
        if not self.sku:
        # Get the maximum existing SKU
            max_sku = Product.objects.aggregate(Max('sku'))['sku__max']

            # If there are no existing SKUs, start from 1000
            if max_sku is None:
                max_sku = 1110

            # Increment the maximum SKU to generate a new one
            self.sku = max_sku + 1


        # Check if cogs is None and calculate if needed
        if self.cogs is None:
            self.cogs = self.calculate_cogs()

        # Always calculate and update base_selling_price
        self.base_selling_price = self.calculate_base_selling_price()

        # Always calculate and update mrp
        self.mrp = self.calculate_mrp()

        super(Product, self).save(*args, **kwargs)

        
class InvoiceProduct(models.Model):
    
    name = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255)
    sku = models.IntegerField()
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=100, default="kg")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self) -> str:
        return self.name

class SetPos(models.Model):
    customer = models.ForeignKey(CustomerList, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    total_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total_with_discount = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(InvoiceProduct)
    status = models.CharField(max_length=100)
    invoice_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(auto_now_add=True)
    invoice_by = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.customer.Debtors_Name





class PartyList(models.Model):
    Party_Name = models.CharField(max_length=20, blank=True, null=True)
    Print_As = models.CharField(max_length=20, blank=True, null=True)  # Same column name as Debtors_Name
    Phone = models.CharField(max_length=50, blank=True, null=True)
    Fax = models.CharField(max_length=50, blank=True, null=True)
    Website = models.CharField(max_length=50, blank=True, null=True)
    Contact_Person = models.CharField(max_length=50, blank=True, null=True)
    Address = models.TextField(null=True)
    Thana = models.CharField(max_length=50, blank=True, null=True)
    City = models.CharField(max_length=50, blank=True, null=True)
    Email = models.EmailField(max_length=50, blank=True, null=True)
    Status = models.BooleanField(blank=True, null=True)
    Branch = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.Party_Name

    def save(self, *args, **kwargs):
        # Set Print_As to the same value as Debtors_Name before saving
        self.Print_As = self.Party_Name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.Party_Name} - {self.Phone}"


class SetPosPurchase(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Start Progress', 'Start Progress'),
        ('Complete', 'Complete'),
        ('Reject', 'Reject'),
        ('Close', 'Close'),
        # Add more choices as needed
    ]
    party = models.ForeignKey(PartyList, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    total_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total_with_discount = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(InvoiceProduct)
    status = models.CharField(max_length=100)
    delivery_status = models.CharField(
        max_length=100,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending',  
        null=True,
        blank=True
    )
    amount = models.IntegerField(null=True, blank=True, default=0)
    paid_amount = models.IntegerField(null=True, blank=True, default=0)
    due_amount = models.IntegerField(null=True, blank=True, default=0)
    description = models.TextField(null=True, blank=True, default="null")
    invoice_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=100, null=True, blank=True, default="Head Branch")
    invoice_by = models.CharField(max_length=100)
    approved_by = models.CharField(max_length=100, default="Hussain", null=True, blank=True)

    def __str__(self) -> str:
        return self.party.Party_Name