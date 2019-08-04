from flask import Flask, session, request, redirect, render_template, flash, url_for
from mysqlconnection import connectToMySQL
import json

app=Flask(__name__)
app.secret_key = 'keep it secret'

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')



'''
*************************
'''


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/username", methods=['POST'])
def username():
    found = False
    mysql = connectToMySQL('mac_taqueria1')        # connect to the database
    query = "SELECT email from users WHERE users.email = %(user)s;"
    data = { 'user': request.form['email'] }
    result = mysql.query_db(query, data)
    if result:
        found = True
    return render_template('partials/username.html', found=found)



@app.route("/users/add", methods=["POST"])
def add_user_to_db():

    is_valid = True
    if len(request.form['name']) <= 1:
        is_valid = False
        flash("Please enter a NAME") # maybe replace flashes with Ajax/jQuery if time allows
        return redirect('/')
    # if len(request.form['last_name']) <= 1:
    #     is_valid = False
    #     flash("Please enter a LAST NAME")
    #     return redirect('/')
    if len(request.form['email']) <= 1:
        is_valid = False
        flash("Please enter an EMAIL")
        return redirect('/')
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address format")
        return redirect('/')
    if len(request.form['password1']) <= 5:
        is_valid = False
        flash("Password must be 5 or more characters")
        return redirect('/')
    if (request.form['password1'] != request.form['password2']):
        is_valid = False
        flash("Passwords do not match!")
        return redirect('/')

    if is_valid:
        mysql = connectToMySQL('mac_taqueria1')
        pw_hash = bcrypt.generate_password_hash(request.form['password1'])
        query = 'INSERT INTO users (name, email, password) VALUES (%(nm)s, %(eml)s, %(psw)s);'
        data = {
            "nm": request.form['name'],
            "eml": request.form['email'],
            "psw": pw_hash
        }
        mysql.query_db(query, data)


        session['login'] = True

        mysql2 = connectToMySQL('mac_taqueria1')
        query2 = "SELECT * FROM users WHERE email = %(email2)s;"
        data2 = {
            "email2": request.form["email"]
        }
        result = mysql2.query_db(query2, data2)
        session['userid'] = result[0]['id']
        flash("You've Successfully Added a User!")

        return redirect('/users/welcome')
    


@app.route('/users/login', methods=['POST'])
def login():
    mysql = connectToMySQL('mac_taqueria1')
    query = 'SELECT * FROM users WHERE email = %(eml)s;'
    data = {
        "eml": request.form['logemail']
    }
    result = mysql.query_db(query, data)

    if result:
        session['userid'] = result[0]['id']
        hashed_pw = result[0]['password']
        if bcrypt.check_password_hash(hashed_pw, request.form['logpassword']):
            session['login'] = True
            flash("Thanks for logging in")
            return redirect('/users/welcome')
        else:
            session['login'] = False
            flash("Login failed. Please try again or register.")
            return redirect('/')
    else:
        flash("Your email could not be found. Please retry or register.")
        return redirect('/')



@app.route('/users/welcome', methods = ['POST', 'GET'])
def welcome():
    mysql1 = connectToMySQL("mac_taqueria1")
    query1 = "SELECT * FROM items WHERE type = 'taco';"
    taco_info = mysql1.query_db(query1)

    # mysql2 = connectToMySQL("mac_taqueria1")
    # query2 = "SELECT taco_price FROM tacos;"
    # taco_prices = mysql2.query_db(query2)

    mysql2 = connectToMySQL("mac_taqueria1")
    query2 = "SELECT * FROM items WHERE type = 'drink';"
    drink_info = mysql2.query_db(query2)

    mysql3 = connectToMySQL("mac_taqueria1")
    query3 = "SELECT * FROM users WHERE id = %(user_id)s;"
    data3 = { "user_id": session['userid'] }
    user_info = mysql3.query_db(query3, data3)
    if len(user_info) > 0:
        user_info = user_info[0]

    mysql4 = connectToMySQL("mac_taqueria1")
    query4 = "SELECT * FROM users JOIN orders ON users.id = orders.user_id JOIN items_has_orders ON items_has_orders.order_id = orders.id JOIN items ON items_has_orders.item_id = items.id;"
    all_info = mysql4.query_db(query4)


    return render_template('welcome.html', taco_info = taco_info, drink_info = drink_info, user_info = user_info, all_info = all_info)



'''
What I'm trying to do below:
I'm getting both the user info and the order info.
I'm inserting into the orders table the info from the order on the template page
I'm going to associate/join the orders table with the users table
'''




