"""
generate_placeholder_others.py

Generates clearly-labeled PLACEHOLDER entries for the 7 categories HRSA
doesn't cover (food, shelter, legal, financial, childcare, mental_health,
other) so you have a full ~200-row dataset to test the pipeline with today.

These are NOT real organizations - every row is prefixed "[SAMPLE]" and the
description says so explicitly, so nobody mistakes them for verified data.
Before a real demo, replace these with actual local organizations (Step 2/3b
in the README - 211.org, city health dept, food bank locator, etc.).

Usage:
    python scripts/generate_placeholder_others.py
Writes data/resources_placeholder_others.csv
"""

import random
import pandas as pd

random.seed(42)  # reproducible output

OUTPUT_PATH = "data/resources_placeholder_others.csv"

# Center the placeholder addresses/coordinates near Houston, TX so distance
# filtering has something sensible to work with alongside the real HRSA rows.
CENTER_LAT, CENTER_LNG = 29.7604, -95.3698

STREET_NAMES = [
    "Main St", "Oak Ave", "Elm St", "Bissonnet St", "Westheimer Rd", "Fondren Rd",
    "Cullen Blvd", "Airline Dr", "Telephone Rd", "Gessner Rd", "Antoine Dr",
    "Broadway St", "Wayside Dr", "Griggs Rd", "Lockwood Dr", "Hillcroft Ave",
]

HOURS_OPTIONS = [
    "Mon-Fri 09:00-17:00",
    "Mon-Fri 08:00-18:00",
    "24/7",
    "Tue,Thu 09:00-13:00",
    "Mon-Sat 08:00-16:00",
    "Mon-Fri 10:00-19:00",
]

