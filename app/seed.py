from .db import init_db, db
from .auth import hash_password

def seed():
    init_db()
    with db() as con:
        users=[
            ('parent@neuroconnect.local','DemoParent123!','Ayesha Khan','parent','en'),
            ('therapist@neuroconnect.local','DemoProfessional123!','Dr. Sara Ahmed','professional','en'),
            ('admin@neuroconnect.local','DemoAdmin123!','Platform Admin','admin','en')]
        for email,pw,name,role,lang in users:
            con.execute("INSERT OR IGNORE INTO users(email,password_hash,full_name,role,preferred_language) VALUES(?,?,?,?,?)",
                        (email,hash_password(pw),name,role,lang))
        parent=con.execute("SELECT id FROM users WHERE email='parent@neuroconnect.local'").fetchone()
        prof_user=con.execute("SELECT id FROM users WHERE email='therapist@neuroconnect.local'").fetchone()
        if parent and not con.execute("SELECT 1 FROM child_profiles WHERE parent_user_id=?",(parent['id'],)).fetchone():
            con.execute("INSERT INTO child_profiles(parent_user_id,display_name,birth_year,communication_level,school_status,primary_concerns) VALUES(?,?,?,?,?,?)",
                        (parent['id'],'Ali',2020,'Uses short phrases','Primary school','Communication and sound sensitivity'))
        if not con.execute("SELECT 1 FROM resources").fetchone():
            rows=[
              ('Understanding Autism','Understanding autism','all','en','A neurodiversity-affirming introduction to autism, common differences, strengths, support needs, and respectful language.','WHO','https://www.who.int/news-room/fact-sheets/detail/autism-spectrum-disorders','article'),
              ('Early Development: What to Observe','Early childhood autism','parent','en','A practical guide to observing communication, play, social interaction and sensory responses without treating any single sign as a diagnosis.','CDC','https://www.cdc.gov/autism/','guide'),
              ('Creating Autism-Friendly Classrooms','Education','teacher','en','Low-arousal classroom strategies, predictable routines, visual support and sensory accommodations.','NICE','https://www.nice.org.uk/guidance/cg170','guide'),
              ('Autism Support for Adults','Autism in adults','all','en','Information on self-advocacy, sensory accommodations, employment and independent living support.','NICE','https://www.nice.org.uk/guidance/cg142','article'),
              ('آٹزم کو سمجھنا','Understanding autism','all','ur','آٹزم کے بارے میں بنیادی، باعزت اور غیر تشخیصی معلومات۔','WHO','https://www.who.int/news-room/fact-sheets/detail/autism-spectrum-disorders','article'),
              ('Autism ko samajhna','Understanding autism','all','roman_ur','Autism ke bare mein bunyadi, ehtiram par mabni aur ghair-tashkhisi maloomat.','WHO','https://www.who.int/news-room/fact-sheets/detail/autism-spectrum-disorders','article')]
            con.executemany("INSERT INTO resources(title,category,audience,language,summary,source_name,source_url,content_type) VALUES(?,?,?,?,?,?,?,?)", rows)
        if prof_user and not con.execute("SELECT 1 FROM professionals WHERE user_id=?",(prof_user['id'],)).fetchone():
            profs=[
              (prof_user['id'],'Dr. Sara Ahmed','Speech-Language Therapist','Speech and communication','Lahore','English, Urdu','online, in_person',9,1,'Supports functional communication, parent coaching and school collaboration.'),
              (None,'Dr. Hamza Raza','Clinical Psychologist','Developmental psychology','Lahore','English, Urdu','in_person',11,1,'Provides developmental and family-focused psychological support.'),
              (None,'Mariam Siddiqui','Occupational Therapist','Sensory and daily living','Islamabad','English, Urdu','online, in_person',7,1,'Focuses on sensory accommodations, routines and adaptive participation.'),
              (None,'Adeel Farooq','Special Educator','Inclusive education','Karachi','English, Urdu','online',8,1,'Supports classroom planning, visual schedules and individualized learning goals.')]
            con.executemany("INSERT INTO professionals(user_id,name,title,specialization,city,languages,consultation_modes,experience_years,verified,bio) VALUES(?,?,?,?,?,?,?,?,?,?)",profs)

if __name__ == '__main__':
    seed()
    print('NeuroConnect 360 database initialized and seeded.')
