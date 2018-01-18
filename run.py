import battlecode as bc
import random
import sys
import traceback
import os

gc = bc.GameController()
directions = [bc.Direction.North, bc.Direction.Northeast, bc.Direction.East, bc.Direction.Southeast, bc.Direction.South, bc.Direction.Southwest, bc.Direction.West, bc.Direction.Northwest]
tryRotate = [0,-1,1,-2,2]
my_team = gc.team()


def invert(loc):#assumes Earth
	newx = earthMap.width-loc.x
	newy = earthMap.height-loc.y
	return bc.MapLocation(bc.Planet.Earth,newx,newy)

def locToStr(loc):
	return '('+str(loc.x)+','+str(loc.y)+')'

if gc.planet() == bc.Planet.Earth:
	oneLoc = gc.my_units()[0].location.map_location()
	earthMap = gc.starting_map(bc.Planet.Earth)
	enemyStart = invert(oneLoc);
	print('worker starts at '+locToStr(oneLoc))
	print('enemy worker presumably at '+locToStr(enemyStart))

marsMap = gc.starting_map(bc.Planet.Earth)

def rotate(dir,amount):
	ind = directions.index(dir)
	return directions[(ind+amount)%8]

def goto(unit,dest):
	d = unit.location.map_location().direction_to(dest)
	if gc.can_move(unit.id, d):
		gc.move_robot(unit.id,d)

def fuzzygoto(unit,dest):
	toward = unit.location.map_location().direction_to(dest)
	for tilt in tryRotate:
		d = rotate(toward,tilt)
		if gc.can_move(unit.id, d):
			gc.move_robot(unit.id,d)
			break

gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Healer)