@app.route('/orders/<id>/review', methods=['POST'])
def reviewOrder(id):

    order_dict = {}
    quant_arr = []
    for i in request.form:
        id_arr = (i.split("-")) # creates a list: [#, 'quantity']

        itm = id_arr[0] # gets the # from the list above and stores it as itm
        '''
        The following checks every second part of the multidict to see what value it holds, if none then it assigns it to zero
        '''
        quantity_info = int(request.form[i]) if request.form[i] else 0 # we have the quantity for each

        if quantity_info > 0:
        
            order_dict[itm] = itm # this prints out 1, 2, 3, 4, 5, 6 (all the id numbers)
            
            order_dict[itm] = quantity_info # this prints out all the quantities

            quant_arr.append(quantity_info)
            
            
        
    # dict_key_array = [] 
    # dict_val_array = []
    # for k, v in session["order_info"].items():
    #     if v > 0:
    #         dict_key_array.append(k) 
    #         dict_val_array.append(v)
        

    '''
    order_dict now has all the ids and all the quantities as a dictionary! This is where I should replace the keys with the keys found in the database.
    '''

    session['order_info'] = order_dict

    

    dict_key_array = [] # this converted the dictionary above to a list!
    dict_val_array = []
    for k, v in session["order_info"].items():
        if v > 0:
            dict_key_array.append(k) 
            dict_key_array.append(v)
            dict_val_array.append(v)
    
    temp_dict = session["order_info"]


    for key in list(temp_dict.keys()):
        if temp_dict[key] < 1:
            del temp_dict[key]

    session['final_dict'] = temp_dict

    print(" SESSIONFINALDICT "*10)
    print(session['final_dict'])

   

    order_data = session['final_dict']

    
    jungle = []
    for x in range(0, len(dict_key_array), 2):
        data6 = {
            "itm_num": int(dict_key_array[x])
        }
        mysql6 = connectToMySQL("mac_taqueria1")
        query6 = "SELECT name, price FROM items WHERE items.id = %(itm_num)s;"
        pre_jungle6 = mysql6.query_db(query6, data6)
        jungle.append(pre_jungle6[0]['name'])

    new_dict = {}
    counter = 0
    while counter < len(dict_val_array):
        for name in jungle:
            new_dict[name] = dict_val_array[counter]
            counter+=1

    session['new_dict'] = new_dict

    c = 0
    price = []
    while c < len(order_dict):
        price.append(pre_jungle6[0]['price'])
        c += 1

    print("printing pre_jungle6"*5)
    print(price)
    
    print("jungle"*5)
    # print(pre_jungle6[0]['name'])
    # print(jungle)
    print(session['new_dict'])

    mysql2 = connectToMySQL("mac_taqueria1") # for getting USER INFORMATION
    query2 = "SELECT * FROM users WHERE id = %(_id)s;"
    data2 = { "_id": id }
    customer_info = mysql2.query_db(query2, data2)
    customer_info = customer_info[0]


    mysql5 = connectToMySQL("mac_taqueria1") # for JOINING ALL the tables together
    query5 = "SELECT users.name, orders.id, items.id, items.name, items.type, items.price FROM users JOIN orders ON users.id = orders.user_id JOIN items_has_orders ON items_has_orders.order_id = orders.id JOIN items ON items_has_orders.item_id = items.id ORDER BY orders.id;"
    all_info = mysql5.query_db(query5)

    grand_total = 0
    for key, value in new_dict.items():
        grand_total += value * pre_jungle6[0]['price']
    
    print("grand total"*5)
    print(grand_total)

    sum = 0
    for v in new_dict.values():
        sum += v
    
    # count = 0
    # for key, value in new_dict.items():
    #     count = value * pre_jungle6[0]['price']
    #     key = key
    #     value = value

    order_num = 0

    session["order_num"] = order_num



    return render_template("review.html", all_info = all_info, customer_info = customer_info, order_data = order_data, jungle = jungle, quant_arr = quant_arr, new_dict = new_dict, pre_jungle6 = pre_jungle6, price = price, grand_total = grand_total, sum = sum)


@app.route('/orders/<id>/confirm', methods=['POST'])
def confirm_order(id):

    mysql14 = connectToMySQL("mac_taqueria1")
    query14 = "SELECT order_number FROM orders;"
    result = mysql14.query_db(query14)

    max = 0
    for i in result: # this finds the highest order_number in the orders table
        if max < i['order_number']:
            max = i['order_number']

    max = max + 1
    mysql15 = connectToMySQL("mac_taqueria1")
    query15 = "INSERT INTO orders (order_number, user_id) VALUES (%(_max)s, %(_id)s);"
    data15 = {"_max": max, "_id": id }
    mysql15.query_db(query15, data15)

    mysql9 = connectToMySQL('mac_taqueria1')
    query9 = "SELECT * FROM users WHERE id = %(_id)s;"
    data9 = { "_id": id}
    user_info = mysql9.query_db(query9, data9)
    user_info = user_info[0]

    mysql23 = connectToMySQL("mac_taqueria1")
    query23 = "SELECT id FROM orders WHERE order_number = %(_max)s;"
    data23 = { "_max": max}
    orderzID = mysql23.query_db(query23, data23)
    print(" ordzID "*10)
    print(orderzID[0]['id'])
    orderzID = orderzID[0]['id']

    for k, v in session['final_dict'].items():

        print(" WHAT IS K?"*10)
        print(k)
        print(" WHAT IS V?"*10)
        print(v)

        mysql22 = connectToMySQL("mac_taqueria1")
        query22 = "INSERT INTO items_has_orders (item_id, order_id, item_count) VALUES ('%(_k)s', '%(_ord)s', '%(_v)s');"
        data22 = {
            "_k": int(k),
            "_ord": orderzID,
            "_v": int(v)
        }
        final_order_info = mysql22.query_db(query22, data22)


    return render_template("complete.html", user_info = user_info, order_number = max, final_order_info = final_order_info)


@app.route('/orders/edit', methods=['POST'])
def edit_order():

    return render_template('edit.html')


@app.route('/users/logout', methods=['GET'])
def logout():
    session['login'] = False
    flash("You are now logged out. Come back soon!")
    session.clear()
    return redirect('/')



if __name__ == ('__main__'):
    app.run(debug=True)