Integrated healthcare scheduling deals with the coordination of resources re-
lated to various services within a single healthcare system. It aims to streamline
and optimize the flow of patients across different departments and facilities of
the hospital. The benefits of integrated healthcare optimization are manifold:
enhanced patient experience, improved operational efficiency, and optimized re-
source utilization across the entire hospital system.
Contributions to integrated healthcare applications have been surveyed by
Rachuba et al. [6]. They identify three levels of increasing integration, ranging
2 S. Ceschia et al.
from solving a single problem while incorporating the constraints coming from
the other problems (level 1), to sequentially solving two or more problems using
the output of one problem as input for the next one (level 2), and finally to
simultaneously solving two or more problems at once in a single stage (level 3).
A recent proposal for level 3 integration by Brandt et al. [1] addresses the
simultaneousresolutionoftwooperationalproblemsthatarecriticalinhospitals:
the Patient-to-Room Assignment (PRA) and the Nurse-to-Patient Assignment
(NPA) problems.
The Integrated Healthcare Timetabling Competition 2024 (IHTC) revises
the problem introduced by Brandt et al. and generalizes it by incorporating a
third important optimization problem in hospitals, namely Surgical Case Plan-
ning (SCP)[7]. The resulting integrated problem, which we call the Integrated
Healthcare Timetabling Problem (IHTP), brings together three NP-hard prob-
lems and requires the following decisions: (i) the admission date for each patient
(or admission postponement to the next scheduling period), (ii) the room for
each admitted patient for the duration of their stay, (iii) the nurse for each room
during each shift of the scheduling period, and (iv) the operating theater (OT)
for each admitted patient.
The IHTP is subject to many hard and soft constraints. Some of these con-
straintsrelatetoaspecificsubproblem,whileothersarisefromtheirinteractions.
The IHTP is a special case of real-world timetabling at hospitals, which are often
subject to additional constraints. Furthermore, we consider the static, determin-
istic variant of the IHTC, in which all information for a fixed scheduling period
is known at the time of solving.
The remainder of this paper is organized as follows. Section 2 provides the
problem definition. Section 3 introduces the datasets and the validator made
available to participants for evaluating their solutions. Finally, Section 4 de-
scribes the rules of the competition. Appendix A is also included as supple-
mentary material, which describes the file formats. All up-to-date information
concerning the competition is available at the competition’s website https:
//ihtc2024.github.io.
2 Problem definition
After first introducing the basic concepts of the IHTP, we will define the hard
and soft constraints of the problem and explain how they must be evaluated
throughout the entire scheduling horizon.
2.1 Basic concepts
We begin by introducing the time horizon and physical resources involved in the
IHTP:
Scheduling period: The scheduling period is defined as a number D of con-
secutive days. D is always a multiple of seven, and can vary from 14 (two
weeks) to 28 (four weeks). Days are numbered from 0 to D−1.
Last update 10th January 2025
Integrated Healthcare Timetabling Competition 3
Shifts: A shift denotes a nurse’s working period during a day. We assume three
non-overlapping shifts per day: early, late, and night. The entire scheduling
period thus consists of 3D shifts. Each shift is denoted by an integer ranging
from0 to3D−1.Theearly,lateandnightshiftsonthefirstdayarenumbered
0, 1, and 2, respectively. For the second day, the shifts are numbered 3, 4,
and 5. This pattern continues until the end of the scheduling period.
Operating theaters: All OTs are identical in that they are suitable for ac-
commodating any type of surgery. Each OT has a daily maximum capacity,
expressed in minutes. Some OTs might be unavailable on specific days, indi-
cated by a maximum capacity of 0 minutes on those days.
Rooms: Rooms host the patients during their recovery. These rooms are char-
acterized by their capacity, expressed in terms of the number of beds. Room
equipment is not explicitly taken into account. However, as will be outlined
in what follows, some rooms might be declared unsuitable for some patients.
Next, we describe the human resources that are involved in the IHTP:
Nurses: Each nurse has a skill level. Levels are strictly ordered (hierarchical)
and represented by an integer that ranges from 0 (lowest) to L−1 (highest),
where L is the number of skill levels. Furthermore, each nurse has a prede-
termined roster, which is defined as a set of shifts that the nurse has been
assigned to, along with the maximum workload the nurse can accommodate
in each shift. This roster is fixed and cannot be changed.
Surgeons: Each surgeon has a maximum operating time on each day, which is
0 when the surgeon is unavailable on that day. If a surgeon is available, we
assume their surgical team is also available. In other words, the surgeon and
theirteamformanatomicindivisibleresource(calledsurgeon forsimplicity).
Note that the maximum nurse workload is shift-dependent as nurses can
carry out auxiliary activities during some specific working shifts, thereby reduc-
ing their availability. Also note that we assume an open scheduling policy [3],
which means that all surgeons can operate in all OTs.
The patient is the central entity of the problem. The following information
is provided for each patient:
– mandatory/optional: mandatory patients must be admitted during the
scheduling period, while the admission of optional patients can be postponed
until a future scheduling period.
– release date: earliest possible admission date for the patient.
– due date: latest possible admission date, provided only for mandatory pa-
tients.
– age group: the age group of the patient (e.g., infant, youth, adult, elder).
The list of age groups is fully ordered.
– gender: the gender of the patient.
– length of stay: duration of the hospitalization in days.
Last update 10th January 2025
4 S. Ceschia et al.
– incompatible rooms: set of rooms that must not be allocated to the pa-
tient because, for example, they do not have the specific equipment or the
necessary isolation.
– surgery duration: the expected duration of the patient’s surgery, which is
assumed to always take place on the day of admission.
– surgeon: the surgeon who carries out the patient’s surgery.
– workload: the workload profile generated by the patient, which is described
by a vector, starts at the early shift of the admission day and ends at the
night shift of the discharge day. The length of the vector equals 3 times the
patient’s length of stay.
– minimum skill level: the minimum nurse skill level required by the patient
for each shift they are staying in the hospital; described by a vector similar
to the patient workload vector.
Note that both the workload and the minimum skill level required for a
patient can vary based on the shift and how long the patient has been in the
hospital, as these factors are related to the patient’s treatments and stage of
recovery. Both values are usually lower during night shifts and higher during the
initial days of the stay.
2.2 Solution
The solution of an IHTP instance consists of the following decisions:
i. the admission date for patients, or, in the case of optional patients, poten-
tially their postponement to the next scheduling period;
ii. the allocation of a room for each admitted patient;
iii. the assignment of a single nurse to each occupied room, for each shift within
the scheduling period;
iv. the assignment of patient surgeries to OTs, for each day of the scheduling
period.
We assume that patients are always admitted and discharged after the night
shift and before the early shift. Note that a patient stays in only one room during
the entire length of their stay, meaning a patient cannot be transferred from one
room to another.
We also assume that all patients undergo surgery, and that this takes place
on the day of admission. In addition, as each patient’s surgeon is predetermined,
the day of admission automatically determines the total surgery time of each
surgeon on each day. By contrast, the OT must be selected. This assignment
does not include the precise operating time, only the date. The IHTP does not
consider the order of surgeries in an OT.
A nurse can be assigned to more than one room in each shift (but only one
nurse is assigned to a room in a shift). Finally, note that it is necessary to assign
a nurse to a room on a given shift only if that room contains patients on the day
to which the shift belongs. Nevertheless, assigning nurses to empty rooms would
be feasible and does not incur additional costs.
Last update 10th January 2025
Integrated Healthcare Timetabling Competition 5
2.3 Constraints
We divide the constraints into four sets: (i) those related to the PAS problem,
(ii) those related to the NRA problem, (iii) those related related to the SCP
problem, and finally (iv) those related to the integration of the three problems.
In addition, constraints are categorized as either hard (starting with H) or soft
(startingwithS).Theformermustalwaysbesatisfied,whilethelattercontribute
totheobjectivefunction.ViolationsofsoftconstraintSi aremultipliedbyweight
Wi. Note that the soft constraint weights are instance-specific and thus given in
each input file.
Constraints on Patient Admission Scheduling
H1 No gender mix: Patients of different genders may not share a room on any
day.
H2 Compatible rooms: Patients can only be assigned to one of their compatible
rooms.
S1 Age groups: For each day of the scheduling period and for each room, the
maximum difference between age groups of patients sharing the room should
be minimized.
H7 Room capacity: The number of patients in each room in each day cannot
exceed the capacity of the room.
Constraints on Nurse-to-Room Assignment
While the IHTP does not explicitly require the assignment of nurses to pa-
tients, the combination of patient-to-room assignments and nurse-to-room as-
signments determines which nurses are responsible for which patients. The fol-
lowing constraints (S2, S3, and S4) depend on the resulting nurse-patient as-
signment.
S2 Minimum skill level: The minimum skill level a nurse must have to provide
the required care for a patient during each shift of their stay should be met.
If the skill level of the nurse assigned to a patient’s room in a shift does
not reach the minimum level required by that patient, a penalty is incurred
equal to the difference between the two skill levels. Note that a nurse with a
skill level greater than the minimum required can be assigned to the room
at no additional cost.
S3 Continuity of care: To ensure continuity of care, the total number of distinct
nurses providing care to a patient during their entire stay should be mini-
mized. The given rosters assume maximum one shift per day for each nurse,
hence the number of different nurses who take care of a patient is at least 3,
thus resulting in a minimum cost for this component of 3 times the number
of admitted patients.
S4 Maximum workload: For each shift, the total workload induced by patients
staying in rooms assigned to a nurse should not exceed the maximum work-
load of that nurse in that shift. The penalty is the amount by which the
total workload exceeds the limit, or 0 if it does not exceed it.
Last update 10th January 2025
6 S. Ceschia et al.
Constraints on Surgical Case Planning
H3 Surgeon overtime: The maximum daily surgery time of a surgeon must not
be exceeded.
H4 OT overtime: The duration of all surgeries allocated to an OT on a day
must not exceed its maximum capacity.
S5 Open OTs: The number of OTs opened on each day should be minimized.
Note that if an OT has no patients assigned for a particular day, it should
not open on that day.
S6 Surgeon transfer: The number of different OTs a surgeon is assigned to per
working day should be minimized.
Global constraints
H5 Mandatory versus optional patients: All mandatory patients must be ad-
mitted within the scheduling period, whereas optional patients may be post-
poned to future scheduling periods.
H6 Admission day: A patient can be admitted on any day from their release
date to their due date. Given that optional patients do not have a due date,
they can be admitted on any day after their release date.
S7 Admission delay: The number of days between a patient’s release date and
their actual date of admission should be minimized.
S8 Unscheduledpatients:Thenumberofoptionalpatientswhoarenotadmitted
in the current scheduling period should be minimized.
