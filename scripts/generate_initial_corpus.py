#!/usr/bin/env python3
"""
Corpus Generator Script
Generates a realistic collection of 24 institutional policy documents across 6 categories
and creates the authoritative data/raw/corpus_manifest.json with SHA-256 checksums.
"""

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

DOCUMENTS = [
    # 1. Academic Regulations
    {
        "document_id": "DOC-ACAD-001",
        "title": "Autonomous Academic Regulations & Credit Framework 2024-2025",
        "category": "academic_regulations",
        "language": "en",
        "file_name": "DOC-ACAD-001.txt",
        "folder": "academic_regulations",
        "file_type": "txt",
        "expected_page_count": 3,
        "description": "Choice Based Credit System (CBCS), degree duration, credit minimums, and 10-point grading scales.",
        "content": """================================================================================
AUTONOMOUS ACADEMIC REGULATIONS & CREDIT FRAMEWORK (2024-2025)
Document ID: DOC-ACAD-001 | Category: Academic Regulations | Version: 2.1
================================================================================

1. PROGRAM STRUCTURE AND DURATION
1.1 The Master of Computer Applications (MCA) and Bachelor of Engineering (BE) programs operate under the Choice Based Credit System (CBCS) across semester patterns.
1.2 The minimum duration for the 2-year MCA program shall be four (4) academic semesters, and the maximum duration permitted for completion shall be eight (8) consecutive semesters from the date of admission.
1.3 Each academic year is partitioned into two regular semesters: Odd Semester (August to December) and Even Semester (January to May), comprising a minimum of ninety (90) instructional days each.

2. CREDIT SYSTEM AND COURSE ALLOCATION
2.1 One credit is equivalent to one (1) hour of lecture/tutorial per week or two (2) hours of practical laboratory session per week over a 15-week instructional semester.
2.2 The minimum total credits required for the award of the MCA degree is eighty-eight (88) credits, distributed across Program Core, Professional Electives, Open Electives, and Project Work.
2.3 A student may register for a maximum of twenty-eight (28) credits and a minimum of sixteen (16) credits in any regular semester, subject to prerequisites.

3. GRADING SCHEME AND PERFORMANCE METRICS
3.1 Academic performance is graded on a 10-point scale:
    - Grade 'O' (Outstanding)     : Marks >= 90% -> Grade Point 10
    - Grade 'A+' (Excellent)      : Marks 80-89% -> Grade Point 9
    - Grade 'A' (Very Good)       : Marks 70-79% -> Grade Point 8
    - Grade 'B+' (Good)           : Marks 60-69% -> Grade Point 7
    - Grade 'B' (Above Average)   : Marks 50-59% -> Grade Point 6
    - Grade 'C' (Pass)            : Marks 40-49% -> Grade Point 5
    - Grade 'F' (Fail)            : Marks < 40%  -> Grade Point 0
    - Grade 'AB' (Absent)         : Grade Point 0
3.2 The Semester Grade Point Average (SGPA) is computed as: SGPA = Sum(Credit_i * GradePoint_i) / Sum(Credit_i).
3.3 The Cumulative Grade Point Average (CGPA) is computed across all completed semesters from matriculation to date."""
    },
    {
        "document_id": "DOC-ACAD-002",
        "title": "Degree Requirements, CGPA Calculation & Award of Honors",
        "category": "academic_regulations",
        "language": "en",
        "file_name": "DOC-ACAD-002.txt",
        "folder": "academic_regulations",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Graduation criteria, classification of degrees, First Class with Distinction, and Honors degree guidelines.",
        "content": """================================================================================
DEGREE REQUIREMENTS, CGPA CALCULATION & AWARD OF HONORS
Document ID: DOC-ACAD-002 | Category: Academic Regulations | Version: 1.4
================================================================================

1. ELIGIBILITY FOR DEGREE CONFERMENT
1.1 A student shall be declared eligible for the award of the degree if they have:
    a) Earned all prescribed credits specified in the curriculum (88 credits for MCA).
    b) Maintained a final CGPA of not less than 5.00 at the end of the final semester.
    c) Cleared all mandatory non-credit audit courses (Environmental Studies, Research Methodology).
    d) No pending disciplinary cases, malpractice investigations, or institutional fee dues.

2. CLASSIFICATION OF DEGREE AWARDS
2.1 Degree classifications are determined strictly by final CGPA upon completing the program:
    - First Class with Distinction (FCD): CGPA >= 7.75, provided all courses are cleared in the first attempt within normal duration.
    - First Class (FC)                  : CGPA >= 6.75 and < 7.75.
    - Second Class (SC)                 : CGPA >= 5.00 and < 6.75.
2.2 Students clearing courses through supplementary or make-up exams are not eligible for University ranks or Gold Medals."""
    },
    {
        "document_id": "DOC-ACAD-003",
        "title": "Course Registration, Add-Drop and Withdrawal Bylaws",
        "category": "academic_regulations",
        "language": "en",
        "file_name": "DOC-ACAD-003.txt",
        "folder": "academic_regulations",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Timeline for course registration, elective selection, add/drop windows, and formal semester withdrawal.",
        "content": """================================================================================
COURSE REGISTRATION, ADD-DROP AND WITHDRAWAL BYLAWS
Document ID: DOC-ACAD-003 | Category: Academic Regulations | Version: 1.2
================================================================================

1. SEMESTER REGISTRATION TIMELINES
1.1 Every student must formally register for prescribed core and elective courses within the first three (3) working days of the semester via the student portal.
1.2 Late registration with a fine of Rs. 500 is permitted up to seven (7) working days after semester commencement with Dean approval.

2. ADD / DROP OF ELECTIVE COURSES
2.1 A student may add or drop an elective course within ten (10) instructional days from the beginning of the semester.
2.2 Dropping a course reduces the semester credit count; however, the registered credits must not drop below the mandatory minimum of sixteen (16) credits.

3. TEMPORARY SEMESTER WITHDRAWAL
3.1 A student may apply for temporary semester withdrawal on genuine medical grounds before the conduct of the second Continuous Internal Evaluation (CIE-2)."""
    },
    {
        "document_id": "DOC-ACAD-004",
        "title": "Academic Calendar & Semester Schedule Guidelines",
        "category": "academic_regulations",
        "language": "en",
        "file_name": "DOC-ACAD-004.txt",
        "folder": "academic_regulations",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Instructional duration, internal test schedules, vacation periods, and grievance redressal timelines.",
        "content": """================================================================================
ACADEMIC CALENDAR & SEMESTER SCHEDULE GUIDELINES
Document ID: DOC-ACAD-004 | Category: Academic Regulations | Version: 1.1
================================================================================

1. CALENDAR STRUCTURE AND INSTRUCTION DAYS
1.1 The Academic Calendar is published by the Dean (Academic) at least two weeks prior to the commencement of each academic year.
1.2 Each semester guarantees a minimum of 90 instructional days excluding days designated for Semester End Examinations (SEE).

2. ASSESSMENT MILESTONES
2.1 Continuous Internal Evaluation 1 (CIE-1): Scheduled at the end of the 5th week of instruction.
2.2 Continuous Internal Evaluation 2 (CIE-2): Scheduled at the end of the 10th week of instruction.
2.3 Lab Internal Tests: Conducted during the 14th week of the semester.
2.4 Semester End Examinations (SEE): Commence from the 16th week onwards."""
    },

    # 2. Examination Guidelines
    {
        "document_id": "DOC-EXAM-001",
        "title": "Semester End Examination Code of Conduct & Malpractice Rules",
        "category": "examination_guidelines",
        "language": "en",
        "file_name": "DOC-EXAM-001.txt",
        "folder": "examination_guidelines",
        "file_type": "txt",
        "expected_page_count": 3,
        "description": "Examination entry rules, hall ticket mandates, prohibited electronic items, and Malpractice Committee penalties.",
        "content": """================================================================================
SEMESTER END EXAMINATION CODE OF CONDUCT & MALPRACTICE RULES
Document ID: DOC-EXAM-001 | Category: Examination Guidelines | Version: 2.0
================================================================================

1. EXAMINATION HALL ADMISSION RULES
1.1 Candidates must occupy their allotted seats fifteen (15) minutes prior to the scheduled examination commencement.
1.2 No student shall be admitted to the examination hall after thirty (30) minutes from the commencement of the exam.
1.3 Candidates must produce their valid Institutional Identity Card and official Hall Ticket to the room invigilator upon request.

2. PROHIBITED ARTICLES AND ELECTRONIC DEVICES
2.1 Mobile phones, programmable calculators, smart watches, Bluetooth devices, and handwritten notes are strictly prohibited inside the hall.
2.2 Possession of unauthorized material, whether accessed or not, constitutes a prima facie case of examination malpractice.

3. MALPRACTICE INQUIRY AND PENALTY MATRIX
3.1 Level 1 Offense (Possession of copying material / copying from neighboring candidate): Cancellation of the concerned paper; award of 'F' grade in the subject.
3.2 Level 2 Offense (Smuggling question papers / answer booklets / digital communication): Cancellation of all registered courses in the current semester; debarment for one subsequent semester.
3.3 Level 3 Offense (Impersonation / assault on invigilator): Expulsion from the institution and lodging of formal police FIR."""
    },
    {
        "document_id": "DOC-EXAM-002",
        "title": "Answer Script Revaluation and Challenge Evaluation Regulations",
        "category": "examination_guidelines",
        "language": "en",
        "file_name": "DOC-EXAM-002.txt",
        "folder": "examination_guidelines",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Procedure for obtaining answer script photocopies, revaluation fee structure, and challenge evaluation rules.",
        "content": """================================================================================
ANSWER SCRIPT REVALUATION AND CHALLENGE EVALUATION REGULATIONS
Document ID: DOC-EXAM-002 | Category: Examination Guidelines | Version: 1.3
================================================================================

1. PHOTOCOPY OF VALUED ANSWER SCRIPTS
1.1 A student may apply for a soft copy/photocopy of their evaluated Semester End Examination answer script within five (5) working days of result declaration upon payment of Rs. 300 per subject.

2. REVALUATION APPLICATION & SCORING RULES
2.1 Revaluation applications must be submitted online within ten (10) days of result announcement. The revaluation fee is Rs. 750 per theory course.
2.2 If the difference between original valuation and revaluation is >= 15% of maximum marks, the script shall be sent to a third evaluator, and the average of the two nearest scores shall be final.
2.3 If revaluation results in an increase of >= 10 marks or changes the result from Fail to Pass, a refund of 50% of the revaluation fee will be credited."""
    },
    {
        "document_id": "DOC-EXAM-003",
        "title": "Make-Up and Fast-Track Supplementary Examination Policy",
        "category": "examination_guidelines",
        "language": "en",
        "file_name": "DOC-EXAM-003.txt",
        "folder": "examination_guidelines",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Eligibility criteria for make-up examinations, fast-track summer semesters, and maximum allowable backlog registration.",
        "content": """================================================================================
MAKE-UP AND FAST-TRACK SUPPLEMENTARY EXAMINATION POLICY
Document ID: DOC-EXAM-003 | Category: Examination Guidelines | Version: 1.5
================================================================================

1. MAKE-UP EXAMINATION ELIGIBILITY
1.1 Make-up examinations are conducted exclusively for students who missed regular Semester End Examinations due to serious illness (hospitalization) or institutional duty, with prior approval.
1.2 Students who obtained an 'F' grade due to poor performance in regular exams are NOT eligible for make-up exams; they must appear in supplementary/fast-track exams.

2. FAST-TRACK SUMMER SEMESTER
2.1 A fast-track summer semester of 6 weeks is conducted during June-July for students with backlogs.
2.2 A student may register for a maximum of four (4) backlog courses or sixteen (16) credits during the fast-track semester upon paying the prescribed per-credit examination fee."""
    },
    {
        "document_id": "DOC-EXAM-004",
        "title": "Grade Card Issuance, Duplicate Certificate & Transcript Rules",
        "category": "examination_guidelines",
        "language": "en",
        "file_name": "DOC-EXAM-004.txt",
        "folder": "examination_guidelines",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Procedures for provisional grade cards, official transcripts for overseas admissions, and duplicate degree issuance.",
        "content": """================================================================================
GRADE CARD ISSUANCE, DUPLICATE CERTIFICATE & TRANSCRIPT RULES
Document ID: DOC-EXAM-004 | Category: Examination Guidelines | Version: 1.1
================================================================================

1. SEMESTER GRADE CARDS
1.1 Official hard-copy Semester Grade Cards are issued through the respective department offices within twenty (20) working days following the announcement of final revaluation results.

2. OFFICIAL TRANSCRIPTS
2.1 Transcripts for higher education or employment applications may be requested through the Examination Portal.
2.2 Standard processing time is five (5) working days for electronic transcripts and ten (10) working days for sealed physical copies.

3. DUPLICATE GRADE CARDS / DEGREE CERTIFICATES
3.1 In the event of loss or damage, a duplicate certificate will be issued upon submitting a notarized affidavit, police non-traceable report, and payment of Rs. 1,500."""
    },

    # 3. Attendance Guidelines
    {
        "document_id": "DOC-ATTN-001",
        "title": "Mandatory Attendance Thresholds and 75% Requirement Policy",
        "category": "attendance",
        "language": "en",
        "file_name": "DOC-ATTN-001.txt",
        "folder": "attendance",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Mandatory 75% minimum attendance requirement per course, computation methods, and biometric verification rules.",
        "content": """================================================================================
MANDATORY ATTENDANCE THRESHOLDS AND 75% REQUIREMENT POLICY
Document ID: DOC-ATTN-001 | Category: Attendance | Version: 2.0
================================================================================

1. MINIMUM ATTENDANCE REQUIREMENT
1.1 Every student is required to maintain a minimum attendance of seventy-five percent (75%) in each individual registered theory and practical course to be eligible to appear for the Semester End Examination.
1.2 Attendance is calculated from the date of commencement of instructional classes as per the official academic calendar until the last working day.

2. BIOMETRIC LOGGING & PORTAL SYNCHRONIZATION
2.1 Attendance is logged in real-time by course instructors via the institutional Enterprise Resource Planning (ERP) portal.
2.2 Students can monitor their live cumulative attendance percentage daily through the student dashboard. Any discrepancy must be reported within forty-eight (48) hours of class conduct."""
    },
    {
        "document_id": "DOC-ATTN-002",
        "title": "Medical Leave Condonation and Duty Leave Regulations",
        "category": "attendance",
        "language": "en",
        "file_name": "DOC-ATTN-002.txt",
        "folder": "attendance",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Condonation rules for medical emergencies between 65% and 75%, On-Duty (OD) approval, and medical certificate submission.",
        "content": """================================================================================
MEDICAL LEAVE CONDONATION AND DUTY LEAVE REGULATIONS
Document ID: DOC-ATTN-002 | Category: Attendance | Version: 1.4
================================================================================

1. ATTENDANCE CONDONATION ON MEDICAL GROUNDS
1.1 The Principal / Dean (Academic) may condone attendance shortages up to a maximum of ten percent (10%), permitting students with attendance between 65% and 74.9% to appear for exams, strictly on valid medical grounds or university-sanctioned sports/cultural events.
1.2 Under no circumstances shall a student with attendance below sixty-five percent (65%) be granted condonation.

2. MEDICAL CERTIFICATE SUBMISSION PROCEDURE
2.1 In case of medical illness exceeding three (3) consecutive days, the student must notify the Head of Department (HOD) in writing within forty-eight (48) hours of absence.
2.2 Original medical fitness certificate, hospitalization records, and prescription bills issued by a registered medical practitioner must be submitted within three (3) working days of returning to campus.

3. ON-DUTY (OD) ATTENDANCE CREDIT
3.1 Students representing the institution in sports tournaments, hackathons, seminars, or placement training are eligible for Duty Leave (OD), credited upon producing an authorized participation certificate."""
    },
    {
        "document_id": "DOC-ATTN-003",
        "title": "Attendance Shortage Detention and Course Repetition Bylaws",
        "category": "attendance",
        "language": "en",
        "file_name": "DOC-ATTN-003.txt",
        "folder": "attendance",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Consequences of attendance shortage below 65%, course detention (NSSR), and mandatory course re-registration.",
        "content": """================================================================================
ATTENDANCE SHORTAGE DETENTION AND COURSE REPETITION BYLAWS
Document ID: DOC-ATTN-003 | Category: Attendance | Version: 1.2
================================================================================

1. COURSE DETENTION (NOT SATISFIED SEMESTER REQUIREMENTS - NSSR)
1.1 A student whose attendance in a course falls below 65% (or below 75% without approved medical condonation) shall be awarded the grade 'NSSR' (Course Detention) and debarred from appearing in the Semester End Examination of that course.
1.2 Internal Assessment (CIE) marks obtained in a detained course stand annulled.

2. RE-REGISTRATION AND COURSE REPETITION
2.1 Detained students must re-register for the course in its entirety (attending lectures, practicals, and repeating CIE) during the subsequent regular semester or fast-track summer semester, paying the per-course re-registration fee."""
    },
    {
        "document_id": "DOC-ATTN-004",
        "title": "Internal Assessment Biometric Logging & Grievance Guidelines",
        "category": "attendance",
        "language": "en",
        "file_name": "DOC-ATTN-004.txt",
        "folder": "attendance",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Continuous Internal Evaluation (CIE) eligibility, internal test attendance, and grievance redressal committee procedures.",
        "content": """================================================================================
INTERNAL ASSESSMENT BIOMETRIC LOGGING & GRIEVANCE GUIDELINES
Document ID: DOC-ATTN-004 | Category: Attendance | Version: 1.0
================================================================================

1. CIE ELIGIBILITY AND MINIMUM SCORE CRITERIA
1.1 A student must secure a minimum of 40% in continuous internal assessments (CIE) in theory courses and 50% in laboratory courses to be certified eligible for Semester End Examinations.

2. ATTENDANCE GRIEVANCE COMMITTEE
2.1 If a student believes an attendance entry in the ERP portal is incorrect due to technical failure, they may appeal to the Department Attendance Grievance Committee within three (3) working days of the monthly attendance display."""
    },

    # 4. Scholarships & Financial Aid
    {
        "document_id": "DOC-SCHOL-001",
        "title": "Institutional Merit-cum-Means Scholarship Guidelines 2024",
        "category": "scholarships",
        "language": "en",
        "file_name": "DOC-SCHOL-001.txt",
        "folder": "scholarships",
        "file_type": "txt",
        "expected_page_count": 3,
        "description": "Income caps, CGPA criteria, scholarship disbursement amounts, and annual renewal prerequisites.",
        "content": """================================================================================
INSTITUTIONAL MERIT-CUM-MEANS SCHOLARSHIP GUIDELINES 2024
Document ID: DOC-SCHOL-001 | Category: Scholarships | Version: 2.1
================================================================================

1. ELIGIBILITY CRITERIA
1.1 Family Annual Income: The total annual household income of the applicant's parents/guardians from all sources must not exceed Rs. 2,50,000 (Rupees Two Lakhs Fifty Thousand) per annum. An authorized Revenue Officer Income Certificate is mandatory.
1.2 Academic Merit: The applicant must have secured a minimum CGPA of 7.50 in the preceding academic year with no active backlogs.

2. SCHOLARSHIP VALUE AND BENEFIT DISBURSEMENT
2.1 Selected scholars receive a direct tuition fee waiver of 50% of the annual tuition fee or Rs. 40,000 per annum, whichever is lower.
2.2 The scholarship amount is credited directly against institutional tuition dues; cash disbursements are strictly prohibited.

3. RENEWAL POLICY
3.1 Scholarships are renewed annually provided the recipient maintains a minimum CGPA of 7.50, has >= 80% attendance, and has not faced disciplinary action."""
    },
    {
        "document_id": "DOC-SCHOL-002",
        "title": "Post-Matric and State Scholarship Portal Application Manual",
        "category": "scholarships",
        "language": "en",
        "file_name": "DOC-SCHOL-002.txt",
        "folder": "scholarships",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "State Scholarship Portal (SSP / NSP) registration guidelines, e-attestation procedures, and mandatory document lists.",
        "content": """================================================================================
POST-MATRIC AND STATE SCHOLARSHIP PORTAL APPLICATION MANUAL
Document ID: DOC-SCHOL-002 | Category: Scholarships | Version: 1.4
================================================================================

1. STATE SCHOLARSHIP PORTAL (SSP) REGISTRATION
1.1 All SC, ST, OBC, and EWS category students seeking government post-matric fee concessions must create a student account on the State Scholarship Portal (SSP) using their Aadhaar-linked mobile number.

2. MANDATORY VERIFICATION DOCUMENTS
2.1 Required documentation:
    a) Valid Caste and Income Certificate with 17-digit RD number.
    b) Aadhaar-linked Nationalized Bank Passbook copy.
    c) Previous semester marks cards / grade transcripts.
    d) Institutional Fee Receipt and Bonafide Certificate issued by the Registrar.

3. E-ATTESTATION DESK
3.1 The Institutional E-Attestation Officer verifies uploaded documents within five (5) days of submission on the portal."""
    },
    {
        "document_id": "DOC-SCHOL-003",
        "title": "Special Tuition Fee Concession for Differently Abled and Single Girl Child",
        "category": "scholarships",
        "language": "en",
        "file_name": "DOC-SCHOL-003.txt",
        "folder": "scholarships",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Tuition fee discounts for Persons with Disabilities (PwD) and Single Girl Child affirmative action scheme.",
        "content": """================================================================================
SPECIAL TUITION FEE CONCESSION FOR DIFFERENTLY ABLED AND SINGLE GIRL CHILD
Document ID: DOC-SCHOL-003 | Category: Scholarships | Version: 1.1
================================================================================

1. DIFFERENTLY ABLED (PwD) FEE CONCESSION
1.1 Students with benchmark disability of 40% or more (as certified by a District Medical Board) are eligible for a 75% tuition fee waiver throughout the program duration.

2. SINGLE GIRL CHILD EMPOWERMENT SCHEME
2.1 A female student who is the single child in her family is eligible for an annual institutional scholarship of Rs. 25,000 upon submitting a sworn family magistrate affidavit."""
    },
    {
        "document_id": "DOC-SCHOL-004",
        "title": "Sports Excellence and Cultural Achievement Scholarship Bylaws",
        "category": "scholarships",
        "language": "en",
        "file_name": "DOC-SCHOL-004.txt",
        "folder": "scholarships",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Financial incentives for All-India Inter-University sports medalists and national cultural competition winners.",
        "content": """================================================================================
SPORTS EXCELLENCE AND CULTURAL ACHIEVEMENT SCHOLARSHIP BYLAWS
Document ID: DOC-SCHOL-004 | Category: Scholarships | Version: 1.0
================================================================================

1. INTER-UNIVERSITY SPORTS SCHOLARSHIP
1.1 Gold Medalists at AIU (All-India Inter-University) or National Games: 100% Tuition Fee Waiver + Free Hostel Lodging.
1.2 Silver / Bronze Medalists: 50% Tuition Fee Waiver.
1.3 State-Level Champions representing the university: Rs. 15,000 one-time cash incentive."""
    },

    # 5. Hostel & Campus Life
    {
        "document_id": "DOC-HOST-001",
        "title": "Campus Residential Hostel Rules and Disciplinary Code 2024",
        "category": "hostel",
        "language": "en",
        "file_name": "DOC-HOST-001.txt",
        "folder": "hostel",
        "file_type": "txt",
        "expected_page_count": 3,
        "description": "Hostel residency terms, curfew timings (9:00 PM), guest restrictions, electrical appliance policies, and disciplinary penalties.",
        "content": """================================================================================
CAMPUS RESIDENTIAL HOSTEL RULES AND DISCIPLINARY CODE 2024
Document ID: DOC-HOST-001 | Category: Hostel | Version: 2.2
================================================================================

1. HOSTEL ADMISSION & ROOM ALLOTMENT
1.1 Hostel accommodation is allocated on a merit-cum-distance basis for one academic year at a time.
1.2 Room swapping or unauthorized subletting of beds is strictly forbidden and results in immediate cancellation of hostel residency.

2. CURFEW TIMINGS AND BIOMETRIC IN-OUT GATING
2.1 All resident students must return to the hostel premises before 9:00 PM on weekdays and 9:30 PM on weekends.
2.2 Biometric entry scanners operate at all hostel gates. Failure to register entry before curfew generates an automated SMS alert to parents/guardians.
2.3 Night out passes must be requested through the hostel portal at least twenty-four (24) hours in advance with parent email authorization.

3. PROHIBITED ITEMS AND DISCIPLINARY SANCTIONS
3.1 Possession or consumption of alcohol, tobacco products, narcotics, e-cigarettes, or intoxicating substances is strictly prohibited on campus. Violation results in immediate hostel expulsion, suspension from classes, and referral to the Disciplinary Board.
3.2 High-wattage electrical appliances (heaters, immersion rods, induction cooktops) are banned in student rooms due to fire safety regulations."""
    },
    {
        "document_id": "DOC-HOST-002",
        "title": "Hostel Fee Structure, Caution Deposit & Refund Policy",
        "category": "hostel",
        "language": "en",
        "file_name": "DOC-HOST-002.txt",
        "folder": "hostel",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Room rent rates, mess advance, refundable caution deposit (Rs. 10,000), and refund calculation upon mid-year room surrender.",
        "content": """================================================================================
HOSTEL FEE STRUCTURE, CAUTION DEPOSIT & REFUND POLICY
Document ID: DOC-HOST-002 | Category: Hostel | Version: 1.3
================================================================================

1. ANNUAL HOSTEL FEE SCHEDULE
1.1 Double Occupancy (Attached Bath): Rs. 75,000 per annum (Room Rent & Maintenance) + Mess Advance.
1.2 Triple Occupancy (Standard): Rs. 55,000 per annum.
1.3 Refundable Caution Deposit: Rs. 10,000 (one-time deposit payable at admission).

2. HOSTEL WITHDRAWAL AND REFUND MATRIX
2.1 Withdrawal before occupying room: 100% refund of room rent minus Rs. 1,000 administrative charge.
2.2 Withdrawal within 30 days of semester start: 50% room rent refund.
2.3 Withdrawal after 30 days: No room rent refund; unused mess advance and caution deposit refunded in full after clearance of dues."""
    },
    {
        "document_id": "DOC-HOST-003",
        "title": "Campus Anti-Ragging Regulations and Grievance Redressal Committee",
        "category": "hostel",
        "language": "en",
        "file_name": "DOC-HOST-003.txt",
        "folder": "hostel",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Zero-tolerance anti-ragging statutory regulations, reporting hotlines, Anti-Ragging Squad patrolling, and disciplinary actions.",
        "content": """================================================================================
CAMPUS ANTI-RAGGING REGULATIONS AND GRIEVANCE REDRESSAL COMMITTEE
Document ID: DOC-HOST-003 | Category: Hostel | Version: 2.0
================================================================================

1. ZERO TOLERANCE ANTI-RAGGING POLICY
1.1 Ragging in any form (physical, psychological, verbal, online harassment) is a cognizable criminal offense under UGC / AICTE Regulations and State enactments.
1.2 The institution maintains a Zero Tolerance Policy towards ragging on campus, residential hostels, and college transport.

2. COMPLAINT LODGING AND EMERGENCY HELPLINES
2.1 24x7 Anti-Ragging Institutional Toll-Free Helpline: 1800-425-0099.
2.2 Written complaints may be dropped in the anonymous Anti-Ragging Grievance Boxes placed in every department and hostel foyer or emailed to antiragging@institution.edu."""
    },
    {
        "document_id": "DOC-HOST-004",
        "title": "Hostel Mess Timings, Nutrition Committee and Guest Meal Rules",
        "category": "hostel",
        "language": "en",
        "file_name": "DOC-HOST-004.txt",
        "folder": "hostel",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Dining hours, food safety inspections, Student Mess Committee responsibilities, and guest meal token charges.",
        "content": """================================================================================
HOSTEL MESS TIMINGS, NUTRITION COMMITTEE AND GUEST MEAL RULES
Document ID: DOC-HOST-004 | Category: Hostel | Version: 1.0
================================================================================

1. DINING SERVICE HOURS
1.1 Breakfast : 07:30 AM to 09:15 AM
1.2 Lunch     : 12:30 PM to 02:15 PM
1.3 Evening Tea: 05:00 PM to 06:00 PM
1.4 Dinner    : 07:45 PM to 09:30 PM

2. GUEST MEAL COUPOINS
2.1 Parents and authorized guests may dine in the student mess upon purchasing a Guest Meal Token from the Hostel Warden's Office (Breakfast: Rs. 60, Lunch/Dinner: Rs. 100)."""
    },

    # 6. Placement & Career Services
    {
        "document_id": "DOC-PLACE-001",
        "title": "Campus Placement Eligibility and One-Student-One-Job Policy 2024",
        "category": "placements",
        "language": "en",
        "file_name": "DOC-PLACE-001.txt",
        "folder": "placements",
        "file_type": "txt",
        "expected_page_count": 3,
        "description": "Placement registration criteria (60% / 6.5 CGPA), One-Offer policy, Dream Company upgrade rules, and debarment conditions.",
        "content": """================================================================================
CAMPUS PLACEMENT ELIGIBILITY AND ONE-STUDENT-ONE-JOB POLICY 2024
Document ID: DOC-PLACE-001 | Category: Placements | Version: 2.1
================================================================================

1. PLACEMENT REGISTRATION ELIGIBILITY
1.1 To register with the Department of Training & Placements (T&P), a candidate must possess a minimum cumulative CGPA of 6.50 (or 60% aggregate) across all completed semesters with no standing backlogs.
1.2 A minimum attendance of eighty-five percent (85%) in all pre-placement training sessions and soft-skill workshops is mandatory to sit for campus recruitment drives.

2. ONE-STUDENT-ONE-JOB POLICY
2.1 Once a student receives a formal job offer (Offer Letter / Letter of Intent) from a participating company, they are deemed 'Placed' and shall not participate in subsequent drives.

3. DREAM COMPANY UPGRADE EXCEPTION
3.1 A placed student is permitted one (1) additional chance to interview for a 'Dream / Super-Dream Company' if the offered Cost-to-Company (CTC) is at least 2.0x (double) their initial placement package (or exceeding Rs. 10.0 LPA).

4. DEBARMENT AND DISCIPLINARY PENALTIES
4.1 Registering for a recruitment drive and failing to appear for the online test / technical interview without prior written permission results in debarment from the next two (2) recruitment drives."""
    },
    {
        "document_id": "DOC-PLACE-002",
        "title": "Mandatory Industry Internship & Project Work Guidelines",
        "category": "placements",
        "language": "en",
        "file_name": "DOC-PLACE-002.txt",
        "folder": "placements",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Full-semester internship eligibility, No Objection Certificate (NOC) requirements, stipend reporting, and project viva voce.",
        "content": """================================================================================
MANDATORY INDUSTRY INTERNSHIP & PROJECT WORK GUIDELINES
Document ID: DOC-PLACE-002 | Category: Placements | Version: 1.4
================================================================================

1. FULL-SEMESTER INDUSTRY INTERNSHIP (FINAL SEMESTER)
1.1 Students in their final semester (MCA 4th Semester) may undertake a full-time, six-month industry internship in lieu of on-campus elective courses, subject to securing a placement offer or official internship stipend letter.

2. NO OBJECTION CERTIFICATE (NOC) ISSUANCE
2.1 An NOC is issued by the T&P Cell only after verifying that the candidate has completed all prerequisite coursework and has a minimum CGPA of 6.75.
2.2 Fortnightly progress reports certified by the external industry mentor must be submitted to the institutional faculty guide."""
    },
    {
        "document_id": "DOC-PLACE-003",
        "title": "Placement Drive Code of Conduct, Dress Code and Attendance Bylaws",
        "category": "placements",
        "language": "en",
        "file_name": "DOC-PLACE-003.txt",
        "folder": "placements",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Formal business attire mandates, resume verification protocols, punctual reporting, and interview etiquette.",
        "content": """================================================================================
PLACEMENT DRIVE CODE OF CONDUCT, DRESS CODE AND ATTENDANCE BYLAWS
Document ID: DOC-PLACE-003 | Category: Placements | Version: 1.1
================================================================================

1. PROFESSIONAL DRESS CODE MANDATES
1.1 All candidates appearing for aptitude tests, group discussions, and technical/HR interviews must strictly adhere to formal corporate attire (Formal shirt, trousers, tie, blazer, and formal shoes).

2. RESUME ACCURACY & AUTHENTICATION
2.1 All resumes submitted through the T&P portal must be verified by the Department Placement Coordinator. Falsification of marks, projects, or certifications leads to permanent debarment from campus placements."""
    },
    {
        "document_id": "DOC-PLACE-004",
        "title": "Career Guidance, Skill Training & Higher Education Advisory Circular",
        "category": "placements",
        "language": "en",
        "file_name": "DOC-PLACE-004.txt",
        "folder": "placements",
        "file_type": "txt",
        "expected_page_count": 2,
        "description": "Competitive exam coaching (GATE / GRE / CAT), free certification sponsorship, and alumni mentorship programs.",
        "content": """================================================================================
CAREER GUIDANCE, SKILL TRAINING & HIGHER EDUCATION ADVISORY CIRCULAR
Document ID: DOC-PLACE-004 | Category: Placements | Version: 1.0
================================================================================

1. HIGHER EDUCATION AND COMPETITIVE EXAM SUPPORT
1.1 The Centre for Career Advisory conducts weekend coaching for GATE, GRE, CAT, and UGC-NET examinations free of charge for enrolled students.

2. INDUSTRY CERTIFICATION SPONSORSHIP
2.1 The institution subsidizes up to 50% of the examination fee for approved professional cloud/AI certifications (AWS, Microsoft Azure, Google Cloud, Oracle) for students maintaining a CGPA >= 7.50."""
    }
]

