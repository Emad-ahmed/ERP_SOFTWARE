from django.shortcuts import render
from django.views import View
import subprocess
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import ActivityLog,CustomerList,Product, SetPos, InvoiceProduct,  PartyList, SetPosPurchase, Employee, Voucher, Account, SetPosCancelation
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import link_callback
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from reportlab.lib import styles
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from django.views.decorators.http import require_POST
from .forms import CustomerListForm, PartyListForm,  ProductForm, ProductUpdateForm, EmployeeForm, VoucherForm
from django.contrib import messages
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from barcode import Code128
from barcode.writer import ImageWriter
from django.conf import settings
from io import BytesIO
from django.db.models import Sum
from django.db import transaction
class LoginView(View):
    def get(self, request):
        return render(request, 'login/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Log login activity
            ActivityLog.objects.create(user=user, action='User logged in')

            return redirect('home')  # Redirect to your home page or another view
        else:
            error_message = 'Wrong Email and Password'
            return render(request, 'login/login.html', {'error_message': error_message})

class HomeView(View):
    def get(self, request):
        total_with_discount_sum = SetPos.objects.aggregate(total_sum=Sum('total_with_discount'))['total_sum']
        paid_amount_sum = SetPos.objects.aggregate(paid_sum=Sum('paid_amount'))['paid_sum']
        due_amount_sum = SetPos.objects.aggregate(due_sum=Sum('due_amount'))['due_sum']
        if request.user.is_authenticated:
            return render(request, 'ERP/home.html', {
            'total_with_discount_sum': total_with_discount_sum,
            'paid_amount_sum': paid_amount_sum,
            'due_amount_sum': due_amount_sum,
        })
        else:
            return redirect("/")


class CustomerListView(View):
    def get(self, request):
        customer_data = list(CustomerList.objects.values('id', 'Debtors_Name', 'Phone', 'Address'))
        return JsonResponse({'customer_data': customer_data})

class ProductListView(View):
    def get(self, request):
        product_data = list(Product.objects.values('id', 'name', 'sku', 'mrp', 'uom', 'purchase_price'))
        return JsonResponse({'product_data': product_data})


class NewInvoice(View):
    def get(self, request):
        customerform = CustomerListForm() 
        return render(request, 'ERP/new_invoice_add.html', {'customerform': customerform})

    def post(self, request):
        customerform = CustomerListForm(request.POST)
        if customerform.is_valid():
            customer = customerform.save()
            messages.success(request, 'Customer saved successfully!')
            return redirect('new_invoice')  # Replace 'your_redirect_view_name' with the actual name or URL of the view you want to redirect to
        else:
            messages.error(request, 'Error saving customer. Please check the form.')
        
        return render(request, 'ERP/new_invoice_add.html', {'customerform': customerform})
    

class ProductDetailsView(View):
    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product_data = {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'uom': product.uom,
                'vendor': product.vendor,
                'brand': product.brand,
                'category': product.category,
                'sub_category': product.sub_category,
                'product_type': product.product_type,
                'variation_name': product.variation_name,
                'variation_values': product.variation_values,
                'barcode_type': product.barcode_type,
                'alert_quantity': product.alert_quantity,
                'lead_time': product.lead_time,
                'reorder_quantity': product.reorder_quantity,
                'reorder_date': product.reorder_date,
                'expires_in': product.expires_in,
                'tax': product.tax,
                'purchase_price': product.purchase_price,
                'transport_cost': product.transport_cost,
                'other_cost': product.other_cost,
                'cogs': product.cogs,
                'profit_margin_base_seeling': product.profit_margin_base_seeling,
                'profit_margin_mrp': product.profit_margin_mrp,
                'base_selling_price': product.base_selling_price,
                'mrp': product.mrp,
                'opening_stock': product.opening_stock,
                'inventory_location': product.inventory_location,
                'weight': product.weight,
                'position': product.position,
                'rack': product.rack,
                'row': product.row,
                'image': str(product.image),  # Convert ImageField to string
                'product_description': product.product_description,
                'instruction': product.instruction,
                'custom_field_1': product.custom_field_1,
                'custom_field_2': product.custom_field_2,
                'custom_field_3': product.custom_field_3,
                'selling': product.selling,
            }
            return JsonResponse({'product_data': product_data})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

@csrf_exempt
def save_invoice(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            status = data.get('status', 'draft')  # Default to 'draft' if status is not provided

            # Validate required fields
            if not customer_id or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)

            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

            # Create SetPos instance and save
            set_pos_instance = SetPos.objects.create(
                customer=customer,
                discount=discount_value,
                total_subtotal=total_subtotal,
                total_with_discount=total_with_discount,
                status=status,
                invoice_by=request.user.username
            )

            set_pos_instance.products.set(products)
            set_pos_id = set_pos_instance

          
            
            # Generate PDF for product details including customer details
            if status == "draft":
                status = "Draft Invoice"
            elif status == "credit_sale":
                status = "Credit Sale Invoice"
            elif status == "quatation":
                status = "Quatation Invoice"
            elif status == "cash":
                status = "Cash Invoice"

            product_pdf_content = generate_product_pdf(customer, products, set_pos_id, discount_value, total_subtotal,
                                                       total_with_discount, status)


            account = Account.objects.create(invoice_id_view=set_pos_instance, invoice_sale_now=total_with_discount)
            account.save()

            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_instance.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Update total_sale in the Account model
            

            # Open the PDF file
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)


