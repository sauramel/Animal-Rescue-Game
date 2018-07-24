from game_classes import *
from game_functions import *
from client_networking import *
import random
import socket
import pickle
import zlib
import time

print('Loading')
print_loading_dots(0.07, 20, 1)


##############################################################################################################

def getRandomLinefile(name):
    with open(name) as file:
        lines = file.read().splitlines()
        return random.choice(lines)

def generatename():
    name = getRandomLinefile('wordlists/animals.txt')
    return name

def randomenemy():
    health = random.randint(50,300)
    name = generatename()
    return health, name
character = 0

def assignpoints():
    print('############ Create Character ############\n')
    print('Strength = Base Damage')
    print('Accuracy = Deduction from penalty')
    print('Agility  = Chance to dodge')

    def stat_input(stat_name):
        valid = False
        while not valid:
            try:
                stat = int(input("Input {}".format(stat_name)))
                pointsremaining = pointsremaining - stat
                if pointsremaining < 0:
                    print('Too many points assigned, Retry')
                else:
                    valid = True
            except:
                print("Error: Your {} must be a number!".format(stat_name))


    pointsremaining = 20
    print('Points Remaining: ' + str(pointsremaining))

    # Strength
    strength = int(input('Input Strength: '))
    pointsremaining = pointsremaining - strength
    if pointsremaining < 0:
        print('Too many points assigned, Retry')
        assignpoints()
    print('Points Remaining: ')
    print(pointsremaining)

    # Accuracy
    accuracy = int(input('Input Accuracy: '))
    pointsremaining = pointsremaining - accuracy
    if pointsremaining < 0:
        print('Too many points assigned, Retry')
        assignpoints()
    print('Points Remaining: ')
    print(pointsremaining)

    # Agility
    agility = int(input('Input Agility: '))
    pointsremaining = pointsremaining - agility
    if pointsremaining < 0:
        print('Too many points assigned, Retry')
        assignpoints()
    print('Points Remaining: ')
    print(pointsremaining)

    if pointsremaining > 0:
        print('You failed to assign {} points...... Reassign?: '.format(pointsremaining))
        reassign = input('Y or N -- ')
        if reassign in ["Y","y"]:
            assignpoints()
        elif reassign in ["N","n"]:
            print('Continuing without assigning all points')
        else:
            print('Expected Y or N but got ' + reassign + ' Restarting...')
            assignpoints()
    name = input('Input your name: ')

    if strength > 20 or accuracy > 20 or agility > 20:
        cheater = max(strength, accuracy, agility) #50 + accuracy + agility
        return strength, accuracy, agility, cheater, name
    if pointsremaining == 0 or reassign == "N" or "n":
        cheater = 0
        return strength, accuracy, agility, cheater, name

######## THIS IS WHERE THE CODE STARTS EXECUTING ########

print("Loading complete")
print('\n\n\n\n')

multi = restrictive_input(
        "Singleplayer (0) or multiplayer (1)? ",
        lambda x: int(x),
        lambda x: x in [0,1])

if multi:
    print("BOI ITS NOT DONE YET LEAVE ME ALONE")
    time.sleep(0.69)

    valid_connection = False
    while not valid_connection:
        HOST, PORT = query_host_port(default=("25.21.236.231", 222))

        # # SEND HANDSHAKE 2 THE SERVER # #
        # P.S Most of these functions are #
        # defined in client_networking.py #
        # # # # # # # # # # # # # # # # # #
        valid_connection = send_handshake(HOST, PORT)

    ### HERE IS WHERE WE WILL TRY TO SEND THE PLAYER DATA TO THE SERVER ###
    ##### P.S The below part isn't complete.

    with socket.socket() as s:
        print("Connecting...")
        s.connect((HOST, PORT))
        print("Connection successful! Sending player data to server...")
        s.send(tb2_c)
        data_bytes = s.recv(1024)
        print("")

    ##################################################################################

    raise # Should move each gamemode into its own file or something


#################### SINGLEPLAYER ####################

# Generate the map
map = Map(size_x = 9, size_y = 9)

player = Player(stats_entry = assignpoints())
location = random.choice(map.locations)
player.location = location

while True:
    print("You are in the", player.location)
    player.location.print_map()

    if player.location.shop:
        print('There is a shop here.')

    fight = Encounter(player=player) # Need to pass the player because it's in a different file
    A, B = randomenemy()
    fight.e_health = A
    fight.name = B

    selection = 0
    print('\n 1. to fight \n 2. to check your balance: \n 3. to travel')
    if player.location.shop:
        print(' 4. to Access the Shop')
        print(' 5. to Heal Fully')
    selection = int(input('Input Selection: '))
    print('\n\n\n')
    if player.p_health < 1:
        print('YOU CANT DO THAT BECAUSE YOU DIED')
        selection = 404
    if selection == 1:
        if player.location.shop:
            print('There is nothing to fight here...')
        else:
            encounter_result = fight.main()
            if encounter_result:
                print("probably won")
            else:
                print("probably not")

    elif selection == 2:
        print('Your Gold = ', player.p_gold)

    elif selection == 3:
        randomencounter = random.randint(1,6)
        if randomencounter > 4 and not player.location.shop:
            print('YOU WERE AMBUSHED WHILE TRAVELING!!')
            fight.main()
        else:
            player.trymove(input('Which direction? '))

    elif selection == 4:
        shop = player.location.shop
        print("### You have entered {} ###".format(shop.name))
        while True:
            shop.print_wares()
            shop_input = restrictive_input(": ", lambda x: int(x), lambda x: 0 <= x <= len(shop.items))
            if shop_input == 0:
                print("You have left {}.".format(shop.name))
                break
            else:
                shop.try_buyitem(shop_input, player)
                print("\n ### You are in {} ###".format(shop.name))

    elif selection == 5:
        if player.location.shop:
            player.p_health = 500
        else:
            print('You need to be at a shop to perform that action.')

    elif selection == 404:
        Print('WE SHOULD FIGURE OUT A DEATH CONDITION...')

    elif selection == -69:
        print_properties(player)

    elif selection == "-360**13":
        player.p_stre = 500
        player.p_agil = 500
        player.p_accu = 500
        player.p_gold = 100000
        player.cheater = 0

x = input()
#--------------------------------------
#------------------------
#--------------------------------
#------------
#----------------------------------
#-----
#------------------------------------
#--------------------------------------
#--------------------------------------
#--------------------------------------
#--------------------------------------
#--------------------------------------
#--------------------------------------
#--
