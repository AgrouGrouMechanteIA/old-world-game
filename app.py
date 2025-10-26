from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, PlayerProfile, Place, ItemType, InventoryItem, Mail, MarketListing, Task, HarvestTimer, Property, BoatStatus, Turn
from datetime import date, datetime
import json, os, random
from config import HUNGER_MAX, HEALTH_MAX

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app

app = create_app()

# helpers
def get_current_user():
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

def money_to_shillings(p, s):
    return p*20 + s

def shillings_to_money(total):
    return divmod(total, 20)

# load narrations
with open(os.path.join(os.path.dirname(__file__),'narrations.json'),'r',encoding='utf-8') as f:
    NARR = json.load(f)

def pick_variant(collection):
    if not collection:
        return None
    keys = list(collection.keys())
    if not keys:
        return None
    tone = random.choice(keys)
    return collection[tone]

# routes
@app.route('/')
def index():
    user = get_current_user()
    places = Place.query.order_by(Place.name).all()
    return render_template('index.html', user=user, places=places)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        u = request.form['username'].strip()
        p = request.form['password']
        if not u or not p:
            flash('Provide username/password'); return redirect(url_for('register'))
        if User.query.filter_by(username=u).first():
            flash('Username taken'); return redirect(url_for('register'))
        user = User(username=u, password=p)
        db.session.add(user); db.session.commit()
        profile = PlayerProfile(user_id=user.id, pounds=0, shillings=0, hunger=0, health=HEALTH_MAX, level=1)
        bf = Place.query.filter_by(name='Beautiful Forest').first()
        if bf:
            profile.location_id = bf.id
        db.session.add(profile); db.session.commit()
        flash('Account created. Please login.'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form['username']; p = request.form['password']
        user = User.query.filter_by(username=u, password=p).first()
        if not user:
            flash('Bad credentials'); return redirect(url_for('login'))
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

@app.route('/profile')
def profile():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    prof = user.profile
    inv = InventoryItem.query.filter_by(player_id=prof.id).all()
    mails = Mail.query.filter_by(to_player=prof.id).order_by(Mail.created_at.desc()).all()
    return render_template('profile.html', user=user, profile=prof, inventory=inv, mails=mails)

@app.route('/place/<int:place_id>')
def place(place_id):
    place = Place.query.get_or_404(place_id)
    user = get_current_user()
    listings = MarketListing.query.filter_by(place_id=place_id).all()
    narr_collection = NARR.get('places_by_name', {}).get(place.name, {})
    narration = pick_variant(narr_collection)
    return render_template('place.html', place=place, user=user, listings=listings, narration=narration)

@app.route('/start_task', methods=['POST'])
def start_task():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    task_type = request.form['task_type']
    today = date.today().isoformat()
    if user.profile.last_task_turn == today:
        flash('You already started a task this turn'); return redirect(url_for('place', place_id=user.profile.location_id))
    task = Task(player_id=user.profile.id, task_type=task_type, metadata={}, turn_date=today)
    user.profile.last_task_turn = today
    db.session.add(task); db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get(task_type, {})
    action_feedback = pick_variant(action_narr_collection) or "You begin."
    flash(action_feedback)
    return redirect(url_for('place', place_id=user.profile.location_id))

@app.route('/inventory/eat', methods=['POST'])
def eat():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    inv_id = int(request.form['inventory_item_id'])
    qty = int(request.form.get('qty',1))
    inv = InventoryItem.query.get(inv_id)
    if not inv or inv.player_id != user.profile.id or inv.amount < qty:
        flash('Invalid eat'); return redirect(url_for('profile'))
    it = inv.item_type
    inv.amount -= qty
    user.profile.hunger = min(HUNGER_MAX, user.profile.hunger + it.edible_hunger * qty)
    user.profile.health = min(HEALTH_MAX, user.profile.health + it.edible_health * qty)
    db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get('eat', {})
    action_feedback = pick_variant(action_narr_collection) or "You eat."
    flash(action_feedback)
    return redirect(url_for('profile'))

@app.route('/craft', methods=['POST'])
def craft():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    recipe_key = request.form['recipe_key']
    today = date.today().isoformat()
    if user.profile.last_task_turn == today:
        flash('Already did a task this turn'); return redirect(url_for('profile'))
    task = Task(player_id=user.profile.id, task_type=f'artisanat:{recipe_key}', metadata={}, turn_date=today)
    user.profile.last_task_turn = today
    db.session.add(task); db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get(f'artisanat:{recipe_key}', {})
    action_feedback = pick_variant(action_narr_collection) or "You craft."
    flash(action_feedback)
    return redirect(url_for('profile'))

@app.route('/market/post', methods=['POST'])
def post_listing():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    item_id = int(request.form['item_type_id'])
    amount = int(request.form['amount'])
    place_id = int(request.form['place_id'])
    price_p = int(request.form.get('price_pounds',0))
    price_s = int(request.form.get('price_shillings',0))
    inv = InventoryItem.query.filter_by(player_id=user.profile.id, item_type_id=item_id).first()
    if not inv or inv.amount < amount:
        flash('Not enough items'); return redirect(url_for('place', place_id=place_id))
    inv.amount -= amount
    listing = MarketListing(seller_id=user.profile.id, place_id=place_id, item_type_id=item_id, amount=amount, price_pounds=price_p, price_shillings=price_s)
    db.session.add(listing); db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get('sell', {})
    action_feedback = pick_variant(action_narr_collection) or "You post goods."
    flash(action_feedback)
    return redirect(url_for('place', place_id=place_id))

@app.route('/market/buy/<int:listing_id>', methods=['POST'])
def buy_listing(listing_id):
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    listing = MarketListing.query.get_or_404(listing_id)
    buyer = user.profile
    total_price = money_to_shillings(listing.price_pounds, listing.price_shillings)
    buyer_money = money_to_shillings(buyer.pounds, buyer.shillings)
    if buyer_money < total_price:
        flash('Not enough money'); return redirect(url_for('place', place_id=listing.place_id))
    buyer_new = buyer_money - total_price
    buyer.pounds, buyer.shillings = shillings_to_money(buyer_new)
    seller = PlayerProfile.query.get(listing.seller_id)
    seller_money = money_to_shillings(seller.pounds, seller.shillings) + total_price
    seller.pounds, seller.shillings = shillings_to_money(seller_money)
    inv = InventoryItem.query.filter_by(player_id=buyer.id, item_type_id=listing.item_type_id).first()
    if not inv:
        inv = InventoryItem(player_id=buyer.id, item_type_id=listing.item_type_id, amount=0)
        db.session.add(inv)
    inv.amount += listing.amount
    db.session.delete(listing); db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get('buy', {})
    action_feedback = pick_variant(action_narr_collection) or "You buy."
    flash(action_feedback)
    return redirect(url_for('place', place_id=buyer.location_id))

@app.route('/mail/send', methods=['POST'])
def send_mail():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    to_player = int(request.form['to_player'])
    subj = request.form.get('subject','')
    body = request.form.get('body','')
    mail = Mail(from_player=user.profile.id, to_player=to_player, subject=subj, body=body)
    db.session.add(mail); db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get('send_letter', {})
    action_feedback = pick_variant(action_narr_collection) or "You send a letter."
    flash(action_feedback)
    return redirect(url_for('profile'))

@app.route('/found_city', methods=['POST'])
def found_city():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    place_id = int(request.form['place_id'])
    name = request.form['city_name'].strip()
    total = 25*20
    cur = money_to_shillings(user.profile.pounds, user.profile.shillings)
    if cur < total:
        flash('Not enough money to found a city (25 pounds)'); return redirect(url_for('place', place_id=place_id))
    cur -= total
    user.profile.pounds, user.profile.shillings = shillings_to_money(cur)
    place = Place.query.get_or_404(place_id)
    place.name = name
    place.is_city = True
    place.has_market = True
    place.colonisable = False
    db.session.commit()
    action_narr_collection = NARR.get('actions', {}).get('found_city', {})
    action_feedback = pick_variant(action_narr_collection) or "You found a city."
    flash(action_feedback)
    return redirect(url_for('place', place_id=place.id))

# admin utilities
@app.route('/admin/seed')
def admin_seed():
    from seed import seed_all
    seed_all()
    flash('World seeded.')
    return redirect(url_for('index'))

@app.route('/admin/process_turn_now')
def admin_process():
    from process_turn import process_new_turn
    process_new_turn()
    flash('Turn processed.')
    return redirect(url_for('index'))
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
