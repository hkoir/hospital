


SERVICE_TYPE_CHOICES = [
    ('Consultation', 'Consultation'),
    ('Followup_Consultation', 'Follow-up Consultation'),
    ('Lab_Test', 'Lab / Diagnostic Test'),
    ('Radiology', 'Radiology / Imaging (X-ray, USG, CT, MRI)'),
    ('ECG', 'ECG / EEG / EMG'),
    ('Procedure', 'Minor Procedures'),
    ('Operation_Theatre', 'Operation Theatre Charges'),
    ('Surgery', 'Surgical Charges'),
    ('Ward_Bed', 'Ward / Bed Charge'),
    ('Cabin', 'Cabin Charge'),
    ('ICU', 'ICU Charges'),
    ('CCU', 'CCU Charges'),
    ('NICU', 'NICU Charges'),
    ('PICU', 'PICU Charges'),
    ('OT_Consumables', 'OT Consumables'),
     ('OT', 'Operation Theatre'),
    ('Medicine_Sale', 'Medicine / Pharmacy Sale'),
    ('Injection', 'Injection / IV / Medication Service'),
    ('Nursing', 'Nursing Service Charge'),
    ('Emergency', 'Emergency Service'),
    ('Ambulance', 'Ambulance Charge'),
    ('Dialysis', 'Dialysis Charge'),
    ('Physiotherapy', 'Physiotherapy'),
    ('Blood_Bank', 'Blood Bank Services'),
    ('Vaccination', 'Vaccination'),
    ('Dental', 'Dental Services'),
    ('ENT', 'ENT Procedures'),
    ('Eye', 'Eye / Ophthalmology Procedures'),
    ('Consultation_Discount', 'Consultation Discount'),
    ('Hospital_Package', 'Hospital Packages'),
]





SERVICE_TYPE_TO_REFERRAL_MAP = {
    # Consultation
    "Consultation": "consultation",
    "Followup_Consultation": "consultation",
    "Consultation_Discount": "consultation",
    # Emergency
    "Emergency": "emergency",

    # Lab
    "Lab_Test": "lab",
    "Radiology": "lab",
    "ECG": "lab",
    "Procedure": "lab",
    # Medicine
    "Medicine_Sale": "medicine",
    "Injection":"medicine",
    # Ward
    "Ward_Bed": "ward",
    "Cabine": "ward",
    "ICU": "ward",
    "CCU": "ward",
    "NICU": "ward",
    "PICU": "ward",
    # OT / Surgery
    "Operation_Theatre": "surgery",
    "Surgery": "surgery",
    "OT":"ot",
    "OT_Consumables":"surgery",
    # Misc   
    'Blood_Bank':"other",
    'Vaccination':"other",
    'Dental':"other",
    'ENT':"other",
    'Eye':"other",
    'Hospital_Package':"other",
    'Nursing':"other",
    'Dialysis':"other",
    'Ambulance':"other",
    'Physiotherapy':"physio",
}




SERVICE_REFERRAL_TYPES = [
        ('consultation', 'Consultation'),
        ('lab', 'Lab Test'),
        ('surgery', 'Surgery'),
        ('ot', 'Operation Theatre'),
        ('emergency', 'Emergency visit'),
        ('physio', 'Physiotherapy'),
        ('ward', 'ward bill'),
        ('medicine', 'medicine bill'),
        ('all', 'All services'),
        ('other', 'Other')
    ]