def generate_corpus():
    manifest_entries = []
    print("Generating 24 institutional policy documents...")

    for doc in DOCUMENTS:
        cat_dir = RAW_DIR / doc["folder"]
        cat_dir.mkdir(parents=True, exist_ok=True)
        file_path = cat_dir / doc["file_name"]

        # Write text content
        file_path.write_text(doc["content"].strip(), encoding="utf-8")

        # Compute SHA-256 hash
        sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        rel_path = f"data/raw/{doc['folder']}/{doc['file_name']}"

        manifest_entry = {
            "document_id": doc["document_id"],
            "title": doc["title"],
            "category": doc["category"],
            "language": doc["language"],
            "file_path": rel_path,
            "source_type": "synthetic_institutional_policy",
            "source_reference": "Authored for MCA Academic Demonstration based on VTU/AICTE regulatory norms",
            "license_or_usage": "Academic Demonstration & Research Use Only",
            "version": "1.0",
            "file_type": doc["file_type"],
            "expected_page_count": doc["expected_page_count"],
            "checksum_sha256": sha256,
            "description": doc["description"],
            "is_active": True
        }
        manifest_entries.append(manifest_entry)
        print(f"  [+] Created: {rel_path} ({sha256[:12]}...)")

    manifest_file = RAW_DIR / "corpus_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)

    print(f"\n[+] Created manifest at {manifest_file} with {len(manifest_entries)} documents.")

if __name__ == "__main__":
    generate_corpus()
