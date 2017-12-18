
# coding: utf-8
#Designed and Created by Sashidhar NJ
#Email ID: sashijeevan@hotmail

# In[7]:


###Importing all the necessary libraries
from flask import Flask, jsonify
from flask import abort
from flask import request
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import PorterStemmer
from nltk import word_tokenize
from nltk.corpus import stopwords
from sklearn.pipeline import Pipeline
from time import *
import random
from pandas.io.json import json_normalize
import pymongo
from pymongo import MongoClient
import datetime
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


# In[8]:


###Wrapping the complaints code into a flask Api for complaints registration
app = Flask(__name__)

@app.route('/chatbot/api/v1.0/tests', methods=['POST']) ###Enter a path for the app
def create_chat():
    if not request.json or not 'speech' in request.json:
        abort(400)
    chat = {
        'speech': request.json['speech'], #Fetching the input Json
        'issue' : request.json['issue'],
        'response': request.json['response']
    }
   
    #data= jsonify({'chat': chat})
    #return(data)
    #df= pd.DataFrame.from_dict(json_normalize(data), orient='columns')
    text=chat['speech']
    issue_type= chat['issue']
    response= chat['response']
    ###Reading the MongoDB tables where all the complaints data is to be pushed
    client= MongoClient()
    client= MongoClient('localhost',port=27017)
    db= client.test_database1
    posts= db.registered_test
    posts2= db.unregistered_test
    ###Extracting the last entry pushed into DB
    lastissue = posts.find().sort([("date", pymongo.DESCENDING)])
    lastissue=lastissue.next()
    lastissue=lastissue['id']+1
    
    
    
    ###Reading and preprocessing the text file which contains few complaints that could be recorded by customers.
    ### All the complaints are tagged under few classes of categories under which the complaints fall.
    documents= open("../service_type_multiple1.txt").read().split('\n')
    df= pd.DataFrame(documents)
    my_columns= ["service_issues"]
    df.columns=my_columns
    df = pd.concat([df['service_issues'].str.split(',', expand=True)], axis=1)
    my_columns= ["service_issues","issue_type"] #Naming the columns
    df.columns= my_columns
    
    ###Counting the occurances of words (Term document matrix) and preprocessing
    count_vect= CountVectorizer() 
    df_count= count_vect.fit_transform(df['service_issues'])
    tfidf_transformer= TfidfTransformer()
    df_tfidf= tfidf_transformer.fit_transform(df_count)
    stemmer= SnowballStemmer("english", ignore_stopwords=True)
    class StemmedCountVectorizer(CountVectorizer):
        def build_analyzer(self):
            analyzer= super(StemmedCountVectorizer,self).build_analyzer()
            return lambda doc: ([stemmer.stem(w) for w in analyzer(doc)])
    stemmed_count_vect=  StemmedCountVectorizer(stop_words='english')
    text_mnb_stemmed= Pipeline([('vect', stemmed_count_vect),('tfidf',TfidfTransformer()),('clf',MultinomialNB())])
    
    ###Fitting the model
    text_clf_stemmed= text_mnb_stemmed.fit(df['service_issues'],df['issue_type'])
    
    ###Predictions
    predicted= text_clf_stemmed.predict([text])
    pred = text_clf_stemmed.predict_proba([text]) ###Probabilities of preditions of comaplaints to a class
    pred=np.sort(pred)
    pred=pred[:,-1][0]
    
    ###Creating few questions and responses for casual greetings
    greetings = ['Hi Ashish, how may i help you today?']
    random_greeting= random.choice(greetings)
    question= ['How are you?','How are you doing?','How are you','how are you','how are you doing','How are you doing','what are you upto','how have you been']
    responses= ["I am doing Okay","I'm fine. Thank you","I am doing great!","I am perfectly fine"]
    random_response= random.choice(responses)
    thankyou= ['Pleasure is mine!','Pleasure.','nice talking to you','let me know if i can help you with anything else']
    random_thanks= random.choice(thankyou)
    if (text in question)== True:
        chat2= {
        'speech': text,
        'reply': random_response,
        'issue':'',
        'response':''
        }
        return (jsonify({'chat2': chat2}))
    else:
        if predicted== 'question':
            chat2= {
            'speech': text,
            'reply': random_response,
            'issue':'',
            'response':''
            }
            return (jsonify({'chat2': chat2}))
        else:
            if predicted== 'salutation':
                chat2= {
                'speech': text,
                'reply': random_thanks,
                'issue':'',
                'response':''
                }
                return (jsonify({'chat2': chat2}))
        #Start of validation of issue type and speech
        #We are trying to make a case if a user says yes to register a particular category of complaint then a reply for successful registration will be echoed.
            else:
                if predicted== 'greeting':
                    chat2= {
                    'speech': text,
                    'reply': random_greeting,
                    'issue':'',
                    'response':''
                    }
                    return (jsonify({'chat2': chat2}))
                ###------------------------------------LAYER 3 Start---------------------------------------------------------------------------------
                else:
                    if issue_type=="ac_issue" and response=='yes':
                        chat2= {
                        'speech': text,
                        'reply': 'you have successfully registered a complaint with us. Our champion team should be able to fix it shortly!, Ticket ID: INQ{}'.format(lastissue),
                        'issue':'Ticket ID: INQ{} ; Ashish has requested to register a complaint towards an issue with the air conditioner. Desk details: 3FWS97,Building and Location: Aplha, koramangala'.format(lastissue),
                        'date': datetime.datetime.utcnow(),
                        'response':'',
                        'id': lastissue,
                        'Ticket No': 'INQ{}'.format(lastissue)
                        }
                        try:
                            return (jsonify({'chat2': chat2}))
                        finally:
                            
                            post_id= posts.insert_one(chat2).inserted_id
                           
                    else:
                        if issue_type=="Internet_issue" and response=='yes':
                            chat2= {
                            'speech': text,
                            'reply': 'you have successfully registered a complaint with us. Our champion team should be able to fix it shortly!, Ticket ID: INQ{}'.format(lastissue),
                            'issue':'Ticket ID: INQ{} ; Ashish has requested to register a complaint towards an issue with the internet. Desk details: 3FWS97,Building and Location: Aplha, koramangala'.format(lastissue),
                            'date': datetime.datetime.utcnow(),
                            'response':'',
                            'id': lastissue,
                            'Ticket No': 'INQ{}'.format(lastissue)
                            }
                            try:
                                return (jsonify({'chat2': chat2}))
                            finally:
                                #try:
                                post_id= posts.insert_one(chat2)
                        else:
                            if issue_type=="lighting_issue" and response=='yes':
                                chat2= {
                                'speech': text,
                                'reply': 'you have successfully registered a complaint with us. Our champion team should be able to fix it shortly!, Ticket ID: INQ{}'.format(lastissue),
                                'issue':'Ticket ID: INQ{} ; Ashish has requested to register a complaint towards an issue with the lighting. Desk details: 3FWS97,Building and Location: Aplha, koramangala'.format(lastissue),
                                'date': datetime.datetime.utcnow(),
                                'response':'yes',
                                'id': lastissue,
                                'Ticket No': 'INQ{}'.format(lastissue)
                                }
                                try:
                                    return (jsonify({'chat2': chat2}))
                                finally:
                                    #try:
                                    post_id= posts.insert_one(chat2).inserted_id
                            else:
                                if issue_type=="lock_key_issue" and response=='yes':
                                    chat2= {
                                    'speech': text,
                                    'reply': 'you have successfully registered a complaint with us. Our champion team should be able to fix it shortly!, Ticket ID: INQ{}'.format(lastissue),
                                    'issue':'Ticket ID: INQ{} ; Ashish has requested to register a complaint towards an issue with the lock and keys. Desk details: 3FWS97,Building and Location: Aplha, koramangala'.format(lastissue),
                                    'date': datetime.datetime.utcnow(),
                                    'response':'',
                                    'id': lastissue,
                                    'Ticket No': 'INQ{}'.format(lastissue)
                                    }
                                    try:
                                        return (jsonify({'chat2': chat2}))
                                    finally:
                                        #try:
                                        post_id= posts.insert_one(chat2).inserted_id
                                else:
                                    if issue_type=="washroom_issue" and response=='yes':
                                        chat2= {
                                        'speech': text,
                                        'reply': 'you have successfully registered a complaint with us. Our champion team should be able to fix it shortly!, Ticket ID: INQ{}'.format(lastissue),
                                        'issue':'Ticket ID: INQ{} ; Ashish has requested to register a complaint towards an issue with the Washrooms. Desk details: 3FWS97,Building and Location: Aplha, koramangala'.format(lastissue),
                                        'date': datetime.datetime.utcnow(),
                                        'response':'',
                                        'id': lastissue,
                                        'Ticket No': 'INQ{}'.format(lastissue)
                                        }
                                        try:
                                            return (jsonify({'chat2': chat2}))
                                        finally:
                                            #try:
                                            post_id= posts.insert_one(chat2).inserted_id
                                    ###------------------------------------LAYER 3 End------------------------------------------------------------
                                    
                                    ###------------------------------------ LAYER 2 Start---------------------------------------------------------
                                    else:
                                        if issue_type=="ac_issue" and text=='yes':
                                            chat2= {
                                            'speech': text,
                                            'reply': 'could you please help us by elaborating about the complaint in short?',
                                            'issue': 'ac_issue',
                                            'date': datetime.datetime.utcnow(),
                                            'response': 'yes'
                                            }
                                            try:
                                                return (jsonify({'chat2': chat2}))
                                            finally:
                                                post_id= posts2.insert_one(chat2).inserted_id
                                        else:
                                            if issue_type=="ac_issue" and text=='no':
                                                chat2= {
                                                'speech': text,
                                                'reply': 'We would love to assist you in case of any complaints',
                                                'issue':'',
                                                'response':''
                                                }
                                                return (jsonify({'chat2': chat2}))
                        #End of validation of issue type and speech
                                            else:
                                                if issue_type=="Internet_issue" and text=='yes':
                                                    chat2= {
                                                    'speech': text,
                                                    'reply': 'could you please help us by elaborating about the complaint in short?',
                                                    'issue': 'Internet_issue', 
                                                    'date': datetime.datetime.utcnow(),
                                                    'response':'yes'
                                                    }
                                                    try:
                                                        return (jsonify({'chat2': chat2}))
                                                    finally:
                                                        post_id= posts2.insert_one(chat2).inserted_id
                                                else:
                                                    if issue_type=="Internet_issue" and text=='no':
                                                        chat2= {
                                                        'speech': text,
                                                        'reply': 'We would love to assist you in case of any complaints',
                                                        'issue':'',
                                                        'response':''
                                                        }
                                                        return (jsonify({'chat2': chat2}))
                                                    else:
                                                        if issue_type=="lock_key_issue" and text=='yes':
                                                            chat2= {
                                                            'speech': text,
                                                            'reply': 'could you please help us by elaborating about the complaint in short?',
                                                            'issue': 'lock_key_issue',
                                                            'date': datetime.datetime.utcnow(),
                                                            'response':'yes'
                                                            }
                                                            try:
                                                                return (jsonify({'chat2': chat2}))
                                                            finally:
                                                                post_id= posts2.insert_one(chat2).inserted_id
                                                        else:
                                                            if issue_type=="lock_key_issue" and text=='no':
                                                                chat2= {
                                                                'speech': text,
                                                                'reply': 'We would love to assist you in case of any complaints',
                                                                'issue':'',
                                                                'response':''
                                                                }
                                                                return (jsonify({'chat2': chat2}))
                                                            else:
                                                                if issue_type=="Phoneline_issue" and text=='yes':
                                                                    chat2= {
                                                                    'speech': text,
                                                                    'reply': 'you have successfully registered a complaint with us. We should be able to fix it shortly!, Ticket ID: INQ154',
                                                                    'issue': 'Phoneline_issue',
                                                                    'date': datetime.datetime.utcnow(),
                                                                    'response':''
                                                                    }
                                                                    try:
                                                                        return (jsonify({'chat2': chat2}))
                                                                    finally:
                                                                        post_id= posts2.insert_one(chat2).inserted_id
                                                                else:
                                                                    if issue_type=="Phoneline_issue" and text=='no':
                                                                        chat2= {
                                                                        'speech': text,
                                                                        'reply': 'We would love to assist you in case of any complaints',
                                                                        'issue':'',
                                                                        'response':''
                                                                        }
                                                                        return (jsonify({'chat2': chat2}))
                                                                    else:
                                                                        if issue_type=="lighting_issue" and text=='yes':
                                                                            chat2= {
                                                                            'speech': text,
                                                                            'reply': 'could you please help us by elaborating about the complaint in short?',
                                                                            'issue': 'lighting_issue',
                                                                            'date': datetime.datetime.utcnow(),
                                                                            'response':'yes'
                                                                            }
                                                                            try:
                                                                                return (jsonify({'chat2': chat2}))
                                                                            finally:
                                                                                post_id= posts2.insert_one(chat2).inserted_id
                                                                        else:
                                                                            if issue_type=="lighting_issue" and text=='no':
                                                                                chat2= {
                                                                                'speech': text,
                                                                                'reply': 'We would love to assist you in case of any complaints',
                                                                                'issue':'',
                                                                                'response':''
                                                                                }
                                                                                return (jsonify({'chat2': chat2}))
                                                                            else:
                                                                                if issue_type=="washroom_issue" and text=='yes':
                                                                                    chat2= {
                                                                                    'speech': text,
                                                                                    'reply': 'could you please help us by elaborating about the complaint in short?',
                                                                                    'issue': 'washroom_issue',
                                                                                    'date': datetime.datetime.utcnow(),
                                                                                    'response':'yes'
                                                                                    }
                                                                                    try:
                                                                                        return (jsonify({'chat2': chat2}))
                                                                                    finally:
                                                                                        post_id= posts2.insert_one(chat2).inserted_id
                                                                                else:
                                                                                    if issue_type=="lighting_issue" and text=='no':
                                                                                        chat2= {
                                                                                        'speech': text,
                                                                                        'reply': 'We would love to assist you in case of any complaints',
                                                                                        'issue':'',
                                                                                        'response':''
                                                                                        }
                                                                                        return (jsonify({'chat2': chat2}))
                                                                                    ###--------------LAYER 2 End--------------------------------------------------------------------
                                                                                    else:
                                                                                        if (pred<0.25) == True:
                                                                                            chat2= {
                                                                                            'speech': text,
                                                                                            'reply': 'Sorry, i couldnt catch that!',
                                                                                            'issue':'',
                                                                                            'response':''
                                                                                            }
                                                                                            return (jsonify({'chat2': chat2}))
                                                                                        ### ---------LAYER 1 Start------------------------------------------------------------------
                                                                                        else:
                                                                                            if predicted== 'ac_issue':
                                                                                                chat2= {
                                                                                                'speech': text,
                                                                                                'reply': 'Would you like to register a complaint regarding your AC?, please say yes or no',
                                                                                                'issue': 'ac_issue',
                                                                                                'date': datetime.datetime.utcnow(),
                                                                                                'response':''
                                                                                                }
                                                                                                try:
                                                                                                    return (jsonify({'chat2': chat2}))
                                                                                                finally:
                                                                                                    post_id= posts2.insert_one(chat2).inserted_id
                                                                                            else:
                                                                                                if predicted== 'Internet_issue':
                                                                                                    chat2= {
                                                                                                    'speech': text,
                                                                                                    'reply': 'Would you like to register a complaint regarding your Internet?, please say yes or no',
                                                                                                    'issue': 'Internet_issue',
                                                                                                    'date': datetime.datetime.utcnow(),
                                                                                                    'response':''
                                                                                                    }
                                                                                                    try:
                                                                                                        return (jsonify({'chat2': chat2}))
                                                                                                    finally:
                                                                                                        post_id= posts2.insert_one(chat2).inserted_id
                                                                                                else:
                                                                                                    if predicted== 'lock_key_issue':
                                                                                                        chat2= {
                                                                                                        'speech': text,
                                                                                                        'reply': 'Would you like to raise a ticket related to lock and key?, please say yes or no',
                                                                                                        'issue': 'lock_key_issue',
                                                                                                        'date': datetime.datetime.utcnow(),
                                                                                                        'response':''
                                                                                                        }
                                                                                                        try:
                                                                                                            return (jsonify({'chat2': chat2}))
                                                                                                        finally:
                                                                                                            post_id= posts2.insert_one(chat2).inserted_id
                                                                                                    else:
                                                                                                        if predicted== 'Phoneline_issue':
                                                                                                            chat2= {
                                                                                                            'speech': text,
                                                                                                            'reply': 'Would you like to register a complaint regarding your Telephone line?, please say yes or no',
                                                                                                            'issue': 'Phoneline_issue',
                                                                                                            'date': datetime.datetime.utcnow(),
                                                                                                            'response':''
                                                                                                            }
                                                                                                            try:
                                                                                                                return (jsonify({'chat2': chat2}))
                                                                                                            finally:
                                                                                                                post_id= posts2.insert_one(chat2).inserted_id
                                                                                                        else:
                                                                                                            if predicted== 'lighting_issue':
                                                                                                                chat2= {
                                                                                                                'speech': text,
                                                                                                                'reply': 'Would you like to register a complaint regarding the lighting?, please say yes or no',
                                                                                                                'issue': 'lighting_issue',
                                                                                                                'date': datetime.datetime.utcnow(),
                                                                                                                'response':''
                                                                                                                }
                                                                                                                try:
                                                                                                                    return (jsonify({'chat2': chat2}))
                                                                                                                finally:
                                                                                                                    post_id= posts2.insert_one(chat2).inserted_id
                                                                                                            else:
                                                                                                                if predicted== 'washroom_issue':
                                                                                                                    chat2= {
                                                                                                                    'speech': text,
                                                                                                                    'reply': 'Would you like to register a complaint regarding the washroom?, please say yes or no',
                                                                                                                    'issue': 'washroom_issue',
                                                                                                                    'date': datetime.datetime.utcnow(),
                                                                                                                    'response':''
                                                                                                                    }
                                                                                                                    try:
                                                                                                                        return (jsonify({'chat2': chat2}))
                                                                                                                    finally:
                                                                                                                        post_id= posts2.insert_one(chat2).inserted_id
                                                                                                                else:
                                                                                                                    chat2= {
                                                                                                                    'speech': text,
                                                                                                                    'reply': 'If you are facing any issues our help desk will get back to you very soon!',
                                                                                                                    'issue':'',
                                                                                                                    'response':''
                                                                                                                    }
                                                                                                                    return (jsonify({'chat2': chat2}))
                                                                                                                ###--------LAYER 1 End--------------------------------
if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=False,port=5002)

