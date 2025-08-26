import json
from ortools.sat.python import cp_model
from Instance import Instance

# === Load instance ===
instance = Instance.from_file("instance/test30.json")

# === Extract data ===
num_days = instance.days
patients = list(instance.patients.values())
rooms = list(instance.rooms.values())
room_ids = list(instance.rooms.keys())
surgeons = list(instance.surgeons.values())
weights = instance.weights

# === OR-Tools model ===
model = cp_model.CpModel()

# === Decision variables ===
admission_day = {}
room_assignment = {}
scheduled = {}

for p in patients:
    pid = p.id
    scheduled[pid] = model.NewBoolVar(f"scheduled_{pid}")
    admission_day[pid] = model.NewIntVar(0, num_days - 1, f"admission_day_{pid}")
    room_assignment[pid] = model.NewIntVar(0, len(room_ids) - 1, f"room_{pid}")

# === Constraints ===

# H1: No gender mixing in same room on same day
for d in range(num_days):
    for i, room in enumerate(rooms):
        male_present = []
        female_present = []
        for p in patients:
            pid = p.id
            if d + 1 < p.length_of_stay:
                continue

            start_ok = model.NewBoolVar(f"{pid}_start_le_d{d}_g")
            end_ok = model.NewBoolVar(f"{pid}_end_ge_d{d}_g")
            in_range = model.NewBoolVar(f"{pid}_in_range_d{d}_g")
            in_room = model.NewBoolVar(f"{pid}_in_r{i}_d{d}_g")
            present = model.NewBoolVar(f"{pid}_present_r{i}_d{d}_g")

            model.Add(admission_day[pid] <= d).OnlyEnforceIf(start_ok)
            model.Add(admission_day[pid] > d).OnlyEnforceIf(start_ok.Not())

            model.Add(admission_day[pid] + p.length_of_stay > d).OnlyEnforceIf(end_ok)
            model.Add(admission_day[pid] + p.length_of_stay <= d).OnlyEnforceIf(end_ok.Not())

            model.AddBoolAnd([start_ok, end_ok]).OnlyEnforceIf(in_range)
            model.AddBoolOr([start_ok.Not(), end_ok.Not()]).OnlyEnforceIf(in_range.Not())

            model.Add(room_assignment[pid] == i).OnlyEnforceIf(in_room)
            model.Add(room_assignment[pid] != i).OnlyEnforceIf(in_room.Not())

            model.AddBoolAnd([scheduled[pid], in_range, in_room]).OnlyEnforceIf(present)
            model.AddBoolOr([scheduled[pid].Not(), in_range.Not(), in_room.Not()]).OnlyEnforceIf(present.Not())

            if p.gender == "M":
                male_present.append(present)
            elif p.gender == "F":
                female_present.append(present)

        if male_present and female_present:
            any_male = model.NewBoolVar(f"male_present_r{i}_d{d}")
            any_female = model.NewBoolVar(f"female_present_r{i}_d{d}")
            model.AddMaxEquality(any_male, male_present)
            model.AddMaxEquality(any_female, female_present)
            model.Add(any_male + any_female <= 1)

# H2: Incompatible rooms
for p in patients:
    pid = p.id
    for i, rid in enumerate(room_ids):
        if rid in p.incompatible_room_ids:
            model.Add(room_assignment[pid] != i).OnlyEnforceIf(scheduled[pid])

# H3: Surgeon daily capacity (mandatory patients)
for d in range(num_days):
    for s in surgeons:
        sid = s.id
        surgery_durations = []
        for p in patients:
            if not p.mandatory or p.surgeon_id != sid:
                continue
            pid = p.id
            is_today = model.NewBoolVar(f"{pid}_surgery_day_{d}")
            model.Add(admission_day[pid] == d).OnlyEnforceIf(is_today)
            model.Add(admission_day[pid] != d).OnlyEnforceIf(is_today.Not())
            model.Add(scheduled[pid] == 1).OnlyEnforceIf(is_today)
            surgery_durations.append((is_today, p.surgery_duration))
        if surgery_durations:
            model.Add(sum(var * dur for var, dur in surgery_durations) <= s.max_surgery_time[d])

# H5: Mandatory patients must be scheduled
for p in patients:
    if p.mandatory:
        model.Add(scheduled[p.id] == 1)

# H6: Surgery release/due window
for p in patients:
    pid = p.id
    model.Add(admission_day[pid] >= p.surgery_release_day).OnlyEnforceIf(scheduled[pid])
    if p.mandatory:
        model.Add(admission_day[pid] <= p.surgery_due_day).OnlyEnforceIf(scheduled[pid])

# H7: Approximate room capacity constraint
for d in range(num_days):
    for i, room in enumerate(rooms):
        occupancy_vars = []
        for p in patients:
            pid = p.id
            if d + 1 < p.length_of_stay:
                continue

            stay_range_start = model.NewBoolVar(f"{pid}_stay_start_le_d{d}")
            model.Add(admission_day[pid] <= d).OnlyEnforceIf(stay_range_start)
            model.Add(admission_day[pid] > d).OnlyEnforceIf(stay_range_start.Not())

            stay_range_end = model.NewBoolVar(f"{pid}_stay_end_ge_d{d}")
            model.Add(admission_day[pid] + p.length_of_stay > d).OnlyEnforceIf(stay_range_end)
            model.Add(admission_day[pid] + p.length_of_stay <= d).OnlyEnforceIf(stay_range_end.Not())

            in_range = model.NewBoolVar(f"{pid}_in_range_d{d}")
            model.AddBoolAnd([stay_range_start, stay_range_end]).OnlyEnforceIf(in_range)
            model.AddBoolOr([stay_range_start.Not(), stay_range_end.Not()]).OnlyEnforceIf(in_range.Not())

            in_room = model.NewBoolVar(f"{pid}_in_r{i}_d{d}")
            model.Add(room_assignment[pid] == i).OnlyEnforceIf(in_room)
            model.Add(room_assignment[pid] != i).OnlyEnforceIf(in_room.Not())

            present = model.NewBoolVar(f"{pid}_present_r{i}_d{d}")
            model.AddBoolAnd([scheduled[pid], in_range, in_room]).OnlyEnforceIf(present)
            model.AddBoolOr([scheduled[pid].Not(), in_range.Not(), in_room.Not()]).OnlyEnforceIf(present.Not())

            occupancy_vars.append(present)

        if occupancy_vars:
            model.Add(sum(occupancy_vars) <= room.capacity)