class Salecancel_view(View):
    def get(self, request):
        pass

@csrf_exempt
def generate_invoice_pdf(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            posid = data.get('posid')
            
            set_pos_instannce = SetPos.objects.get(id=posid)

            # Validate required fields
            if not customer_id  or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)
                
            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

           

            # Create SetPos instance and save
            
            set_pos_instance = set_pos_instannce
            status = set_pos_instance.status
            set_pos_id = set_pos_instance
            # Generate PDF for product details including customer details
            if(status == "draft"):
                status = "Draft Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "credit_sale"):
                status = "Credit Sale Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "quatation"):
                status = "Quatation Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "cash"):
                status = "Cash Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)

                
                
            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_id.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)


@csrf_exempt
def generate_return_invoice_pdf(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            posid = data.get('posid')
            
            set_pos_instannce = SetPosCancelation.objects.get(id=posid)

            # Validate required fields
            if not customer_id  or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)
                
            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

           

            # Create SetPos instance and save
            
            set_pos_instance = set_pos_instannce
            status = set_pos_instance.status
            set_pos_id = set_pos_instance
            # Generate PDF for product details including customer details
            if(status == "draft"):
                status = "Draft Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "credit_sale"):
                status = "Credit Sale Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "quatation"):
                status = "Quatation Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)
            elif(status == "cash"):
                status = "Cash Invoice"
                product_pdf_content = generate_product_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status)

            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_id.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)


def generate_product_pdf(customer, products, set_pos_id, discount_value, total_subtotal, total_with_discount, status):
    # Prepare data for the PDF template
    total_with_discount = float(total_with_discount)
    total_subtotal = float(total_subtotal)
    context = {
        'customer': customer,
        'set_pos_id': set_pos_id,
        'products': products,
        'total_subtotal': total_subtotal,
        'total_with_discount': total_with_discount,
        'status' : status
    }

    # Initialize product_pdf_content with an empty value
    product_pdf_content = b''

    # Include discount_value in the context if it is not None
    if discount_value is not None:
        context['discount_value'] = discount_value

        # Render the PDF template and get the PDF content
        product_pdf_content = render_to_pdf('ERP/invoicecredit.html', context).content

    return product_pdf_content

def render_to_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)

    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()

    # Create the PDF object using the BytesIO buffer as its "file."
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), buffer, link_callback=link_callback)

    # Check if the PDF generation was successful
    if not pdf.err:
        # If the PDF generation was successful, return the response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response

    # If the PDF generation failed, return an error response
    return HttpResponse('PDF generation failed', status=500)


