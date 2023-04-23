
import datetime
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from functools import reduce


from flask import Flask, render_template, request
from pip._vendor.rich.markup import render

app = Flask(__name__)
s3 = boto3.client('s3')    
   
@app.route("/checkLogin", methods = ['POST'])
def checkLogin():
    global curEmail
    global curSubscriptions
    email = request.form['email']
    password = request.form['password']
    #if logged in return render_template["mainPage.html"]
    #else return render_template["index.html"] with error message
    login = getLogin(email, password)
    
    
    if login:
        curEmail = email
        curSubscriptions = getSubscriptions(curEmail)
        return render_template('MainPage.html', username = getUsername(email), subscribed = curSubscriptions)
    else:
        error = "Incorrect email or password"
        return render_template('index.html', error= error)
    

@app.route("/logout", methods = ['GET'])
def logout():
    return render_template("index.html")

@app.route('/')
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    return render_template('index.html')

@app.route("/beginRegister", methods = ['GET'])
def beginRegister():
        return render_template('register.html')

@app.route("/register", methods = ['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('login')
    
    try:
        response = table.query(KeyConditionExpression = Key('email').eq(email))
        items = response['Items']
        if len(items) >= 1:
            #Returns error to alert user that email already exists
            error = "Email already exists in database"
            return render_template('register.html', error = error)
            
        else: 
            addLogin(email, password, username, table)
            return render_template('index.html')
        
    except ClientError as e:
            print(e.response['Error']['Message'])
    
    return render_template('register.html', error=e.response['Error']['Message'])

@app.route("/query", methods = ['POST'])
def query():
    
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Music')
    
    title = request.form['title']
    artist = request.form['artist']
    year = request.form['year']
    
    #collect user queries
    queryList = []
    if title:
        queryList.append(Key('title').eq(title))
    if artist:
        queryList.append(Key('artist').eq(artist))
    if year:
        queryList.append(Key('year').eq(year))
        
    #combine  the queries into one larger query  
    if queryList:
        response = table.scan(
            FilterExpression=reduce(lambda x, y: x & y, queryList)
        )
        results = response['Items']    
    else:
        results = []
    
    for song in results:
        #image_object = s3.get_object(Bucket="assignment1-music", Key='ArcadeFire.jpg')
        curKey = song['img_url']
        finalKey = curKey.rsplit('/', 1)
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': 'assignment1-music', 'Key': finalKey[1]},
            ExpiresIn=360 )
        song['image_url'] = url
    
    if results:
        return render_template('MainPage.html', results=results, username = getUsername(curEmail), subscribed = curSubscriptions)
    else:    
        return render_template('MainPage.html', queryError="Data couldn't be found in database", username= getUsername(curEmail), subscribed = curSubscriptions)

@app.route("/subscribe", methods = ['POST'])
def subscribe():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    subbedTable = dynamodb.Table('Subscribed')
    global curSubscriptions
    title = request.form['titleSubbed']
    
    subbedTable.put_item(
        Item={
        'email': curEmail,
        'SongTitle': title,
        })
    curSubscriptions = getSubscriptions(curEmail)
    return render_template('MainPage.html' , username = getUsername(curEmail), subscribed = curSubscriptions)


@app.route("/unsubscribe", methods = ['POST'])
def unsubscribe():  
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    subbedTable = dynamodb.Table('Subscribed')
    global curSubscriptions  
    title = request.form['titleSubbed']

    subbedTable.delete_item(
        Key={
        'email': curEmail,
        'SongTitle': title,
    })
    curSubscriptions = getSubscriptions(curEmail)
    return render_template('MainPage.html' , username = getUsername(curEmail), subscribed = curSubscriptions)


def getSubscriptions(email):
    try:    
    #Finds a users subscriptions and returns them
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        subTable = dynamodb.Table('Subscribed')
        musicTable = dynamodb.Table('Music')
        
        response = subTable.query(
                KeyConditionExpression=Key('email').eq(email)
            )
        subscriptions = response['Items'] 
        subscribed = []
        for song in subscriptions:
            songResponse = musicTable.scan(
                FilterExpression=(
                    Key('title').eq(song["SongTitle"])
            ))
        
            subscribed.extend(songResponse['Items'])
    
        #generate images for songs
        for song in subscribed:
            curKey = song['img_url']
            finalKey = curKey.rsplit('/', 1)
            url = s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': 'assignment1-music', 'Key': finalKey[1]},
                ExpiresIn=360 )
            song['image_url'] = url
    
        return subscribed
    except Exception as e:
        print(f"An error occurred: {e}")

def addLogin(email, password, username, table):
    table.put_item(
        Item={
        'email': email,
        'password': password,
        'user_name': username
        })

def getUsername(email):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('login')
        
        try: 
            response = table.query(KeyConditionExpression = Key('email').eq(email))
            items = response['Items']
            if len(items) == 1:
                return items[0]['user_name']
            else:
                return null
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return 1;

def getLogin(email, password):
        """
        Gets movie data from the table for a specific movie.
        :param email: Email of user.
        :param password: Password of user.
        :return: True if data matches login in the database, false otherwise.
        """
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('login')
        
        #Find any matching emails in database and then check if passwords match
        try: 
            response = table.query(KeyConditionExpression = Key('email').eq(email))
            items = response['Items']
            if len(items) == 1 and items[0]['password'] == password:
                return True
            else:
                return False
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            #no errors, login successful
            return 1;


        
if __name__ == '__main__':
    
    app.run(host='127.0.0.1', port=80, debug=True)
    #app.run(port=8080)
    