while True:
	try:
		#count things: unfinished buildings, workers
		numWorkers = 0
		numFactory = 0
		numBlueprint = 0
		numRanger = 0
		numKnight = 0
		numMage = 0
		numRocket = 0
		numHealer = 0
		blueprintLocation = None
		blueprintWaiting = False
		rocketLocation = None
		rocketWaiting = False
		for unit in gc.my_units():
			if unit.unit_type== bc.UnitType.Factory:
				if not unit.structure_is_built():
					ml = unit.location.map_location()
					blueprintLocation = ml
					blueprintWaiting = True
					numBlueprint+=1
				else:
					numFactory+=1
			if unit.unit_type == bc.UnitType.Rocket:
				if not unit.structure_is_built():
					ml = unit.location.map_location()
					blueprintLocation = ml
					blueprintWaiting = True
					numBlueprint+=1
				else:
					ml = unit.location.map_location()
					rocketLocation = ml
					rocketWaiting = True
					numRocket+=1
			if unit.unit_type== bc.UnitType.Worker:
				numWorkers+=1
			if unit.unit_type == bc.UnitType.Ranger:
				numRanger+=1
			if unit.unit_type == bc.UnitType.Knight:
				numKnight+=1
			if unit.unit_type == bc.UnitType.Mage:
				numMage+=1
			if unit.unit_type == bc.UnitType.Healer:
				numHealer+=1
		print("Number of Workers: " + str(numWorkers))
		print("Number of Factories: " + str(numFactory))
		print("Number of Blueprints: " + str(numBlueprint))
		print("Number of Rangers: " + str(numRanger))
		print("Number of Knights: " + str(numKnight))
		print("Number of Mages: " + str(numMage))
		print("Number of Rockets: " + str(numRocket))
		print("Number of Healer" + str(numHealer))

		for unit in gc.my_units():
			d = random.choice(directions)
			if unit.unit_type == bc.UnitType.Worker: # Worker micro
				if gc.karbonite_at(unit.location.map_location()) and gc.can_harvest(unit.id, d):
					gc.harvest(unit.id, d)
				d = random.choice(directions)
				if numWorkers<5 and gc.can_replicate(unit.id, d):
					gc.replicate(unit.id,d)
					continue
				if gc.round() > 150 and gc.can_blueprint(unit.id, bc.UnitType.Rocket, d) and gc.karbonite() > bc.UnitType.Rocket.blueprint_cost():
					gc.blueprint(unit.id, bc.UnitType.Rocket, d)
					continue
				if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and numFactory <= 5:#blueprint
					if gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
						gc.blueprint(unit.id, bc.UnitType.Factory, d)
						continue
				adjacentUnits = gc.sense_nearby_units(unit.location.map_location(), 2)
				for adjacent in adjacentUnits:#build
					if gc.can_build(unit.id,adjacent.id):
						gc.build(unit.id,adjacent.id)
						continue
				if blueprintWaiting:
					if gc.is_move_ready(unit.id):
						ml = unit.location.map_location()
						bdist = ml.distance_squared_to(blueprintLocation)
						if bdist>2:
							fuzzygoto(unit,blueprintLocation)
							continue
				if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
					gc.move_robot(unit.id, d)
					continue

			if unit.unit_type == bc.UnitType.Rocket: # rocket micro
				passenger = unit.structure_garrison()
				if rocketWaiting:
					if len(passenger) < 6 and unit.location.is_on_planet(bc.Planet.Earth):
						adjacentUnits = gc.sense_nearby_units(unit.location.map_location(), 2)
						for other in adjacentUnits:
							if other.team == my_team and other.unit_type == bc.UnitType.Ranger and gc.can_load(unit.id, other.id):
								gc.load(unit.id, other.id)
								continue
					elif len(passenger) >= 6:
						mx = random.randint(0, marsMap.width)
						my = random.randint(0, marsMap.height)
						landingSite = bc.MapLocation(bc.Planet.Mars, mx, my)
						if gc.can_launch_rocket(unit.id, landingSite) and gc.starting_map(bc.Planet.Mars).is_passable_terrain_at(bc.MapLocation(bc.Planet.Mars, mx, my)):
							gc.launch_rocket(unit.id, landingSite)
							rocketWaiting = False
							continue
				if unit.location.is_on_map() and unit.location.is_on_planet(bc.Planet.Mars):
					if len(passenger) > 0:
						if gc.can_unload(unit.id, d):
							gc.unload(unit.id, d)
							continue

			if unit.unit_type == bc.UnitType.Factory: # Factory micro
				garrison = unit.structure_garrison()
				if len(garrison) > 0:#ungarrison
					if gc.can_unload(unit.id, d):
						gc.unload(unit.id, d)
				else:
					build = random.randint(1,5)
					if  build == 1 or build == 2 or build == 3 or build == 4:
						if gc.can_produce_robot(unit.id, bc.UnitType.Ranger) and numRanger <= 75: #produce Rangers
							gc.produce_robot(unit.id, bc.UnitType.Ranger)
							continue
					if build == 5:
						if gc.can_produce_robot(unit.id, bc.UnitType.Healer) and numHealer <= 20: #produce Healers
							gc.produce_robot(unit.id, bc.UnitType.Healer)
							continue
						continue

			if unit.unit_type == bc.UnitType.Knight: # Knight micro
				if unit.location.is_on_map():#can't move from inside a factory
					inRangeUnits = gc.sense_nearby_units(unit.location.map_location(), 2)
					for other in inRangeUnits:
						if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
							gc.attack(unit.id, other.id)
							continue
					inViewUnits = gc.sense_nearby_units(unit.location.map_location(), 50)
					for other in inViewUnits:
						if other.team != my_team and gc.is_move_ready(unit.id):
							el = other.location.map_location()
							fuzzygoto(unit, el)
							continue
					if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
						gc.move_robot(unit.id, d)
						continue

			if unit.unit_type == bc.UnitType.Healer: #Healer micro
				if unit.location.is_on_map():
					inHealUnits = gc.sense_nearby_units(unit.location.map_location(), 30)
					for other in inHealUnits:
						if other.team == my_team and gc.is_heal_ready(unit.id) and gc.can_heal(unit.id, other.id) and other.unit_type == bc.UnitType.Ranger:
							if other.health <= 80:
								gc.heal(unit.id, other.id)
								continue
					if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
						gc.move_robot(unit.id, d)
						continue

			if unit.unit_type == bc.UnitType.Mage: # Mage micro
				if unit.location.is_on_map():
					inFireballUnits = gc.sense_nearby_units(unit.location.map_location(), 30)
					for other in inFireballUnits:
						if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
							gc.attack(unit.id, other.id)
							continue
						if other.team != my_team and gc.is_move_ready(unit.id):
							el = other.location.map_location()
							fuzzygoto(unit, el)
							continue
				if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
					gc.move_robot(unit.id, d)
					continue

			if unit.unit_type == bc.UnitType.Ranger: # Ranger micro
				if unit.location.is_on_map():
					inRangeUnits = gc.sense_nearby_units(unit.location.map_location(), 50)
					attacking = False
					for other in inRangeUnits:
						if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
							attacking = True
							gc.attack(unit.id, other.id)
							continue
					if rocketWaiting:
						if gc.is_move_ready(unit.id) and unit.location.is_on_planet(bc.Planet.Earth):
							ml = unit.location.map_location()
							rdist = ml.distance_squared_to(rocketLocation)
							if rdist>2:
								fuzzygoto(unit, rocketLocation)
								continue
					if not attacking:
						if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
							gc.move_robot(unit.id, d)
							continue

	except Exception as e:
		print('Error:', e)
		traceback.print_exc()

	# send the actions we've performed, and wait for our next turn.
	gc.next_turn()

	# these lines are not strictly necessary, but it helps make the logs make more sense.
	# it forces everything we've written this turn to be written to the manager.
	sys.stdout.flush()
	sys.stderr.flush()