class TransactionView(View):
    template_name = 'ERP/alltransaction.html'
    items_per_page = 10  # Set the default number of items per page

    def get(self, request):
        # Get the value of the 'status' parameter from the URL
        status_filter = request.GET.get('status', 'draft')  # Set default value to 'draft'
        form = VoucherForm()  # Create an instance of VoucherForm

        # Get the value of the 'items_per_page' parameter from the URL
        items_per_page = request.GET.get('items_per_page', self.items_per_page)

        # Filter SetPos objects based on the status parameter
        if status_filter:
            setpos = SetPos.objects.filter(status=status_filter)
        else:
            # If no status parameter provided, show all transactions
            setpos = SetPos.objects.all()

        # Pagination
        paginator = Paginator(setpos, items_per_page)
        page = request.GET.get('page', 1)

        try:
            setpos_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            setpos_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g., 9999), deliver the last page
            setpos_page = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'pos_page': setpos_page, 'status_filter': status_filter, 'items_per_page': int(items_per_page), 'form': form})

    def post(self, request):
        form = VoucherForm(request.POST)
        if form.is_valid():
            # Save the form data to the Voucher model
            form.instance.type = 'Receive'

            # Save the form data to the Voucher model
            voucher = form.save()

            # Get the associated salepos
            salepos = voucher.salepos

            # Update SetPos data using Decimal values
            salepos.paid_amount += float(voucher.amount)
            salepos.due_amount = float(salepos.total_with_discount) - float(salepos.paid_amount)
            salepos.save()

            # You might want to do additional processing or redirect to another page
            # Replace 'success_page' with the URL name or path you want to redirect to
            return redirect(f'http://127.0.0.1:8000/transaction/?status={salepos.status}')
                # You might want to do additional processing or redirect to another page

            # If the form is not valid, render the template with the form and other data
        return render(request, self.template_name, {'form': form, 'status_filter': 'draft'})


class EditInvoiceView(View):
    def get(self, request):
        try:
            # Get JSON data from the query parameters
            data = json.loads(request.GET.get('allRowsData', '[]'))
            status = request.GET.get('status', None)

            # Prepare context for the template
            context = {
                'allRowsData': data,
                'status': status,
            }

            # Render the template with the context data
            return render(request, 'ERP/editInvoice.html', context)

        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



class EditRetunView(View):
    def get(self, request):
        try:
            # Get JSON data from the query parameters
            data = json.loads(request.GET.get('allRowsData', '[]'))
            status = request.GET.get('status', None)
            # Prepare context for the template
            context = {
                'allRowsData': data,
                'status': status,
            }
            # Render the template with the context data
            return render(request, 'ERP/returnInvoice.html', context)

        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class NewOrderSheet(View):
    def get(self, request):
        return render(request, 'ERP/ordersheetlist.html')



@csrf_exempt
def update_save_invoice(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            posid = data.get('posid')
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            status = data.get('status', 'draft')  # Default to 'draft' if status is not provided

            # Validate required fields
            if not posid or not customer_id or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)

            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Check if an existing SetPos instance matches the criteria for update
            existing_set_pos_instance = SetPos.objects.filter(id=posid).first()
            
            if existing_set_pos_instance:
                # Update the existing SetPos instance
                existing_set_pos_instance.discount = discount_value
                existing_set_pos_instance.total_subtotal = total_subtotal
                existing_set_pos_instance.total_with_discount = total_with_discount
                existing_set_pos_instance.save()
                set_pos_instance = existing_set_pos_instance
            else:
                # Create a new SetPos instance
                set_pos_instance = SetPos.objects.create(
                    id=posid,
                    customer=customer,
                    discount=discount_value,
                    total_subtotal=total_subtotal,
                    total_with_discount=total_with_discount,
                    status=status,
                    invoice_by=request.user.username
                )

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

            # Set the products for the SetPos instance
            set_pos_instance.products.set(products)
            set_pos_id = set_pos_instance

            # Generate PDF for product details including customer details
            if status == "draft":
                status = "Draft Invoice"
            elif status == "credit_sale":
                status = "Credit Sale Invoice"
            elif status == "quatation":
                status = "Quatation Invoice"
            elif status == "cash":
                status = "Cash Invoice"

            product_pdf_content = generate_product_pdf(customer, products, set_pos_id, discount_value,
                                                       total_subtotal, total_with_discount, status)

            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_instance.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)



@csrf_exempt
def return_save_invoice(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            posid = data.get('posid')
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            status = data.get('status', 'draft')  # Default to 'draft' if status is not provided

            # Validate required fields
            if not posid or not customer_id or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)

            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)
            
            # Create a new SetPosCancelation instance
            set_pos_cancel_instance = SetPosCancelation.objects.create(
                customer=customer,
                discount=discount_value,
                total_subtotal=total_subtotal,
                total_with_discount=total_with_discount,
                status=status,
                invoice_by=request.user.username
                # You may need to adjust other fields here based on your model requirements
            )

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

            # Set the products for the SetPosCancelation instance
            set_pos_cancel_instance.products.set(products)

            # Generate PDF for product details including customer details
            if status == "draft":
                status = "Draft Invoice"
            elif status == "credit_sale":
                status = "Credit Sale Invoice"
            elif status == "quotation":
                status = "Quotation Invoice"
            elif status == "cash":
                status = "Cash Invoice"

            product_pdf_content = generate_product_pdf(customer, products, set_pos_cancel_instance.id, discount_value,
                                                       total_subtotal, total_with_discount, status)

            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_cancel_instance.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)



