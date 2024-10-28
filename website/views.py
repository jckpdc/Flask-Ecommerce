from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Product, Cart, Order
from flask_login import login_required, current_user
from . import db
from intasend import APIService

views = Blueprint('views', __name__)

API_PUBLISHABLE_KEY = 'YOUR_PUBLISHABLE_KEY'
API_TOKEN = 'YOUR_API_TOKEN'

@views.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True)
    cart = Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else []
    return render_template('home.html', items=items, cart=cart)

@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity += 1
            db.session.commit()
            flash(f'Quantity of {item_exists.product.product_name} has been updated')
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of {item_exists.product.product_name} not updated')
    else:
        new_cart_item = Cart(quantity=1, product_link=item_to_add.id, customer_link=current_user.id)
        try:
            db.session.add(new_cart_item)
            db.session.commit()
            flash(f'{new_cart_item.product.product_name} added to cart')
        except Exception as e:
            print('Item not added to cart', e)
            flash(f'{new_cart_item.product.product_name} has not been added to cart')
    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.product.current_price * item.quantity for item in cart)
    return render_template('cart.html', cart=cart, amount=amount, total=amount + 200)

@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity += 1
        db.session.commit()
        amount = sum(item.product.current_price * item.quantity for item in Cart.query.filter_by(customer_link=current_user.id).all())
        return jsonify({'quantity': cart_item.quantity, 'amount': amount, 'total': amount + 200})

@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity -= 1
        db.session.commit()
        amount = sum(item.product.current_price * item.quantity for item in Cart.query.filter_by(customer_link=current_user.id).all())
        return jsonify({'quantity': cart_item.quantity, 'amount': amount, 'total': amount + 200})

@views.route('/removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()
        amount = sum(item.product.current_price * item.quantity for item in Cart.query.filter_by(customer_link=current_user.id).all())
        return jsonify({'quantity': cart_item.quantity, 'amount': amount, 'total': amount + 200})

@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id)
    if customer_cart:
        try:
            total = sum(item.product.current_price * item.quantity for item in customer_cart)
            service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
            create_order_response = service.collect.mpesa_stk_push(phone_number='YOUR_NUMBER', email=current_user.email,
                                                                   amount=total + 200, narrative='Purchase of goods')
            for item in customer_cart:
                new_order = Order(quantity=item.quantity, price=item.product.current_price,
                                  status=create_order_response['invoice']['state'].capitalize(),
                                  payment_id=create_order_response['id'],
                                  product_link=item.product_link, customer_link=item.customer_link)
                product = Product.query.get(item.product_link)
                product.in_stock -= item.quantity
                db.session.add(new_order)
                db.session.delete(item)
            db.session.commit()
            flash('Order Placed Successfully')
            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed')
            return redirect('/')
    flash('Your cart is Empty')
    return redirect('/')

@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)

@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        cart = Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else []
        return render_template('search.html', items=items, cart=cart)
    return render_template('search.html')

@views.route('/product/<int:item_id>')
def product(item_id):
    item = Product.query.get_or_404(item_id)
    return render_template('product.html', item=item)

@views.route('/3Dmodel/', methods=['GET', 'POST'])
def view_3D_model():
    return render_template('3Dmodel.html')

@views.route('/product2/<int:item_id>', methods=["GET", "POST"])
def product2(item_id):
    item = Product.query.get_or_404(item_id)
    return render_template('product2.html', item=item)

@views.route('/3Dmodel2/', methods=['GET', 'POST'])
def view_3D_model2():
    return render_template('3Dmodel2.html')

@views.route('/wishlist', methods=['GET', 'POST'])
def wishlist():
    return render_template('wishlist.html')

@views.route('/roomModel/', methods=['GET', 'POST'])
def view_roomModel():
    return render_template('roomModel.html')

