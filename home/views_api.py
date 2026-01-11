from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
import razorpay
import hmac
import hashlib

from .models import Cart, CartItem, Order, OrderItem, ReturnRequest
from .serializers import (
    CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    OrderSerializer, OrderCreateSerializer
)
from products.models import Product

User = get_user_model()

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart


@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart(request):
    """Get current user's cart"""
    cart = get_or_create_cart(request)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """Add item to cart"""
    serializer = CartItemCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data.get('quantity', 1)
    size = serializer.validated_data.get('size', '')
    color = serializer.validated_data.get('color', '')
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check stock availability
    if product.quantity < quantity:
        return Response(
            {'error': f'Only {product.quantity} items available in stock'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cart = get_or_create_cart(request)
    
    # Check if item already exists in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size or None,
        color=color or None,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Update quantity if item exists
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.quantity:
            return Response(
                {'error': f'Cannot add more items. Only {product.quantity} available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.quantity = new_quantity
        cart_item.save()
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    quantity = request.data.get('quantity')
    if quantity is None:
        return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check stock availability
    if cart_item.product.quantity < quantity:
        return Response(
            {'error': f'Only {cart_item.product.quantity} items available in stock'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cart_item.quantity = quantity
    cart_item.save()
    
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    cart_item.delete()
    return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_cart(request):
    """Clear all items from cart"""
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)


# Order APIs
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_order(request):
    """Create order from cart"""
    cart = get_or_create_cart(request)
    
    if cart.items.count() == 0:
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate totals
    subtotal = Decimal(str(cart.subtotal))
    shipping_cost = Decimal(str(serializer.validated_data.get('shipping_cost', 0)))
    tax = Decimal(str(serializer.validated_data.get('tax', 0)))
    total = subtotal + shipping_cost + tax
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        status='pending',
        payment_status='pending',
        shipping_name=serializer.validated_data['shipping_name'],
        shipping_address=serializer.validated_data['shipping_address'],
        shipping_city=serializer.validated_data['shipping_city'],
        shipping_state=serializer.validated_data['shipping_state'],
        shipping_postal_code=serializer.validated_data['shipping_postal_code'],
        shipping_country=serializer.validated_data.get('shipping_country', 'India'),
        shipping_phone=serializer.validated_data.get('shipping_phone', ''),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        total=total
    )
    
    # Create order items from cart items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.name,
            product_price=cart_item.product.discounted_price,
            quantity=cart_item.quantity,
            size=cart_item.size,
            color=cart_item.color,
            subtotal=cart_item.subtotal
        )
        
        # Update product purchase count
        cart_item.product.no_of_purchase += cart_item.quantity
        cart_item.product.quantity -= cart_item.quantity
        cart_item.product.save()
    
    # Clear cart after order creation
    cart.items.all().delete()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    """Get user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, order_id):
    """Get specific order"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """Update order status (admin only or user can cancel)"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    new_status = request.data.get('status')
    if not new_status:
        return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Users can only cancel their orders
    if not request.user.is_staff and new_status != 'cancelled':
        return Response({'error': 'You can only cancel orders'}, status=status.HTTP_403_FORBIDDEN)
    
    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = new_status
    order.save()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)


# Razorpay Payment APIs
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    """Create Razorpay order for payment"""
    try:
        cart = get_or_create_cart(request)
        
        if cart.items.count() == 0:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get billing data from request
        billing_data = request.data.get('billing_data', {})
        if not billing_data:
            return Response({'error': 'Billing data is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total amount (in paise for Razorpay)
        total_amount = int(float(cart.subtotal) * 100)  # Convert to paise
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': total_amount,
            'currency': 'INR',
            'receipt': f'order_{timezone.now().timestamp()}',
            'notes': {
                'user_id': str(request.user.id),
                'order_number': f'ORD-{timezone.now().strftime("%Y%m%d")}'
            }
        })
        
        return Response({
            'razorpay_order_id': razorpay_order['id'],
            'amount': total_amount,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verify_razorpay_payment(request):
    """Verify Razorpay payment and create order"""
    try:
        payment_data = request.data
        razorpay_order_id = payment_data.get('razorpay_order_id')
        razorpay_payment_id = payment_data.get('razorpay_payment_id')
        razorpay_signature = payment_data.get('razorpay_signature')
        billing_data = payment_data.get('billing_data', {})
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'Payment data is incomplete'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify payment signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return Response({'error': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify payment with Razorpay
        payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        if payment['status'] != 'authorized' and payment['status'] != 'captured':
            return Response({'error': 'Payment not authorized'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cart
        cart = get_or_create_cart(request)
        
        if cart.items.count() == 0:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate totals
        subtotal = Decimal(str(cart.subtotal))
        shipping_cost = Decimal(str(billing_data.get('shipping_cost', 0)))
        tax = Decimal(str(billing_data.get('tax', 0)))
        total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            status='pending',
            payment_status='paid',
            shipping_name=billing_data.get('shipping_name', ''),
            shipping_address=billing_data.get('shipping_address', ''),
            shipping_city=billing_data.get('shipping_city', ''),
            shipping_state=billing_data.get('shipping_state', ''),
            shipping_postal_code=billing_data.get('shipping_postal_code', ''),
            shipping_country=billing_data.get('shipping_country', 'India'),
            shipping_phone=billing_data.get('shipping_phone', ''),
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.discounted_price,
                quantity=cart_item.quantity,
                size=cart_item.size,
                color=cart_item.color,
                subtotal=cart_item.subtotal
            )
            
            # Update product purchase count and stock
            cart_item.product.no_of_purchase += cart_item.quantity
            cart_item.product.quantity -= cart_item.quantity
            cart_item.product.save()
        
        # Clear cart after order creation
        cart.items.all().delete()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_return_request(request):
    """Create a return request for an order item"""
    try:
        from rest_framework.parsers import MultiPartParser, FormParser
        # Handle both JSON and FormData
        data = request.data
        order_id = data.get('order_id')
        order_item_id = data.get('order_item_id')
        reason = data.get('reason')
        reason_description = data.get('reason_description', '')
        return_quantity = data.get('quantity', 1)
        # Note: defect_image handling requires adding defect_image field to ReturnRequest model
        # This requires a database migration
        defect_image = request.FILES.get('defect_image', None)
        
        # Convert quantity to int (FormData sends strings)
        try:
            return_quantity = int(return_quantity)
        except (ValueError, TypeError):
            return_quantity = 1
        
        # Validate required fields
        if not all([order_id, order_item_id, reason]):
            return Response(
                {'error': 'Order ID, Order Item ID, and reason are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get order and order item
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            order_item = OrderItem.objects.get(id=order_item_id, order=order)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Order item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate order status - only delivered orders can be returned
        if order.status != 'delivered':
            return Response(
                {'error': 'Returns are only allowed for delivered orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate quantity
        if return_quantity > order_item.quantity:
            return Response(
                {'error': f'Return quantity cannot exceed ordered quantity ({order_item.quantity})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if return request already exists for this item
        existing_return = ReturnRequest.objects.filter(
            order_item=order_item,
            status__in=['pending', 'approved', 'processing']
        ).first()
        
        if existing_return:
            return Response(
                {'error': 'A return request already exists for this item'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create return request
        return_request = ReturnRequest.objects.create(
            order=order,
            order_item=order_item,
            user=request.user,
            reason=reason,
            reason_description=reason_description,
            quantity=return_quantity,
            status='pending'
        )
        
        # Update order status to 'applied_for_return'
        order.status = 'applied_for_return'
        order.save()
        
        # Send email to admin
        send_return_request_email(return_request)
        
        return Response({
            'message': 'Return request created successfully',
            'return_request': {
                'id': str(return_request.id),
                'order_number': order.order_number,
                'product_name': order_item.product_name,
                'reason': return_request.get_reason_display(),
                'status': return_request.get_status_display(),
                'created_at': return_request.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_return_requests(request):
    """Get return requests for the current user"""
    try:
        return_requests = ReturnRequest.objects.filter(
            user=request.user
        ).select_related('order', 'order_item').order_by('-created_at')
        
        requests_data = []
        for req in return_requests:
            requests_data.append({
                'id': str(req.id),
                'order_number': req.order.order_number,
                'product_name': req.order_item.product_name,
                'quantity': req.quantity,
                'reason': req.get_reason_display(),
                'reason_description': req.reason_description or '',
                'status': req.get_status_display(),
                'status_value': req.status,
                'admin_notes': req.admin_notes or '',
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        return Response({
            'return_requests': requests_data,
            'count': len(requests_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_return_request_email(return_request):
    """Send email notification to admin about return request"""
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Get admin email (you can configure this in settings)
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@vhinternaltional.com')
        
        # Prepare email context
        context = {
            'return_request': return_request,
            'order': return_request.order,
            'order_item': return_request.order_item,
            'user': return_request.user,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Render email template
        subject = f'New Return Request - Order {return_request.order.order_number}'
        message = render_to_string('home/emails/return_request_notification.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message='',  # Plain text version (optional)
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@vhinternaltional.com'),
            recipient_list=[admin_email],
            html_message=message,
            fail_silently=False,
        )
        
    except Exception as e:
        # Log error but don't fail the return request creation
        print(f"Error sending return request email: {str(e)}")