class ProductDetailsNameView(View):
    def get(self, request, name):
        try:
            product = Product.objects.get(name=name)
            product_data = {
            
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'uom': product.uom,
                'vendor': product.vendor,
                'brand': product.brand,
                'category': product.category,
                'sub_category': product.sub_category,
                'product_type': product.product_type,
                'variation_name': product.variation_name,
                'variation_values': product.variation_values,
                'barcode_type': product.barcode_type,
                'alert_quantity': product.alert_quantity,
                'lead_time': product.lead_time,
                'reorder_quantity': product.reorder_quantity,
                'reorder_date': product.reorder_date,
                'expires_in': product.expires_in,
                'tax': product.tax,
                'purchase_price': product.purchase_price,
                'transport_cost': product.transport_cost,
                'other_cost': product.other_cost,
                'cogs': product.cogs,
                'profit_margin_base_seeling': product.profit_margin_base_seeling,
                'profit_margin_mrp': product.profit_margin_mrp,
                'base_selling_price': product.base_selling_price,
                'mrp': product.mrp,
                'opening_stock': product.opening_stock,
                'inventory_location': product.inventory_location,
                'weight': product.weight,
                'position': product.position,
                'rack': product.rack,
                'row': product.row,
                'image': str(product.image),  # Convert ImageField to string
                'product_description': product.product_description,
                'instruction': product.instruction,
                'custom_field_1': product.custom_field_1,
                'custom_field_2': product.custom_field_2,
                'custom_field_3': product.custom_field_3,
                'selling': product.selling,
            }
            return JsonResponse({'product_data': product_data})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def get_customer_data(request):
    # Assuming you have a model named Customer and you want to fetch data based on customerid
    customer_id = request.GET.get('customerid')

    try:
        # Your logic to fetch customer data based on customerid
        customer_data = CustomerList.objects.get(id=customer_id)
        data = {
            'customer_id': customer_data.id,
            'customer_name': customer_data.Debtors_Name,
            'customer_phone': customer_data.Phone,
            # Add more fields as needed
        }
        return JsonResponse({'customer_data': data})
    except CustomerList.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class PartyListView(View):
    def get(self, request):
        party_list_data = list(PartyList.objects.values('id', 'Party_Name', 'Phone', 'Address'))
        return JsonResponse({'party_list_data': party_list_data})



class NewPurchase(View):
    def get(self, request):
        partyform = PartyListForm()
        return render(request, 'ERP/new_purchase_add.html', {'partyform': partyform})

    def post(self, request):
        partyform = PartyListForm(request.POST)
        if partyform.is_valid():
            partyform = partyform.save()
            messages.success(request, 'Vendor saved successfully!')
            return redirect('new_purchase_list')  # Replace 'your_redirect_view_name' with the actual name or URL of the view you want to redirect to
        else:
            messages.error(request, 'Error saving vendor. Please check the form.')
        return render(request, 'ERP/new_purchase_add.html', {'partyform': partyform})


@csrf_exempt
def save_invoice_purchase(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            description = data.get('description')
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            status = data.get('status', 'quatation')  # Default to 'draft' if status is not provided

            # Validate required fields
            if not customer_id  or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)
                
            # Save customer details
            try:
                customer = PartyList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

           

            # Create SetPos instance and save
            set_pos_instance = SetPosPurchase.objects.create(
                party=customer,
                discount=discount_value,
                total_subtotal=total_subtotal,
                total_with_discount=total_with_discount,
                status=status,
                delivery_status = "Pending",
                description = description,
                invoice_by = request.user.username
            )
            
            set_pos_instance.products.set(products)
            set_pos_id = set_pos_instance
            # Generate PDF for product details including customer details


            
            if(status == "quatation"):
                status = "QUATATION"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)
            elif(status == "purchase"):
                status = "PURCHASE"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)

                
              
            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_instance.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)




