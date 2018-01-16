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
		print("Number of Workers: " + str(numWorkers))
		print("Number of Factories: " + str(numFactory))
		print("Number of Blueprints: " + str(numBlueprint))
		print("Number of Rangers: " + str(numRanger))
		print("Number of Knights: " + str(numKnight))
		print("Number of Mages: " + str(numMage))
		print("Number of Rockets: " + str(numRocket))

		for unit in gc.my_units():
			d = random.choice(directions)
			if unit.unit_type == bc.UnitType.Worker:
				d = random.choice(directions)
				if numWorkers<5 and gc.can_replicate(unit.id,d):
					gc.replicate(unit.id,d)
					continue
				if gc.round() > 150 and gc.can_blueprint(unit.id, bc.UnitType.Rocket, d) and gc.karbonite() > bc.UnitType.Rocket.blueprint_cost():
					gc.blueprint(unit.id, bc.UnitType.Rocket, d)
					continue
				if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and numFactory < 3:#blueprint
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

			if unit.unit_type == bc.UnitType.Rocket:
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

			if unit.unit_type == bc.UnitType.Factory:
				garrison = unit.structure_garrison()
				if len(garrison) > 0:#ungarrison
					if gc.can_unload(unit.id, d):
						gc.unload(unit.id, d)
						continue
				elif gc.can_produce_robot(unit.id, bc.UnitType.Ranger) and numRanger < 60: #produce Rangers
					gc.produce_robot(unit.id, bc.UnitType.Ranger)
					continue
				elif gc.can_produce_robot(unit.id, bc.UnitType.Knight) and numKnight < 0:#produce Knights
					gc.produce_robot(unit.id, bc.UnitType.Knight)
					continue

			if unit.unit_type == bc.UnitType.Knight:
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
							fuzzygoto(unit.id, other.location.map_location())
							continue
					if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
						gc.move_robot(unit.id, d)
						continue

			if unit.unit_type == bc.UnitType.Ranger:
				if unit.location.is_on_map():
					inRangeUnits = gc.sense_nearby_units(unit.location.map_location(), 50)
					for other in inRangeUnits:
						if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
							gc.attack(unit.id, other.id)
							continue
					if rocketWaiting:
						if gc.is_move_ready(unit.id) and unit.location.is_on_planet(bc.Planet.Earth):
							ml = unit.location.map_location()
							rdist = ml.distance_squared_to(rocketLocation)
							if rdist>2:
								fuzzygoto(unit, rocketLocation)
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
