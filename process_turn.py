from models import db, PlayerProfile, Task, Turn, InventoryItem, ItemType, BoatStatus, HarvestTimer
from app import create_app
from datetime import date
import random
from config import HUNGER_MAX, HEALTH_MAX

app = create_app()
app.app_context().push()

def money_to_shillings(p,s): return p*20+s
def shillings_to_money(t): return divmod(t,20)

def process_new_turn():
    today = date.today().isoformat()
    turn = Turn.query.filter_by(date_key=today).first()
    if turn and turn.processed:
        print('Already processed', today); return
    if not turn:
        turn = Turn(date_key=today, processed=False); db.session.add(turn); db.session.commit()

    tasks = Task.query.filter_by(turn_date=today).all()
    for t in tasks:
        profile = PlayerProfile.query.get(t.player_id)
        if not profile:
            db.session.delete(t); continue
        if t.task_type.startswith('gather_'):
            res = t.task_type.split('_',1)[1]
            if res in ('mushrooms','chestnuts'):
                qty = random.randint(2,7)
            elif res == 'wild_herbs':
                qty = random.randint(2,4)
            elif res == 'fish':
                qty = random.randint(1,3)
            elif res == 'fruit':
                qty = random.randint(0,3)
            elif res in ('banana','cactus'):
                qty = random.randint(2,15)
            elif res == 'disgusting_insects':
                qty = random.randint(1,5)
            else:
                qty = random.randint(1,4)
            itype = ItemType.query.filter_by(key=res).first()
            if itype:
                inv = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=itype.id).first()
                if not inv:
                    inv = InventoryItem(player_id=profile.id, item_type_id=itype.id, amount=0); db.session.add(inv)
                inv.amount += qty
        elif t.task_type == 'work_for_king':
            pay = random.randint(5,10)
            cur = money_to_shillings(profile.pounds, profile.shillings) + pay*20
            profile.pounds, profile.shillings = shillings_to_money(cur)
        elif t.task_type.startswith('artisanat:'):
            recipe = t.task_type.split(':',1)[1]
            if recipe == 'mill_wheat':
                src = ItemType.query.filter_by(key='wheat_bag').first()
                tgt = ItemType.query.filter_by(key='flour_bag').first()
                inv = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=src.id).first()
                if inv and inv.amount >= 1:
                    inv.amount -= 1
                    tti = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=tgt.id).first()
                    if not tti:
                        tti = InventoryItem(player_id=profile.id, item_type_id=tgt.id, amount=0); db.session.add(tti)
                    tti.amount += 1
            elif recipe == 'bake_bread':
                src = ItemType.query.filter_by(key='flour_bag').first()
                tgt = ItemType.query.filter_by(key='bread_loaf').first()
                inv = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=src.id).first()
                if inv and inv.amount >= 1:
                    inv.amount -= 1
                    tti = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=tgt.id).first()
                    if not tti:
                        tti = InventoryItem(player_id=profile.id, item_type_id=tgt.id, amount=0); db.session.add(tti)
                    tti.amount += 2
            elif recipe == 'herbs_to_potion':
                src = ItemType.query.filter_by(key='wild_herbs').first()
                tgt = ItemType.query.filter_by(key='health_potion').first()
                inv = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=src.id).first()
                if inv and inv.amount >= 10:
                    inv.amount -= 10
                    tti = InventoryItem.query.filter_by(player_id=profile.id, item_type_id=tgt.id).first()
                    if not tti:
                        tti = InventoryItem(player_id=profile.id, item_type_id=tgt.id, amount=0); db.session.add(tti)
                    tti.amount += 1
        elif t.task_type.startswith('pray'):
            if ':' in t.task_type:
                parts = t.task_type.split(':',1)
                if parts[0]=='pray_for':
                    try:
                        target_id = int(parts[1])
                        target = PlayerProfile.query.get(target_id)
                        if target and random.random() < 1/3:
                            target.health = min(HEALTH_MAX, target.health + 1)
                    except:
                        pass
            else:
                if random.random() < 1/3:
                    profile.health = min(HEALTH_MAX, profile.health + 1)
        db.session.delete(t)

    # process HarvestTimers (simplified)
    hts = HarvestTimer.query.filter_by(done=False).all()
    for h in hts:
        if random.random() < 0.5:
            owner = PlayerProfile.query.get(h.owner_id)
            if owner:
                itype = ItemType.query.filter_by(key=h.item_type_key).first()
                if itype:
                    inv = InventoryItem.query.filter_by(player_id=owner.id, item_type_id=itype.id).first()
                    if not inv:
                        inv = InventoryItem(player_id=owner.id, item_type_id=itype.id, amount=0); db.session.add(inv)
                    qty = random.randint(h.amount_min, h.amount_max)
                    inv.amount += qty
            h.done = True

    # hunger penalty
    profiles = PlayerProfile.query.all()
    for p in profiles:
        if p.hunger == 0:
            p.health = max(0, p.health - 1)

    # boat movement
    boat = BoatStatus.query.first()
    if boat and boat.route:
        if boat.stuck_counter > 0:
            boat.stuck_counter -= 1
        else:
            boat.route_index = (boat.route_index + 1) % len(boat.route)
            if random.random() < 0.5:
                boat.stuck_counter = 2

    turn.processed = True
    db.session.commit()
    print('Processed turn', today)

if __name__ == '__main__':
    process_new_turn()