def generate_purchase_pdf(customer, products, set_pos_id, discount_value, total_subtotal, total_with_discount, status, description):
    # Prepare data for the PDF template
    total_with_discount = float(total_with_discount)
    total_subtotal = float(total_subtotal)
    context = {
        'party': customer,
        'set_pos_id': set_pos_id,
        'products': products,
        'total_subtotal': total_subtotal,
        'total_with_discount': total_with_discount,
        'status' : status,
        'description' : description
    }

    # Initialize product_pdf_content with an empty value
    product_pdf_content = b''

    # Include discount_value in the context if it is not None
    if discount_value is not None:
        context['discount_value'] = discount_value

        # Render the PDF template and get the PDF content
        product_pdf_content =  render_to_pdf_ivoice('ERP/invoicepurchase.html', context).content

    return product_pdf_content

def render_to_pdf_ivoice(template_path, context):
    template = get_template(template_path)
    html = template.render(context)

    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()

    # Create the PDF object using the BytesIO buffer as its "file."
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), buffer, link_callback=link_callback)

    # Check if the PDF generation was successful
    if not pdf.err:
        # If the PDF generation was successful, return the response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response

    # If the PDF generation failed, return an error response
    return HttpResponse('PDF generation failed', status=500)


class PurchaseListView(View):
    template_name = 'ERP/showpurchaselist.html'
    default_items_per_page = 10  # Set the default number of items per page

    def get(self, request):
        # Get the value of the 'status' parameter from the URL
        status_filter = request.GET.get('status', 'Pending')

        # Get the selected number of items per page from the URL
        items_per_page = int(request.GET.get('items_per_page', self.default_items_per_page))

        setpos_purchase = SetPosPurchase.objects.all()

        # Pagination
        paginator = Paginator(setpos_purchase, items_per_page)
        page = request.GET.get('page', 1)

        try:
            setpos_purchase_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            setpos_purchase_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g., 9999), deliver the last page
            setpos_purchase_page = paginator.page(paginator.num_pages)

        # Create an instance of the VoucherForm
        form = VoucherForm()

        return render(request, self.template_name, {'pos_page': setpos_purchase_page, 'status_filter': status_filter, 'items_per_page': items_per_page, 'form': form})

    def post(self, request):
        form = VoucherForm(request.POST)
        if form.is_valid():
            # Save the form data to the Voucher model
            form.instance.type = 'Receive'
            # Save the form data to the Voucher model
            voucher = form.save()
            # Get the associated purchasepos
            purchasepos = voucher.purchasepos

            # Update SetPosPurchase data using Decimal values
            purchasepos.paid_amount += float(voucher.amount)
            purchasepos.due_amount = float(purchasepos.total_with_discount) - float(purchasepos.paid_amount)
            purchasepos.save()

            # You might want to do additional processing or redirect to another page
            # Replace 'success_page' with the URL name or path you want to redirect to
            return redirect(f'http://127.0.0.1:8000/purchaselist/?status={purchasepos.status}')

        # If the form is not valid, render the template with the form and other data
        return render(request, self.template_name, {'form': form, 'status_filter': 'Pending'})


@csrf_exempt  # Use this decorator for simplicity. In production, implement proper CSRF protection.
def update_delivery_status(request):
    if request.method == 'POST':
        pos_id = request.POST.get('posId')
        selected_status = request.POST.get('selectedStatus')

        try:
            # Retrieve the SetPosPurchase instance
            pos_purchase = SetPosPurchase.objects.get(id=pos_id)
            
            # Update the delivery_status
            pos_purchase.delivery_status = selected_status
            pos_purchase.save()

            # Return a JSON response indicating success
            return JsonResponse({'message': 'Database updated successfully'})
        except SetPosPurchase.DoesNotExist:
            return JsonResponse({'error': 'SetPosPurchase with the specified ID does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error updating database: {str(e)}'}, status=500)

    # Return an error response if the request is not a POST
    return JsonResponse({'error': 'Invalid request method'})



@csrf_exempt
def generate_invoice_pdf_purchase(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            description = data.get('description') 
            posid = data.get('posid')

            
            
            set_pos_instannce = SetPosPurchase.objects.get(id=posid)

            # Validate required fields
            if not customer_id  or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)
                
            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

           

            # Create SetPos instance and save
            
            set_pos_instance = set_pos_instannce
            status = set_pos_instance.status
            set_pos_id = set_pos_instance
            # Generate PDF for product details including customer details
            if(status == "quatation"):
                status = "Quatation"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)
            elif(status == "purchase"):
                status = "Purchase"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)
            
                
                
            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_id.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)



