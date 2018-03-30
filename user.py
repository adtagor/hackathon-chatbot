import pymysql

def register_user(firstName, clientId):
    db = pymysql.connect("localhost", "root", "root", "testDB")
    insert_user = """INSERT INTO Users(FirstName, ClientId) values ('%s', %d);""" % (firstName, clientId)

    cursor = db.cursor()

    try:
        user_created = cursor.execute(insert_user)
        db.commit()

    except:
        db.rollback()

    cursor.close()
    db.close()

    