# Each tuple: (category, archetype name, description template, eligibility text)
ARCHETYPES = [
    ("food", "Community Food Pantry", "Weekly grocery distribution including fresh produce and canned goods for families in need.", "No documentation required; once per week per household"),
    ("food", "Regional Food Bank", "Large-scale food distribution center serving individuals and partner pantries across the metro area.", "Open to all residents; ID recommended not required"),
    ("food", "Mobile Food Pantry", "Rotating mobile food distribution bringing groceries directly to underserved neighborhoods.", "No documentation required; check schedule for rotating locations"),
    ("food", "Senior Meal Delivery Program", "Home-delivered meals for homebound seniors who can't shop or cook for themselves.", "Ages 60+; homebound status required"),
    ("food", "School Backpack Meal Program", "Weekend food backpacks for children who rely on school meals during the week.", "School-age children enrolled in a partner school district"),
    ("food", "Community Fridge Network", "Free-access refrigerators stocked with perishable food, available any time with no sign-up.", "Free; open to anyone; no questions asked"),
    ("food", "Church Food Pantry", "Weekly food pantry operated by a local congregation, open to the surrounding community.", "No documentation required; open to all"),
    ("food", "Holiday Meal Assistance Program", "Seasonal meal and grocery assistance around major holidays for low-income households.", "Income-based; registration required in advance"),
    ("food", "WIC Nutrition Program Office", "Nutrition assistance, breastfeeding support, and food vouchers for pregnant women, new mothers, and young children.", "Pregnant women, new mothers, or children under 5; income-based"),
    ("food", "Farmers Market Food Voucher Program", "Provides vouchers usable at local farmers markets for fresh produce.", "Income-based; SNAP recipients prioritized"),
    ("food", "Community Garden Food Share", "Volunteer-run garden distributing fresh produce to neighborhood residents.", "Free; open to all"),
    ("food", "Emergency Food Box Program", "One-time emergency food boxes for households facing a sudden crisis.", "Once per household per emergency; ID requested"),
    ("food", "College Campus Food Pantry", "On-campus food pantry for students facing food insecurity.", "Currently enrolled students only"),
    ("food", "Neighborhood Grocery Rescue Program", "Redistributes surplus grocery store food to community members.", "Free; open to all; while supplies last"),

    ("shelter", "Emergency Overnight Shelter", "Overnight emergency shelter beds for individuals and families experiencing homelessness, with meals provided.", "Open to all; families with children given priority"),
    ("shelter", "Family Shelter Program", "Shelter specifically for families with children experiencing homelessness, including case management.", "Families with children under 18"),
    ("shelter", "Youth Emergency Shelter", "Short-term shelter for unaccompanied youth and teens experiencing homelessness.", "Ages 12-24; unaccompanied minors accepted with intake process"),
    ("shelter", "Domestic Violence Safe House", "Confidential emergency shelter for survivors of domestic violence and their children.", "Survivors of domestic violence; confidential intake"),
    ("shelter", "Winter Warming Center", "Seasonal overnight shelter open during cold weather months with beds and hot meals.", "Open to all; seasonal Nov-Mar only"),
    ("shelter", "Transitional Housing Program", "Longer-term supportive housing helping individuals move from homelessness to stability.", "Referral required; program length 6-24 months"),
    ("shelter", "Day Shelter & Resource Center", "Daytime drop-in center offering showers, storage, meals, and case management for people experiencing homelessness.", "Open to all; no overnight beds"),
    ("shelter", "Veteran Housing Program", "Transitional and permanent supportive housing specifically for veterans experiencing homelessness.", "Must be a veteran; discharge status verified at intake"),
    ("shelter", "Rapid Rehousing Program", "Short-term rental assistance and case management to quickly move families out of homelessness.", "Households currently experiencing homelessness; income-based"),
    ("shelter", "Overflow Shelter Network", "Additional shelter capacity activated during extreme weather or capacity emergencies.", "Open to all when activated; call ahead to confirm activation"),
    ("shelter", "Host Home Network for Youth", "Connects homeless youth with vetted host families for temporary housing.", "Ages 18-24; application and screening required"),
    ("shelter", "Recovery Housing Program", "Sober living transitional housing for individuals in recovery from substance use.", "Must be in active recovery; sobriety requirement"),
    ("shelter", "Emergency Hotel Voucher Program", "Short-term hotel vouchers for families in crisis awaiting shelter bed availability.", "Referral through 211 or partner agency required"),
    ("shelter", "LGBTQ+ Youth Shelter Program", "Shelter and support services specifically for LGBTQ+ youth experiencing homelessness.", "Ages 18-24; LGBTQ+ identifying youth"),

    ("legal", "Legal Aid Society", "Free legal representation and advice for low-income residents on housing, eviction defense, and family law matters.", "Household income under 125% federal poverty line"),
    ("legal", "Immigrant Rights Legal Clinic", "Free consultations on immigration status, asylum applications, and family reunification cases.", "No income requirement; appointment preferred"),
    ("legal", "Tenant Rights Hotline", "Free phone consultations for renters facing eviction, unsafe housing conditions, or landlord disputes.", "Free; open to all renters"),
    ("legal", "Family Law Self-Help Clinic", "Monthly walk-in clinic offering free advice on custody, divorce, and child support matters.", "Free; walk-in; no income requirement"),
    ("legal", "Expungement & Record Clearing Clinic", "Free help filing paperwork to clear or seal eligible criminal records.", "Eligibility depends on offense type and time elapsed"),
    ("legal", "Disability Rights Legal Center", "Free legal help with disability benefits denials, accessibility complaints, and discrimination cases.", "Individuals with disabilities; no income requirement"),
    ("legal", "Veterans Legal Clinic", "Free legal assistance for veterans on benefits appeals, discharge upgrades, and housing issues.", "Must be a veteran"),
    ("legal", "Domestic Violence Legal Advocacy Program", "Free legal help obtaining protective orders and navigating family court for survivors of abuse.", "Survivors of domestic violence; free and confidential"),
    ("legal", "Small Claims Help Desk", "Free guidance navigating the small claims court process, no attorney required.", "Free; open to anyone with a small claims matter"),
    ("legal", "Elder Law Legal Clinic", "Free legal consultations for seniors on wills, guardianship, and elder abuse matters.", "Ages 60+"),
    ("legal", "Consumer Debt Legal Clinic", "Free legal help responding to debt collection lawsuits and understanding consumer rights.", "Income-based; no cost consultation"),
    ("legal", "Employment Rights Legal Clinic", "Free consultations on wage theft, wrongful termination, and workplace discrimination.", "Open to all workers; income-based for full representation"),
    ("legal", "Guardianship & Custody Help Center", "Free help navigating guardianship and custody paperwork for kinship caregivers.", "Kinship caregivers raising a relative's child"),
    ("legal", "Know-Your-Rights Legal Workshop Series", "Free recurring community workshops explaining tenant, immigration, and consumer rights.", "Free; open to the public; no registration required"),

    ("financial", "Financial Empowerment Center", "Free one-on-one financial counseling covering budgeting, debt reduction, and credit repair.", "Free; no income requirement; appointment recommended"),
    ("financial", "Emergency Utility Assistance Program", "One-time financial assistance to prevent utility shutoff for qualifying low-income households.", "Income under 150% federal poverty line; shutoff notice required"),
    ("financial", "Rent Relief Fund", "Emergency rental assistance grants for households at risk of eviction due to job loss or medical hardship.", "Proof of income loss or hardship required"),
    ("financial", "Job & Career Center", "Free job placement, resume help, and career counseling services, including for those with unstable housing.", "Free; open to all residents"),
    ("financial", "Nonprofit Credit Counseling Program", "Free and low-cost credit counseling, debt management plans, and financial literacy classes.", "Free consultation; sliding scale for ongoing services"),
    ("financial", "Free Tax Preparation Program (VITA)", "IRS-certified volunteers provide free tax preparation for low- to moderate-income filers.", "Household income under ~$67,000; seasonal Jan-Apr"),
    ("financial", "Benefits Enrollment Center", "Free help applying for SNAP, Medicaid, and other public benefits programs.", "Free; open to all; income verification may be required for benefits"),
    ("financial", "Emergency Cash Assistance Program", "One-time emergency cash grants for households facing a sudden financial crisis.", "Income-based; documentation of crisis required"),
    ("financial", "First-Time Homebuyer Assistance Program", "Down payment assistance and homebuyer education classes for qualifying first-time buyers.", "First-time buyers; income limits apply"),
    ("financial", "Small Business Microloan Program", "Microloans and free business counseling for low-income entrepreneurs.", "Must complete business counseling; income-based loan terms"),
    ("financial", "Debt Management Program", "Structured debt repayment plans negotiated with creditors on the client's behalf.", "Free enrollment consultation; program fee may apply"),
    ("financial", "Bank On Program - Free Checking Access", "Helps unbanked residents open low-fee, no-overdraft checking accounts at partner banks.", "Free; open to unbanked/underbanked residents"),
    ("financial", "Disaster Financial Recovery Center", "Financial counseling and emergency grants for households recovering from a natural disaster.", "Must be in a declared disaster area"),
    ("financial", "Senior Financial Exploitation Helpline", "Free consultation for seniors who suspect they've been targeted by financial scams or exploitation.", "Ages 60+; free and confidential"),

    ("childcare", "Childcare Subsidy Program", "Helps low-income families access subsidized childcare slots at partner daycare centers citywide.", "Income under 185% federal poverty line; must be employed or in school"),
    ("childcare", "Parent Resource Center", "Free parenting classes, childcare referrals, and diaper distribution for new and expecting parents.", "Free; open to all parents and caregivers"),
    ("childcare", "Early Head Start Program", "Free early childhood education and family support services for infants, toddlers, and pregnant women.", "Income-based; pregnant women and children under 3"),
    ("childcare", "Diaper Bank", "Free diapers and baby wipes distributed monthly to families in need.", "Household with children under 3; income-based"),
    ("childcare", "Home Visiting Program for New Parents", "Free in-home visits from a nurse or parent educator for first-time parents.", "First-time parents; enrollment during pregnancy or infancy preferred"),
    ("childcare", "After-School Enrichment Program", "Free after-school care and tutoring for school-age children of working parents.", "School-age children; parent must be employed or in school"),
    ("childcare", "Teen Parent Support Program", "Parenting classes, childcare, and educational support specifically for teen parents.", "Parents under age 20"),
    ("childcare", "Respite Care Program for Caregivers", "Short-term free childcare to give parents and caregivers of children with disabilities a break.", "Families of children with disabilities or special needs"),
    ("childcare", "Family Resource Center", "One-stop center connecting families to childcare, health, and housing resources.", "Free; open to all families"),
    ("childcare", "Childcare Provider Referral Line", "Free phone service helping parents find licensed childcare providers in their area.", "Free; open to all"),
    ("childcare", "Kinship Caregiver Support Program", "Support groups and financial assistance for grandparents and relatives raising children.", "Kinship caregivers raising a relative's child"),
    ("childcare", "Bilingual Early Childhood Program", "Free bilingual early childhood education classes for children ages 2-5.", "Income-based; ages 2-5"),
    ("childcare", "Foster & Adoptive Parent Support Program", "Training, respite care, and support groups for foster and adoptive families.", "Licensed foster or adoptive parents"),
    ("childcare", "Special Needs Childcare Navigator", "Helps families find childcare providers equipped to support children with disabilities.", "Families of children with disabilities"),

    ("mental_health", "Crisis Counseling Hotline", "24/7 phone counseling for mental health crises including suicide prevention and emotional support.", "Free; open to anyone; no eligibility requirements"),
    ("mental_health", "Sliding Scale Therapy Collective", "Group of independent therapists offering sliding-scale individual therapy for adults.", "Sliding scale fee; no insurance required"),
    ("mental_health", "Youth Counseling Center", "Counseling services specifically for children and teenagers dealing with anxiety and family issues.", "Ages 5-18; parental consent required; sliding scale"),
    ("mental_health", "Substance Use Support Group Network", "Free peer support groups for individuals in recovery from substance use.", "Free; open to anyone in or seeking recovery"),
    ("mental_health", "Grief & Loss Counseling Program", "Free and low-cost individual and group counseling for those experiencing grief.", "Sliding scale; open to all ages"),
    ("mental_health", "Veterans Mental Health Program", "Counseling and support groups specifically for veterans dealing with PTSD, anxiety, or depression.", "Must be a veteran"),
    ("mental_health", "Peer Support Warmline", "Non-crisis phone support staffed by people with lived mental health experience.", "Free; open to anyone; not for emergencies"),
    ("mental_health", "Community Mental Health Center", "Outpatient mental health services including therapy and medication management on a sliding scale.", "Sliding scale; no insurance required"),
    ("mental_health", "Telehealth Counseling Program", "Free or low-cost video counseling sessions for residents in areas with limited in-person access.", "Sliding scale; internet access required"),
    ("mental_health", "LGBTQ+ Affirming Counseling Center", "Therapy services from clinicians trained in LGBTQ+ affirming care.", "Sliding scale; open to all ages"),
    ("mental_health", "Postpartum Support Program", "Free counseling and support groups for new parents experiencing postpartum depression or anxiety.", "New parents; free and confidential"),
    ("mental_health", "School-Based Mental Health Program", "On-campus counseling services for students during the school day.", "Currently enrolled students; parental consent required"),
    ("mental_health", "Trauma Recovery Center", "Specialized counseling for survivors of violent crime and traumatic events.", "Survivors of violent crime; free services often available"),
    ("mental_health", "Faith-Based Counseling Center", "Low-cost counseling integrating mental health support with spiritual care, open to all faiths.", "Sliding scale; open to all, regardless of faith background"),

    ("other", "Senior Services Center", "Meal delivery, transportation assistance, and social programs for adults 60 and older.", "Ages 60+; free or low-cost depending on program"),
    ("other", "Veterans Resource Hub", "One-stop center connecting veterans to benefits, housing assistance, job placement, and counseling.", "Must be a veteran or active military family member"),
    ("other", "Disability Resource Center", "Independent living skills training, equipment loans, and advocacy for people with disabilities.", "Individuals with disabilities; no income requirement"),
    ("other", "Refugee Resettlement Agency", "Case management, English classes, and job placement help for newly arrived refugees.", "Must have refugee or asylee status"),
    ("other", "Reentry Support Program", "Case management, job placement, and housing help for people recently released from incarceration.", "Must have been recently incarcerated"),
    ("other", "Transportation Assistance Program", "Free or low-cost rides to medical appointments for people without reliable transportation.", "Income-based; medical appointments prioritized"),
    ("other", "Interpreter & Translation Services", "Free interpretation services for non-English speakers accessing local health and social services.", "Free; open to anyone needing language access"),
    ("other", "Community Resource Navigator Hotline", "Phone service that helps callers figure out which local program fits their specific need.", "Free; open to anyone; similar to 211"),
    ("other", "Clothing Closet", "Free clothing, shoes, and interview attire for individuals and families in need.", "No documentation required; open to all"),
    ("other", "Computer & Internet Access Center", "Free computer and internet access, plus digital literacy classes.", "Free; open to all; ID may be requested for equipment loans"),
    ("other", "Prescription Eyeglasses Assistance Program", "Free or low-cost eye exams and prescription glasses for uninsured residents.", "No insurance required; income-based discount on glasses"),
    ("other", "Home Repair Assistance Program", "Free minor home repairs and accessibility modifications for low-income homeowners.", "Homeowners; income-based; seniors and people with disabilities prioritized"),
    ("other", "Pet Food & Vet Care Assistance Program", "Free pet food and low-cost veterinary care for low-income pet owners.", "Income-based; proof of pet ownership"),
    ("other", "Community ID Program", "Helps residents without government ID obtain a recognized community identification card.", "Open to all residents, including those without other forms of ID"),
]