class EditInvoicePurchaseView(View):
    def get(self, request):
        try:
            # Get JSON data from the query parameters
            data = json.loads(request.GET.get('allRowsData', '[]'))
            status = request.GET.get('status', None)

            # Prepare context for the template
            context = {
                'allRowsData': data,
                'status': status,
            }

            # Render the template with the context data
            return render(request, 'ERP/neweditinvoicepurchase.html', context)

        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        


@csrf_exempt
def update_save_invoice_purchase(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            posid = data.get('posid')
            customer_id = data.get('customerId')
            discount_value = data.get('discountValue', None)
            products_array = data.get('productsArray')
            total_subtotal = data.get('totalSubtotal')
            total_with_discount = data.get('totalWithDiscount')
            status = data.get('status', 'quatation')  # Default to 'draft' if status is not provided

            # Validate required fields
            if not posid or not customer_id or not products_array or not total_subtotal or not total_with_discount:
                return JsonResponse({'message': 'Incomplete data in the request'}, status=400)

            # Save customer details
            try:
                customer = CustomerList.objects.get(id=customer_id)
            except ObjectDoesNotExist:
                return JsonResponse({'message': 'Customer does not exist'}, status=400)

            # Check if an existing SetPos instance matches the criteria for update
            existing_set_pos_instance = SetPosPurchase.objects.filter(id=posid).first()
            description = existing_set_pos_instance.description
            if existing_set_pos_instance:
                # Update the existing SetPos instance
                existing_set_pos_instance.discount = discount_value
                existing_set_pos_instance.total_subtotal = total_subtotal
                existing_set_pos_instance.total_with_discount = total_with_discount
                existing_set_pos_instance.save()
                set_pos_instance = existing_set_pos_instance
            else:
                # Create a new SetPos instance
                set_pos_instance = SetPosPurchase.objects.create(
                    id=posid,
                    customer=customer,
                    discount=discount_value,
                    total_subtotal=total_subtotal,
                    total_with_discount=total_with_discount,
                    status=status,
                    invoice_by=request.user.username
                )

            # Save products without enforcing uniqueness
            products = []
            for product_data in products_array:
                product = InvoiceProduct.objects.create(**product_data)
                products.append(product)

            # Set the products for the SetPos instance
            set_pos_instance.products.set(products)
            set_pos_id = set_pos_instance

            # Generate PDF for product details including customer details
            if(status == "quatation"):
                status = "Quatation"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)
            elif(status == "purchase"):
                status = "Purchase"
                product_pdf_content = generate_purchase_pdf(customer, products,set_pos_id, discount_value, total_subtotal, total_with_discount, status, description)
            

            # Save the PDF file
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'product_details_{set_pos_instance.id}.pdf')
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(product_pdf_content)

            # Open the PDF file
            subprocess.run(['start', '', pdf_path], shell=True)

            # Include a success message and PDF URL in the JSON response
            return JsonResponse({'message': 'Data saved successfully', 'pdf_url': pdf_path})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)


@require_POST
def delete_pos_purchase(request):
    pos_id = request.POST.get('posId')

    try:
        pos_instance = SetPosPurchase.objects.get(id=pos_id)
        pos_instance.delete()
        response_data = {'message': 'Record deleted successfully'}
        return JsonResponse(response_data, status=200)
    except SetPosPurchase.DoesNotExist:
        response_data = {'message': 'Record not found'}
        return JsonResponse(response_data, status=404)
    except Exception as e:
        response_data = {'message': str(e)}
        return JsonResponse(response_data, status=500)


