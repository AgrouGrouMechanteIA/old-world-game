from app import create_app
from models import db, Place, ItemType, BoatStatus
app = create_app()
app.app_context().push()

def seed_all():
    db.drop_all()
    db.create_all()
    # Places (Old World)
    places = [
        ('Beautiful Forest', True, True, 'Old World', 'mushrooms,chestnuts', False, 'A long stand of old trees where spongy earth hides small treasures.'),
        ('Ocean View', True, True, 'Old World', 'fish', False, 'A city perched on salt and gull-song, where nets creak like sleepy bells.'),
        ('Not-New-Eden', True, True, 'Old World', 'fruit', False, 'Orchards spill fat fruit into sun-baked baskets.'),
        ('Risible Rock', True, True, 'Old World', 'wild_herbs', False, 'Sharp stones and stubborn herbs, thriving where least expected.'),
        ('Temple Island', True, False, 'Old World', None, False, 'A small island holding a hush like folded cloth.'),
        ('Rocky Cliff', True, False, 'Tierra Firme', 'disgusting_insects', False, 'Sheer rock faces and a silence that is not peaceful.'),
        ('Las Formas', True, True, 'Tierra Firme', 'corn,bean', False, 'A market town of broad smiles and narrower coin-purses.'),
        ('Hope Island', False, False, 'Ocean', None, True, 'An open, unclaimed isle where the soil waits for hands.'),
        ('Sunny Island', False, False, 'Ocean', None, True, 'A bright spit of sand and shade, whispering of new beginnings.'),
        ('Desert Place 1', False, False, 'Tierra Firme', 'cactus', False, 'A dune under a great vigilance of sky.'),
        ('Desert Place 2', False, False, 'Tierra Firme', 'cactus', False, 'An expanse that counts its days in heat.'),
        ('Desert Place 3', False, False, 'Tierra Firme', 'cactus', False, 'A place that grinds patience thin as dust.'),
        ('Forest Place 1', False, False, 'Tierra Firme', 'banana', False, 'A hollow bright with leaves and small, stubborn fruits.'),
        ('Forest Place 2', False, False, 'Tierra Firme', 'banana', False, 'A green corridor humming with small lives.'),
        ('Forest Place 3', False, False, 'Tierra Firme', 'banana', False, 'A patch where the canopy keeps secrets.'),
        ('Lost Canoe', False, False, 'Tierra Firme', None, False, 'A skiff that remembers softer currents.'),
        ('River\'s End', False, False, 'Tierra Firme', None, False, 'Where the river unlaces itself into slower water.'),
        ('Lost Point on the Coast', False, False, 'Old World', None, False, 'A place of salt and quiet footprints.'),
        ('Scary Roads', False, False, 'Old World', 'wood', False, 'A road that prefers shadows as company.'),
        ('Nefarious Roads', False, False, 'Old World', 'meat,wood', False, 'Trails that carry the taste of pursuit.'),
    ]
    for name,is_city,has_market,region,res,colonisable,desc in places:
        p = Place(name=name, is_city=is_city, has_market=has_market, region=region, local_resource=res, colonisable=colonisable, description=desc)
        db.session.add(p)
    db.session.commit()

    # Items
    items = [
        ('wheat_bag','Bag of Wheat',0,0,'Growable by players after level 2'),
        ('flour_bag','Bag of Flour',0,0,'Milled from wheat'),
        ('bread_loaf','Bread Loaf',2,0,'Filling bread'),
        ('fish','Fish',2,0,'Sea fish'),
        ('mushrooms','Mushroom',2,0,'Forest mushroom'),
        ('chestnuts','Chestnut',2,0,'Chestnut'),
        ('wild_herbs','Wild Herb',0,0,'Used to craft potions'),
        ('fruit','Fruit',2,0,'Fresh fruit'),
        ('carrot','Carrot',1,0,'Carrot'),
        ('disgusting_insects','Disgusting Insect',1,0,'Insects'),
        ('banana','Banana',0,1,'Banana'),
        ('cactus','Cactus',1,0,'Cactus'),
        ('corn_bag','Corn Bag',2,0,'Corn bag'),
        ('bean_bag','Bean Bag',2,0,'Bean bag'),
        ('health_potion','Health Potion',0,1,'Health potion'),
    ]
    for key,name,eh,eh2,desc in items:
        it = ItemType(key=key, name=name, edible_hunger=eh, edible_health=eh2, description=desc)
        db.session.add(it)
    db.session.commit()

    # Boat route
    pl = {p.name:p.id for p in Place.query.all()}
    route = [pl.get('Beautiful Forest'), pl.get('Not-New-Eden'), pl.get('Ocean View'), pl.get('Temple Island'), pl.get('Risible Rock')]
    boat = BoatStatus(route_index=0, stuck_counter=0, route=route)
    db.session.add(boat)
    db.session.commit()

    print('Seed complete.')

if __name__ == '__main__':
    seed_all()
