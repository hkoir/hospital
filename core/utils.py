

LOCATION_CHOICES=[
    ('',''),
    ('DHAKA','Dhaka'),
    ('CHITTAGONG','Chittagong'),
    ('KHULNA','Khulna'),
    ('RAJSHAHI','Rajshahi'),
    ('SYLHET','Sylhet'),
    ('BAGURA','Bagura'),
    ('BARISAL','Barisal'),
    ('MYMENSINGH','Mymensingh'),
    ('Cumilla','Cumilla')
]


DEPARTMENT_CHOICES = [
    ('', ''),
    ('Engineering', 'Engineering'),
    ('Technology', 'Technology'),
    ('Operations', 'Operations'),
    ('Planning', 'Planning'),
    ('Information Technology', 'Information Technology'),
    ('Customer Support', 'Customer Support'),  # Fixed typo ("Supper" -> "Support")
    ('Research & Development', 'Research & Development'),
    ('Legal & Compliance', 'Legal & Compliance'),
    ('SCM', 'Supply Chain Management (SCM)'),  # Expanded abbreviation for clarity
    ('Logistics', 'Logistics'),
    ('Quality Assurance', 'Quality Assurance'),
    ('Business Control', 'Business Control'),
    ('Design and Creative', 'Design and Creative'),
    ('Public Relations', 'Public Relations'),
    ('Corporate Strategy and Planning', 'Corporate Strategy and Planning'),
    ('Marketing', 'Marketing'),  # Fixed typo ("Marketting" -> "Marketing")
    ('Sales', 'Sales'),
    ('Finance', 'Finance'),
    ('Accounting', 'Accounting'),
    ('Production', 'Production'),
    ('Admin', 'Admin'),
    ('HR', 'Human Resources'),  # Expanded for clarity
    ('Training and Development', 'Training and Development'),
    ('Event Management', 'Event Management'),
    ('Environmental, Social, and Governance (ESG)', 'Environmental, Social, and Governance (ESG)'),  # Improved name
    ('Health and Safety', 'Health and Safety'),  # Removed duplicate
    ('Business Development', 'Business Development'),  # Fixed naming convention
    ('Facilities Management', 'Facilities Management'),
    ('Investor Relations', 'Investor Relations'),  # Added missing comma
    ('Medical Healthcare', 'Medical Healthcare'),  # Fixed typo ("Healthcar" -> "Healthcare")
    ('Procurement', 'Procurement'),  # New addition
    ('Security', 'Security'),  # New addition
    ('Learning and Development', 'Learning and Development'),  # New addition
    ('Corporate Communications', 'Corporate Communications'),  # New addition
    ('Sustainability', 'Sustainability'),  # New addition
]

POSITION_CHOICES = [
    ('', ''),
    
    # Executive Leadership
    ('Chairman', 'Chairman'),
    ('MD', 'MD'),  # Managing Director
    ('CEO', 'CEO'),  # Chief Executive Officer
    ('CFO', 'CFO'),  # Chief Financial Officer
    ('COO', 'COO'),  # Chief Operating Officer
    ('CTO', 'CTO'),  # Chief Technology Officer
    ('CIO', 'CIO'),  # Chief Information Officer
    ('CHRO', 'CHRO'),  # Chief Human Resources Officer
    ('CMO', 'CMO'),  # Chief Marketing Officer
    ('CSO', 'CSO'),  # Chief Strategy Officer
    ('CLO', 'CLO'),  # Chief Legal Officer
    ('CDO', 'CDO'),  # Chief Data Officer

    # Directors and Department Heads
    ('Director', 'Director'),
    ('Executive Director', 'Executive Director'),
    ('HOD', 'HOD'),  # Head of Department
    ('AVP', 'AVP'),  # Assistant Vice President
    ('VP', 'VP'),  # Vice President
    ('Senior VP', 'Senior VP'),
    ('General Manager', 'General Manager'),
    ('DGM', 'DGM'),  # Deputy General Manager
    ('GM', 'GM'),  # General Manager
    ('SrGM', 'SrGM'),  # Senior General Manager

    # Managers and Supervisors
    ('Manager', 'Manager'),
    ('Sr.Manager', 'Sr.Manager'),
    ('Assistant Manager', 'Assistant Manager'),
    ('Team Lead', 'Team Lead'),
    ('Supervisor', 'Supervisor'),
    ('Coordinator', 'Coordinator'),
    ('HSS_manager', 'HSS_manager'),  # Could be Health, Safety & Security Manager

    # Specialists and Officers
    ('Specialist', 'Specialist'),
    ('Senior Specialist', 'Senior Specialist'),
    ('Officer', 'Officer'),
    ('Executive Officer', 'Executive Officer'),
    ('Project Manager', 'Project Manager'),
    ('Program Manager', 'Program Manager'),
    ('Consultant', 'Consultant'),
    ('Advisor', 'Advisor'),

    # Technical Roles
    ('Engineer', 'Engineer'),
    ('Senior Engineer', 'Senior Engineer'),
    ('Software Developer', 'Software Developer'),
    ('System Analyst', 'System Analyst'),
    ('Data Scientist', 'Data Scientist'),
    ('IT Specialist', 'IT Specialist'),
    ('Architect', 'Architect'),

    # Administrative and Support Roles
    ('Driver', 'Driver'),
    ('Peon', 'Peon'),
    ('Office Assistant', 'Office Assistant'),
    ('Receptionist', 'Receptionist'),
    ('Clerk', 'Clerk'),
    ('Secretary', 'Secretary'),
    ('General Staff', 'General Staff'),
    ('Personal Assistant', 'Personal Assistant'),
    ('Administrative Officer', 'Administrative Officer'),

    # Sales and Marketing Roles
    ('Sales Manager', 'Sales Manager'),
    ('Sales Executive', 'Sales Executive'),
    ('Marketing Manager', 'Marketing Manager'),
    ('Marketing Executive', 'Marketing Executive'),
    ('Business Development Manager', 'Business Development Manager'),
    ('Account Manager', 'Account Manager'),

    # Human Resources
    ('HR Manager', 'HR Manager'),
    ('HR Executive', 'HR Executive'),
    ('Recruiter', 'Recruiter'),
    ('Training Manager', 'Training Manager'),
    ('Payroll Specialist', 'Payroll Specialist'),

    # Finance and Legal
    ('Finance Manager', 'Finance Manager'),
    ('Accountant', 'Accountant'),
    ('Auditor', 'Auditor'),
    ('Legal Advisor', 'Legal Advisor'),
    ('Compliance Officer', 'Compliance Officer'),

    # Operations and Logistics
    ('Operations Manager', 'Operations Manager'),
    ('Logistics Manager', 'Logistics Manager'),
    ('Warehouse Supervisor', 'Warehouse Supervisor'),
    ('Procurement Officer', 'Procurement Officer'),
    ('Inventory Manager', 'Inventory Manager'),

    # Research and Development
    ('Research Scientist', 'Research Scientist'),
    ('R&D Manager', 'R&D Manager'),
    ('Product Developer', 'Product Developer'),

    # Education and Training
    ('Teacher', 'Teacher'),
    ('Lecturer', 'Lecturer'),
    ('Professor', 'Professor'),
    ('Trainer', 'Trainer'),
    ('Coach', 'Coach'),

    # Healthcare Roles
    ('Doctor', 'Doctor'),
    ('Nurse', 'Nurse'),
    ('Pharmacist', 'Pharmacist'),
    ('Lab Technician', 'Lab Technician'),
    ('Medical Assistant', 'Medical Assistant'),

    # Other Roles
    ('Volunteer', 'Volunteer'),
    ('Intern', 'Intern'),
    ('Trainee', 'Trainee'),
]