@require_POST
def delete_invoice_transaction(request):
    try:
        pos_id = request.POST.get('posId')
        pos_instance = SetPos.objects.get(id=pos_id)

        # Create an instance of SetPosCancelation and copy data
        with transaction.atomic():
            cancel_instance = SetPosCancelation(
                customer=pos_instance.customer,
                discount=pos_instance.discount,
                total_subtotal=pos_instance.total_subtotal,
                total_with_discount=pos_instance.total_with_discount,
                paid_amount=pos_instance.paid_amount,
                due_amount=pos_instance.due_amount,
                status=pos_instance.status,
                order_sheet=pos_instance.order_sheet,
                invoice_date=pos_instance.invoice_date,
                delivery_date=pos_instance.delivery_date,
                delivery_status=pos_instance.delivery_status,
                invoice_by=pos_instance.invoice_by,
                systemname=pos_instance.systemname,
            )
            cancel_instance.save()

            # Add the products to the cancel_instance
            cancel_instance.products.set(pos_instance.products.all())

        # Now you can delete the original SetPos instance
        pos_instance.delete()

        response_data = {'message': 'Record deleted and saved successfully'}
        return JsonResponse(response_data, status=200)
    
    except SetPos.DoesNotExist:
        response_data = {'message': 'Record not found'}
        return JsonResponse(response_data, status=404)
    
    except Exception as e:
        response_data = {'message': str(e)}
        return JsonResponse(response_data, status=500)



@require_POST
def delete_invoice_transacrtion_cancel(request):
    try:
        pos_id = request.POST.get('posId')
        pos_instance = SetPosCancelation.objects.get(id=pos_id)
        pos_instance.delete()
        response_data = {'message': 'Record deleted and saved successfully'}
        return JsonResponse(response_data, status=200)
    
    except SetPosCancelation.DoesNotExist:
        response_data = {'message': 'Record not found'}
        return JsonResponse(response_data, status=404)
    
    except Exception as e:
        response_data = {'message': str(e)}
        return JsonResponse(response_data, status=500)



def create_or_update_customer(request, customer_id=None):
    if customer_id:
        customer = CustomerList.objects.get(id=customer_id)
    else:
        customer = CustomerList()

    if request.method == 'POST':
        form = CustomerListForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')  # Replace 'customer_list' with the actual URL name for your customer list view
    else:
        form = CustomerListForm(instance=customer)

    return render(request, 'ERP/customeradd.html', {'form': form, 'customer': customer})


def customer_list(request):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    customers = CustomerList.objects.all()

    paginator = Paginator(customers, items_per_page)
    page = request.GET.get('page')

    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        customers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        customers = paginator.page(paginator.num_pages)

    return render(request, 'ERP/customer_list.html', {'customers': customers, 'items_per_page': items_per_page})


def delete_customer(request, customer_id):
    # Retrieve the customer instance
    customer = get_object_or_404(CustomerList, id=customer_id)
    
    customer.delete()
    # Add a success message
    messages.success(request, f"{customer.Debtors_Name} has been successfully deleted.")
    # Redirect to the customer list page after deletion
    return redirect('customer_list')



def create_or_update_party(request, party_id=None):
    if party_id:
        party = get_object_or_404(PartyList, id=party_id)
    else:
        party = PartyList()
    if request.method == 'POST':
        form = PartyListForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            return redirect('party_list')
    else:
        form = PartyListForm(instance=party)

    return render(request, 'ERP/partylistadd.html', {'form': form, 'party': party})



def party_list(request):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    party = PartyList.objects.all()

    paginator = Paginator(party, items_per_page)
    page = request.GET.get('page')

    try:
        party = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        party = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        party = paginator.page(paginator.num_pages)

    return render(request, 'ERP/party_list.html', {'party': party, 'items_per_page': items_per_page})


def delete_party(request, party_id):
    party = get_object_or_404(PartyList, id=party_id)
    party.delete()
    return redirect('party_list')

    











def create_or_update_product(request, product_id=None):
    if product_id:
        product = get_object_or_404(Product, id=product_id)
    else:
        product = Product()

    if request.method == 'POST':
        form = ProductUpdateForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'ERP/productlistadd.html', {'form': form, 'product': product})


def product_list(request):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    product = Product.objects.all()

    paginator = Paginator(product, items_per_page)
    page = request.GET.get('page')

    try:
        product = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        product = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        product = paginator.page(paginator.num_pages)
    return render(request, 'ERP/product_list.html', {'products': product, 'items_per_page': items_per_page})


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('product_list')



def create_or_update_employee(request, employee_id=None):
    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
    else:
        employee = Employee()
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'ERP/employeelistadd.html', {'form': form, 'employee': employee})


def employee_list(request):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    employee = Employee.objects.all()
    
    paginator = Paginator(employee, items_per_page)
    page = request.GET.get('page')

    try:
        employee = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        employee = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        employee = paginator.page(paginator.num_pages)
    return render(request, 'ERP/employee_list.html', {'employees': employee, 'items_per_page': items_per_page})


