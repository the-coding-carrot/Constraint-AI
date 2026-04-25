from constraint import Problem
import json
import time
from itertools import combinations

with open("configC.json", "r") as f:
    config = json.load(f)

print("Setting up problem with pairwise constraints...")
dhbw = Problem()

domain = []
for day in config["days"]:
    for slot in config["timeslots"]:
        for room in config["rooms"]:
            for commission in config["commissions"]:
                domain.append((day, slot, room, commission))

print(f"Domain size: {len(domain)}")

variables = []
for group in config["groups"]:
    for presentation in ["A", "B", "C"]:
        var_name = (group, presentation)
        dhbw.addVariable(var_name, domain)
        variables.append(var_name)

print(f"Variables: {len(variables)}")

def get_group(var):
    return var[0]

def get_presentation(var):
    return var[1]

print("Adding per-variable constraints...")

def commission_available(assignment):
    day, slot, room, commission = assignment
    available = config["availability"][commission]
    return [day, int(slot)] in available

for var in variables:
    dhbw.addConstraint(commission_available, (var,))

print("Adding pairwise constraints...")
added = 0

for v1, v2 in combinations(variables, 2):
    group1 = get_group(v1)
    group2 = get_group(v2)
    pres1 = get_presentation(v1)
    pres2 = get_presentation(v2)
    
    def room_slot_conflict(a1, a2, _v1=v1, _v2=v2):
        day1, slot1, room1, comm1 = a1
        day2, slot2, room2, comm2 = a2
        if day1 == day2 and slot1 == slot2:
            return room1 != room2
        return True
    
    dhbw.addConstraint(room_slot_conflict, (v1, v2))
    
    if group1 == group2:
        def same_group_constraints(a1, a2, _v1=v1, _v2=v2, _p1=pres1, _p2=pres2):
            day1, slot1, room1, comm1 = a1
            day2, slot2, room2, comm2 = a2
            
            if day1 == day2:
                return False
            
            allowed1 = config["commissions"][comm1]
            allowed2 = config["commissions"][comm2]
            if _p1 not in allowed1 or _p2 not in allowed2:
                return False
            
            order_map = {"A": 0, "B": 1, "C": 2}
            if order_map[_p1] < order_map[_p2]:
                day_idx1 = config["days"].index(day1)
                day_idx2 = config["days"].index(day2)
                return day_idx1 < day_idx2
            elif order_map[_p1] > order_map[_p2]:
                day_idx1 = config["days"].index(day1)
                day_idx2 = config["days"].index(day2)
                return day_idx1 > day_idx2
            else:
                return True
        
        dhbw.addConstraint(same_group_constraints, (v1, v2))
    else:
        def different_group_constraints(a1, a2, _v1=v1, _v2=v2, _p1=pres1, _p2=pres2):
            day1, slot1, room1, comm1 = a1
            day2, slot2, room2, comm2 = a2
            allowed1 = config["commissions"][comm1]
            allowed2 = config["commissions"][comm2]
            return _p1 in allowed1 and _p2 in allowed2
        
        dhbw.addConstraint(different_group_constraints, (v1, v2))
    
    added += 1
    if added % 20 == 0:
        print(f"  Added {added} pairwise constraints...")

print(f"Total pairwise constraints: {added}")
print("\nSolving...")
start = time.time()
solution = dhbw.getSolution()
elapsed = time.time() - start

if solution:
    print(f"\n✓ Found solution in {elapsed:.2f}s!")
    print("\nSchedule:")
    for group in config["groups"]:
        print(f"\n{group}:")
        for pres in ["A", "B", "C"]:
            var = (group, pres)
            day, slot, room, comm = solution[var]
            print(f"  Presentation {pres}: {day} slot {slot} in {room} with {comm}")
else:
    print(f"No solution found in {elapsed:.2f}s")
