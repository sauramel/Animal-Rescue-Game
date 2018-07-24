from game_functions import *
import random
import socket
import pickle
import zlib
import time

#   N   #
# W # E #
#   S   #

class Map:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self.num_locations = size_x * size_y
        self.locations = []
        for y in range(size_y):
            for x in range(size_x):
                self.locations.append(Location(x, y, map=self))
    def __hash__(self):
        return hash(
            "".join([x.name for x in self.locations])
        )
    def location_at_coords(self, x, y):
        return self.locations[Map.xy_to_index(x, y, self.size_x)]
    def xy_to_index(x, y, size_x):
        return y * size_x + x
    def print_map(self, x, y):
        empty_row = "O"*self.size_x
        for row in range(self.size_y):
            if y == row:
                print("O"*x+"X"+"O"*(self.size_x-x-1))
            else:
                print(empty_row)

class Location: #dfgidfjg
    def __init__(self, x=None, y=None, map=None):
        self.x = x
        self.y = y
        self.name = Location.generate_name()
        self.map = map
        if random.randint(1,10) > 6:
            self.shop = Shop()
        else:
            self.shop = None
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.name)
    def getCoords(self):
        return self.x, self.y
    def getRandomLine(name):
        with open(name) as file:
            lines = file.read().splitlines()
        return random.choice(lines)
    def generate_name():
        adjective = Location.getRandomLine('wordlists/adjectives.txt')
        biome = Location.getRandomLine('wordlists/biomes.txt')
        return adjective.capitalize() + " " + biome.capitalize()
    def print_map(self):
        self.map.print_map(self.x, self.y)
    def canMove(self, direction):
        if direction == "up":
            return self.y > 0
        if direction == "down":
            return self.y < self.map.size_y - 1
        if direction == "left":
            return self.x > 0
        if direction == "right":
            return self.x < self.map.size_x - 1

class Item:
    def __init__(self):
        self.name  = Item.generate_name()
        self.dmod  = random.randint(2,30)
        self.price = random.randint(1,20) * self.dmod
    '''def re_init(self, name, dmod, price):
        self.name = name
        self.dmod = dmod
        self.price = price'''
    def __hash__(self):
        return hash(self.name + str(self.dmod) + str(self.price))
    def getRandomLine(name):
        with open(name) as file:
            lines = file.read().splitlines()
        return random.choice(lines)
    def generate_name():
        weaponprefix = Location.getRandomLine('wordlists/weaponprefix.txt')
        weapon = Location.getRandomLine('wordlists/weapon.txt')
        return weaponprefix.capitalize() + " " + weapon.capitalize()

class Shop:
    def __init__(self, name="Ye Olde Shoppe"):
        self.name = Shop.generate_name()
        self.items = Shop.generate_items()
    def print_wares(self):
        print("0: Leave shop\n")
        for i,item in enumerate(self.items): #0-indexed displayed as 1-indexed
            print("{}: +{} {} - {}g".format(i+1,item.dmod, item.name, item.price))
    def generate_items():
        return [Item() for i in range(random.randint(4,9))]
    def try_buyitem(self, item_id, player):
        item_id -= 1 # Fix back to 0-indexed array
        item = self.items[item_id]
        if player.p_gold < item.price:
            print("You cannot afford the {}! (price: {}, you have: {})".format(item.name, item.price, player.p_gold))
            return
        print('Are you sure you want to buy', item.name, 'for', item.price, 'gold?')
        if player.item:
            print("Warning: This will remove your {}".format(player.item.name))
        confirm = input(": ").lower()
        if confirm[0] in ["y", "1"]:
            player.p_gold -= item.price
            player.setitem(item)
            print("Succ essfully purchased {}".format(item.name))
            print("You have {} gold remaining.".format(player.p_gold))
    def getRandomLine(name):
        with open(name) as file:
            lines = file.read().splitlines()
        return random.choice(lines)
    def generate_name():
        shopprefix = Location.getRandomLine('wordlists/shopprefix.txt')
        shoptype = Location.getRandomLine('wordlists/shoptype.txt')
        return shopprefix.capitalize() + "'s " + shoptype.capitalize()

class DataPacket:
    def __init__(self, type, data):
        self.type = type
        self.data = data