def jitter(base, spread=0.15):
    return round(base + random.uniform(-spread, spread), 6)


def build_rows():
    rows = []
    next_id = 2000
    for category, archetype_name, desc_template, eligibility in ARCHETYPES:
        street_num = random.randint(100, 9999)
        street = random.choice(STREET_NAMES)
        address = f"{street_num} {street}, Houston, TX, {random.randint(77001, 77099)}"
        lat = jitter(CENTER_LAT)
        lng = jitter(CENTER_LNG)
        hours = random.choice(HOURS_OPTIONS)
        phone = f"713-{random.randint(200,999)}-{random.randint(1000,9999)}"
        walk_in = random.choice([True, False])

        rows.append({
            "id": next_id,
            "name": f"[SAMPLE] {archetype_name}",
            "category": category,
            "description": (
                f"{desc_template} "
                "PLACEHOLDER ENTRY — this is a sample used to fill out the dataset for testing; "
                "replace with a real, verified local organization before using this in a live demo."
            ),
            "eligibility": eligibility,
            "address": address,
            "lat": lat,
            "lng": lng,
            "hours": hours,
            "phone": phone,
            "website": "",
            "walk_in": walk_in,
            "last_verified": pd.Timestamp.today().strftime("%Y-%m-%d"),
        })
        next_id += 1
    return rows


if __name__ == "__main__":
    rows = build_rows()
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} placeholder rows -> {OUTPUT_PATH}")
    print(df["category"].value_counts())