# === Soft Constraint: Delay penalty ===
delay_penalty_terms = []
for p in patients:
    if p.mandatory:
        pid = p.id
        delay = model.NewIntVar(0, num_days, f"delay_{pid}")
        model.Add(delay == admission_day[pid] - p.surgery_release_day).OnlyEnforceIf(scheduled[pid])
        model.Add(delay == 0).OnlyEnforceIf(scheduled[pid].Not())
        delay_penalty_terms.append(delay * weights.patient_delay)

# === Soft Constraint: Mixed age penalty ===
mixed_age_penalties = []
for d in range(num_days):
    for i, room in enumerate(rooms):
        age_flags = {}
        for age in instance.age_groups:
            age_flags[age] = model.NewBoolVar(f"room_{i}_d{d}_has_{age}")

        for p in patients:
            pid = p.id
            if d + 1 < p.length_of_stay:
                continue

            start_ok = model.NewBoolVar(f"{pid}_start_le_d{d}_age")
            end_ok = model.NewBoolVar(f"{pid}_end_ge_d{d}_age")
            in_range = model.NewBoolVar(f"{pid}_in_range_d{d}_age")
            in_room = model.NewBoolVar(f"{pid}_in_r{i}_d{d}_age")
            present = model.NewBoolVar(f"{pid}_present_r{i}_d{d}_age")

            model.Add(admission_day[pid] <= d).OnlyEnforceIf(start_ok)
            model.Add(admission_day[pid] > d).OnlyEnforceIf(start_ok.Not())

            model.Add(admission_day[pid] + p.length_of_stay > d).OnlyEnforceIf(end_ok)
            model.Add(admission_day[pid] + p.length_of_stay <= d).OnlyEnforceIf(end_ok.Not())

            model.AddBoolAnd([start_ok, end_ok]).OnlyEnforceIf(in_range)
            model.AddBoolOr([start_ok.Not(), end_ok.Not()]).OnlyEnforceIf(in_range.Not())

            model.Add(room_assignment[pid] == i).OnlyEnforceIf(in_room)
            model.Add(room_assignment[pid] != i).OnlyEnforceIf(in_room.Not())

            model.AddBoolAnd([scheduled[pid], in_range, in_room]).OnlyEnforceIf(present)
            model.AddBoolOr([scheduled[pid].Not(), in_range.Not(), in_room.Not()]).OnlyEnforceIf(present.Not())

            model.AddImplication(present, age_flags[p.age_group])

        age_group_flags = list(age_flags.values())
        if len(age_group_flags) > 1:
            total_age_groups = model.NewIntVar(0, len(age_group_flags), f"age_group_count_r{i}_d{d}")
            model.Add(total_age_groups == sum(age_group_flags))

            at_least_two = model.NewBoolVar(f"at_least_two_ages_r{i}_d{d}")
            model.Add(total_age_groups >= 2).OnlyEnforceIf(at_least_two)
            model.Add(total_age_groups < 2).OnlyEnforceIf(at_least_two.Not())

            too_mixed = model.NewBoolVar(f"room_{i}_d{d}_mixed_age")
            model.Add(too_mixed == 1).OnlyEnforceIf(at_least_two)
            model.Add(too_mixed == 0).OnlyEnforceIf(at_least_two.Not())

            mixed_age_penalties.append(too_mixed * weights.room_mixed_age)

# === Objective ===
model.Maximize(
    sum(scheduled[p.id] for p in patients if not p.mandatory) * weights.unscheduled_optional
    - sum(delay_penalty_terms)
    - sum(mixed_age_penalties)
)

# === Solve ===
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 600.0
status = solver.Solve(model)
print("Solving time: {:.2f} seconds".format(solver.WallTime()))
print("Number of branches:", solver.NumBranches())

mandatory_scheduled = 0
mandatory_total = 0
optional_scheduled = 0
optional_total = 0

for p in patients:
    pid = p.id
    if p.mandatory:
        mandatory_total += 1
        if solver.Value(scheduled[pid]) == 1:
            mandatory_scheduled += 1
    else:
        optional_total += 1
        if solver.Value(scheduled[pid]) == 1:
            optional_scheduled += 1

print("Mandatory patients scheduled:", mandatory_scheduled, "/", mandatory_total)
print("Optional patients scheduled:", optional_scheduled, "/", optional_total)


# === Output ===
output = {"patients": []}
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    for p in patients:
        pid = p.id
        if solver.Value(scheduled[pid]) == 1:
            output["patients"].append({
                "id": pid,
                "admission_day": solver.Value(admission_day[pid]),
                "room": room_ids[solver.Value(room_assignment[pid])],
                "operating_theater": "t0"
            })
        else:
            output["patients"].append({
                "id": pid,
                "admission_day": "none"
            })

    with open("sol_test30_generated.json", "w") as f:
        json.dump(output, f, indent=2)
    print("✅ Solution written to sol_test30_generated.json")
else:
    print("❌ No feasible solution found.")