def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()
    return redirect('employee_list')





def create_or_update_voucher(request, voucher_id=None):
    if voucher_id:
        voucher = get_object_or_404(Voucher, id=voucher_id)
    else:
        voucher = Voucher()
    if request.method == 'POST':
        form = VoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('voucher_list')
    else:
        form = VoucherForm(instance=voucher)
    
    return render(request, 'ERP/voucherlistadd.html', {'form': form, 'voucher': voucher})


def voucher_list(request):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    voucher = Voucher.objects.all()
    
    paginator = Paginator(voucher, items_per_page)
    page = request.GET.get('page')

    try:
        voucher = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        voucher = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        voucher = paginator.page(paginator.num_pages)
    return render(request, 'ERP/voucher_list.html', {'vouchers': voucher, 'items_per_page': items_per_page})


def delete_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    voucher.delete()
    return redirect('voucher_list')



def customer_details_account(request, customer_id):
    items_per_page = int(request.GET.get('items_per_page', 10))  # Default to 10 items per page
    customer = get_object_or_404(CustomerList, id=customer_id)
    
    # Get all POS records for the employee
    pos_list = SetPos.objects.filter(customer=customer)
    
    paginator = Paginator(pos_list, items_per_page)
    page = request.GET.get('page')  

    try:
        pos_records = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        pos_records = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results.
        pos_records = paginator.page(paginator.num_pages)
    
    return render(request, 'ERP/customer_details_account.html', {'customers': pos_list, 'pos_records': pos_records, 'items_per_page': items_per_page})



class CancelTransactionView(View):
    template_name = 'ERP/allcancelinvoice.html'
    items_per_page = 10  # Set the default number of items per page

    def get(self, request):
        # Get the value of the 'status' parameter from the URL
        status_filter = request.GET.get('status', 'draft')  # Set default value to 'draft'
        # Get the value of the 'items_per_page' parameter from the URL
        items_per_page = request.GET.get('items_per_page', self.items_per_page)
        # Filter SetPos objects based on the status parameter
        if status_filter:
            setpos = SetPosCancelation.objects.filter(status=status_filter)
        else:
            # If no status parameter provided, show all transactions
            setpos = SetPosCancelation.objects.all()
        # Pagination
        paginator = Paginator(setpos, items_per_page)
        page = request.GET.get('page', 1)
        try:
            setpos_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            setpos_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g., 9999), deliver the last page
            setpos_page = paginator.page(paginator.num_pages)
        return render(request, self.template_name, {'pos_page': setpos_page, 'status_filter': status_filter, 'items_per_page': int(items_per_page)})

   


# def get_product_details(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     data = {
#         'name': product.name,
#         'sku': product.sku,
#         # Add other product details as needed
#     }
#     return JsonResponse(data)


# def generate_barcode(barcode_data, filename):
#     # Generate barcode
#     code = Code128(barcode_data, writer=ImageWriter())
#     code.save(filename)

# def generate_pdf_with_barcode(barcode_data, pdf_filename, barcode_filename):
#     # Get the absolute path to the image file using BASE_DIR
#     image_path = os.path.normpath(os.path.join(settings.BASE_DIR, barcode_filename))

#     # Create PDF
#     c = canvas.Canvas(pdf_filename, pagesize=letter)
#     width, height = letter

#     # Draw barcode on PDF
#     barcode_width = 200
#     barcode_height = 100
#     c.drawInlineImage(image_path, (width - barcode_width) / 2, height - 150, width=barcode_width, height=barcode_height)

#     # Add additional content or text if needed
#     c.drawString(100, height - 200, "Barcode Data: {}".format(barcode_data))

#     # Save PDF
#     c.save()

# def generate_barcode_view(request, product_id):
#     # Get the barcode data based on the product_id
#     # Replace the following line with your actual logic to get barcode data
#     barcode_data = f"123456789-{product_id}"

#     barcode_filename = f"barcode_{product_id}.png"
#     pdf_filename = f"output_{product_id}.pdf"

#     # Generate barcode and PDF
#     generate_barcode(barcode_data, barcode_filename)
#     generate_pdf_with_barcode(barcode_data, pdf_filename, barcode_filename)

#     # Serve the PDF file for download
#     with open(pdf_filename, 'rb') as pdf_file:
#         response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
#     return response


    