class Player:
    def __init__(self, name="BUGGED", location=None, stats_entry=None, p_health=500):
        if stats_entry:
            (self.p_stre, self.p_accu, self.p_agil,
            self.cheater, self.name) = stats_entry
        else:
            self.p_stre   = 0
            self.p_accu   = 0
            self.p_agil   = 0
            self.cheater  = 0
            self.name     = name

        self.p_dbonus = 0
        self.p_gold   = 0
        self.p_health = p_health
        self.p_exp = 0
        self.p_level = 0
        self.location = location
        self.item = None
    def __hash__(self):
        return hash(
            "".join([str(hash(str(x))) for x in self.get_stats]) + \
            self.name + str(self.cheater) + str(hash(self.location)) + \
            str(hash(self.item))
        )
    def trymove(self, direction):
        x, y = self.location.getCoords()
        direction = direction.lower()
        if direction in [  "n", "north",   "up",  "u"] and self.location.canMove("up"):
            self.location = self.location.map.location_at_coords(x,   y-1)
        elif direction in ["e", "east",  "right", "r"] and self.location.canMove("right"):
            self.location = self.location.map.location_at_coords(x+1, y  )
        elif direction in ["s", "south", "down",  "d"] and self.location.canMove("down"):
            self.location = self.location.map.location_at_coords(x,   y+1)
        elif direction in ["w", "west",  "left",  "l"] and self.location.canMove("left"):
            self.location = self.location.map.location_at_coords(x-1, y  )
        else:
            print('Trying to move to a location that does not exist')
        print('\n')
    def setitem(self, item):
        self.item = item
        self.p_dbonus = item.dmod
    def get_stats(self):
        return [self.p_stre, self.p_accu, self.p_agil, self.p_health]
    def get_datapacket(self):
        data = [self.name, self.get_stats(), self.location, self.item, self.p_gold, self.cheater]
        return DataPacket("PDATA", data)

class Encounter:
    def __init__(self, e_health=500, e_dbonus=0, name="Bugged", player=None ):
        self.e_health = e_health
        self.e_dbonus = e_dbonus
        self.name     = name
        self.player = player
    def main(self):
        player = self.player
        print('Strength: ' + str(player.p_stre) +
            ', Accuracy: ' + str(player.p_accu) +
            ', Agility: ' + str(player.p_agil))
####################################################### Player Turn #######################################################
        def playertick():
            def maths():
                num1 = random.randint(1,999)
                num2 = random.randint(1,999)
                plusminus = random.randint(1,4)
                if plusminus > 2:
                    total = (num1 - num2)
                    print(num1, ' - ', num2, ' = ')
                else:
                    total = (num1 + num2)
                    print(num1, ' + ', num2, ' = ')
                timestart = time.time()

                valid = False
                while not valid:
                    try:
                        answer = int(input('Input Answer: '))
                        valid = True
                    except:
                        print("Invalid answer!")

                if answer == total:
                    timeend = time.time()
                    timeelapsed = timeend - timestart
                    print('Success, Time Elapsed: ', timeelapsed)
                    return int(timeelapsed)
                else:
                    timeelapsed = 30
                    print('Failed')
                    return int(timeelapsed)
            def calculatedamage(strength, accuracy, timeelapsed, p_dbonus):
                damage = random.randint(10,35)
                damage = damage + (strength * 2) + p_dbonus
                damagemod = 0
                damagemod = damagemod + timeelapsed
                damagemod = damagemod - accuracy
                print(damage)
                damage = damage - damagemod
                if damage <= 0:
                    damage = random.randint(1,10)
                    print('\n\n\nWeak Sauce!.. You Dealt', damage)
                    return damage
                elif damage > 65:
                    print('\n\n\nCritical Hit!.. You Dealt: ', damage)
                    return damage
                else:
                    print('\n\n\nYou Dealt: ', damage)
                    return damage
            mathsresult = int(maths())
            damagedealt = calculatedamage(player.p_stre, player.p_accu, mathsresult, player.p_dbonus)
            return int(damagedealt)

######################################################## Enemy Turn #######################################################
        def enemytock():
            def getRandomLine(name):
                with open(name) as file:
                    lines = file.read().splitlines()
                return random.choice(lines)
            def calculatedamageenemy(agility):
                damage = 15
                damagetype = random.randint(1,10)
                if damagetype > 7:
                    damage = random.randint(40,60)
                else:
                    damage = random.randint(10,30)
                damage = damage - ((agility * 2) * damage) / 100
                damage_type = getRandomLineWeighted("wordlists/damagetypes.txt")
                print('The ',self.name,' Deals ',damage, damagetype,' Damage')
                if player.cheater > 0:
                    print('But cheated')
                return damage
            enemydamage = int(calculatedamageenemy(player.p_agil))
            return enemydamage

####################################################### Encounter #######################################################
        enemyhealth = self.e_health
        print('\n\n\n############ You Encountered ', self.name, ' ############')
        print('############ ', self.name, ' Has ', enemyhealth, 'Health Remaining ############\n\n\n')
        while player.p_health > 0 or enemyhealth > 0:
            won = False
            enemyhealth = enemyhealth - int(playertick())
            print('\n\n\n############ ', self.name, ' Has ', enemyhealth, 'Health remaining ############')

            print_loading_dots(0.4)

            player.p_health = player.p_health - int(enemytock()) - player.cheater
            print('\n\n\n############', player.name, 'Has', player.p_health, 'Health remaining ############')
            if player.p_health < 0:
                print('\n\n\nYou were knocked unconcious')
                if player.cheater > 0:
                    print('YOU NORTY BOI YOU CHEATED AT MY GAME')
                print('You Lost',round(player.p_gold * 0.95), 'Gold')
                player.p_gold = round(player.p_gold * 0.95)
                player.p_health = player.p_health
                won = False
                return won

            elif enemyhealth <0:
                print('\n\n\nYOU WIN')
                print('Yo')
                player.p_gold = player.p_gold + random.randint(10,70)
                won = True
                return won

            print_loading_dots(0.4)