EMPLOYEE_LEVEL_CHOICES = [
    ('', ''),
    ('Executive Leadership', 'Executive Leadership'),  # Replacing Senior Management for clarity
    ('Senior Management', 'Senior Management'),  # Added for high-level clarity
    ('Middle Management', 'Middle Management'),  # Adjusted from MidLevelManager
    ('First-Line Management', 'First-Line Management'),  # More standardized name for FirstLevelManager
    ('Executive', 'Executive'),
    ('Senior Engineer', 'Senior Engineer'),  # Added senior option for engineering roles
    ('Engineer', 'Engineer'),
    ('Junior Engineer', 'Junior Engineer'),  # Added junior option for engineering roles
    ('Doctor', 'Doctor'),
    ('Specialist', 'Specialist'),
    ('Officer', 'Officer'),
    ('Field Force', 'Field Force'),  # Adjusted naming for readability
    ('General Staff', 'General Staff'),  # Fixed typo ("Staffs" -> "Staff")
    ('Intern', 'Intern'),  # New addition for entry-level/trainee employees
    ('Consultant', 'Consultant'),  # New addition for contract/freelance roles
    ('Technician', 'Technician'),  # New addition for technical roles
    ('Supervisor', 'Supervisor'),  # New addition for supervisory roles
    ('Associate', 'Associate'),  # New addition for junior-level roles
]


POSTING_AREA_CHOICES=[
        ('',''),
        ('Dhaka','Dhaka'),
        ('Rangpur','Rangpur'),
        ('Sylhet','Sylhet'),
        ('Rajshahi','Rajshahi'),
        ('Chittagong','Chittagong'),
    ]

SPECIALIZATION_CHOICES = [
    ('Cardiology', 'Cardiology'),
    ('Neurology', 'Neurology'),
    ('Orthopedics', 'Orthopedics'),
    ('Pediatrics', 'Pediatrics'),
    ('Dermatology', 'Dermatology'),
    ('Oncology', 'Oncology'),
    ('Gastroenterology', 'Gastroenterology'),
    ('Psychiatry', 'Psychiatry'),
    ('Radiology', 'Radiology'),
    ('Emergency Medicine', 'Emergency Medicine'),
    ('Anesthesiology', 'Anesthesiology'),
    ('Internal Medicine', 'Internal Medicine'),
    ('Obstetrics and Gynecology', 'Obstetrics and Gynecology'),
    ('Ophthalmology', 'Ophthalmology'),
    ('Nephrology', 'Nephrology'),
    ('ENT', 'Ear, Nose, and Throat (ENT)'),
    ('Urology', 'Urology'),
    ('Rheumatology', 'Rheumatology'),
    ('Endocrinology', 'Endocrinology'),
    ('Hematology', 'Hematology'),
    ('Pulmonology', 'Pulmonology'),
    ('Infectious Disease', 'Infectious Disease'),
    ('Geriatrics', 'Geriatrics'),
    ('Chiropractic', 'Chiropractic'),
    ('Pathology', 'Pathology'),
    ('Plastic Surgery', 'Plastic Surgery'),
    ('Vascular Surgery', 'Vascular Surgery'),
    ('Maxillofacial Surgery', 'Maxillofacial Surgery'),
]
