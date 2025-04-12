from datetime import datetime
from sqlalchemy import func,text
from frontend.user import *
from scripts.passwordhash import PasswordHasher
from configs.keys import *

def check_user(user):
    hasher = PasswordHasher()
    try:
        usr = User.query.filter_by(username=user, active='Y').first()
        if not usr:
            return False
        return user
    except Exception as e:
        print(e)
        return None


def authenticate(user="admin", password="1234"):
    hasher = PasswordHasher()
    try:
        usr = User.query.filter_by(username=user, active='Y').first()
        print(usr.password)
        gen_hash = hasher.verify_password(password, usr.password)
        print(gen_hash)
        return usr if gen_hash else None
    except Exception as e:
        print(e)
        return None
def create_user(request):
    hasher = PasswordHasher()
    try:
        u_key = hasher.generate_secure_token()
        guid = User.query.with_entities(func.max(User.uid)).scalar()
        uid = guid + 1 if guid else 1
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = request['username']
        pass_hash, _ = hasher.generate_hash(request['password'])
        first_name = request['fname']
        last_name = request['lname']
        email = request['email']
        family_size = request['fam_size']
        end_date = '9999-12-31 00:00:00'
        active = 'Y'

        chk = check_user(username)
        if chk:
            return "User Already Exists"

        new_user = User(u_key=u_key,
                        uid= uid,
                        username=username,
                        password=pass_hash,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        family_size=family_size,
                        create_date=create_date,
                        end_date=end_date,
                        active=active)
        db.session.add(new_user)
        db.session.commit()
        return True

    except Exception as e:
        print(e)
        return None


def update_password(user, oldpassword, newpassword):
    hasher = PasswordHasher()

    try:
        old_pass_hash = User.query.filter_by(username=user, active='Y').first()
        if not hasher.verify_password(oldpassword, old_pass_hash.password):
            print("Old password does not match")
            return False
        all_pass_hash = User.query.filter_by(username = user).all()
        all_pass_hash = [i.password for i in all_pass_hash]
        for i in all_pass_hash:
            if hasher.verify_password(newpassword, i):
                print("New password already exists")
                return False

        usr_det = User.query.filter_by(username=user, active='Y').first()
        u_key = hasher.generate_secure_token()
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uid = usr_det.uid
        username = user
        pass_hash, _ = hasher.generate_hash(newpassword)
        first_name = usr_det.first_name
        last_name = usr_det.last_name
        email = usr_det.email
        family_size = usr_det.family_size
        end_date = '9999-12-31 00:00:00'
        active = 'Y'
        qry = text('''
                    insert INTO user_details (u_key,username,password,first_name,last_name,email,family_size,create_date,end_date,active)
                    select u_key, uuid, pass_hash, create_date, last_update_mod, active_mod from
                    (select * , case 
                    when active = 'Y' and row_num > 1 then 'N' 
                    when active = 'Y' and TIMESTAMPDIFF(DAY,create_date,NOW()) > :expiry then 'N'
                    when row_num = 1 then 'Y' 
                    else 'N' 
                    end as active_mod,
                    case  
                    when active = 'Y' and row_num > 1 then date_format(date_sub(last_end_dt_lag,INTERVAL 1 SECOND),'%Y-%m-%d %H:%i:%s')
                    when active = 'Y' and TIMESTAMPDIFF(DAY,create_date,NOW()) > :expiry then date_format(NOW(), '%Y-%m-%d %H:%i:%s')
                    when row_num = 1 then '9999-12-31 00:00:00'
                    else last_update
                    end as last_update_mod from 
                    (select new_data_raw.*, 
                    row_number() over (partition by uuid order by create_date desc) as row_num ,
                    lag(create_date,1) over ( partition by uuid order by create_date desc) as last_end_dt_lag from 
                    (select * from user_details 
                    union all 
                    select :u_key,:uid,:user,:pass_hash,:first_name,:last_name,:email,:family_size,:create_date,:end_date,:active
                    ) new_data_raw ) new_data_rank) new_data 
                    where new_data.row_num <= :history
                    ON DUPLICATE KEY UPDATE end_date = last_update_mod, active = active_mod
                ''') \
            .bindparams(expiry=PASS_EXPIRY, u_key=u_key, uid = uid ,user=username, pass_hash=pass_hash,
                        first_name=first_name, last_name=last_name, email=email, family_size=family_size,
                        create_date=create_date, end_date=end_date, active=active, history=MAX_PASS_HISTORY)
        _ = db.session.execute(qry)
        db.session.commit()
        return True

    except Exception as e:
        print(e)
        return None

