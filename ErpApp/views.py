from django.shortcuts import render
from django.views import View
import subprocess
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import ActivityLog,CustomerList,Product, SetPos, InvoiceProduct, ItemName, PartyList, SetPosPurchase
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import link_callback
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from reportlab.lib import styles
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors



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
        return render(request, 'ERP/home.html')


class CustomerListView(View):
    def get(self, request):
        customer_data = list(CustomerList.objects.values('id', 'Debtors_Name', 'Phone', 'Address'))
        return JsonResponse({'customer_data': customer_data})

class ProductListView(View):
    def get(self, request):
        product_data = list(Product.objects.values('id','item__name', 'name', 'sku', 'mrp', 'uom'))
        return JsonResponse({'product_data': product_data})

class ItemListView(View):
    def get(self, request):
        item_data = list(ItemName.objects.values('id','name'))
        return JsonResponse({'iem-data': item_data})

class NewInvoice(View):
    def get(self, request):
        return render(request, 'ERP/new_invoice_add.html')
    

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
            set_pos_instance = SetPos.objects.create(
                customer=customer,
                discount=discount_value,
                total_subtotal=total_subtotal,
                total_with_discount=total_with_discount,
                status=status,
                invoice_by = request.user.username
            )
            
            set_pos_instance.products.set(products)
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
    items_per_page = 10  # Set the number of items per page

    def get(self, request):
        # Get the value of the 'status' parameter from the URL
        status_filter = request.GET.get('status', 'draft')  # Set default value to 'draft'

        # Filter SetPos objects based on the status parameter
        if status_filter:
            setpos = SetPos.objects.filter(status=status_filter)
        else:
            # If no status parameter provided, show all transactions
            setpos = SetPos.objects.all()

        # Pagination
        paginator = Paginator(setpos, self.items_per_page)
        page = request.GET.get('page', 1)

        try:
            setpos_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            setpos_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g., 9999), deliver the last page
            setpos_page = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'pos_page': setpos_page, 'status_filter': status_filter})



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





class ProductDetailsNameView(View):
    def get(self, request, name):
        try:
            product = Product.objects.get(name=name)
            product_data = {
                'item' : product.item.name,
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
        return render(request, 'ERP/new_purchase_add.html')
    



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
            status = data.get('status', 'draft')  # Default to 'draft' if status is not provided

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
    items_per_page = 10  # Set the number of items per page

    def get(self, request):
        # Get the value of the 'status' parameter from the URL
        
        setpos = SetPosPurchase.objects.all()

        # Pagination
        paginator = Paginator(setpos, self.items_per_page)
        page = request.GET.get('page', 1)

        try:
            setpos_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page
            setpos_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g., 9999), deliver the last page
            setpos_page = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'pos_page': setpos_page})


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

