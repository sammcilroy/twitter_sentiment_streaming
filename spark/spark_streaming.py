import findspark
findspark.init('/spark-2.4.3-bin-hadoop2.7') # local spark installation
import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.4.3 pyspark-shell'

import sys
reload(sys)
sys.setdefaultencoding('UTF-8') # deal with tweet text encoding
from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from kafka import SimpleProducer, KafkaClient
from kafka import KafkaProducer
import json
import numpy
from textblob import TextBlob
import re
import requests

def bounding_box(coordinates):
    '''
    Tweet location is given as a bounding box of four coordinates

    Return the centre of the bounding box to approximate the user's
    location on a map
    '''
    
    coords = str(coordinates)
    coords = coords.replace("[", "")
    coords = coords.replace("]", "")
    coords = coords.replace(",", "")
    coords = coords.replace("'", "")
    coords_list = coords.split(" ")
    x1 = float(coords_list[0])
    y1 = float(coords_list[1])
    x2 = float(coords_list[2])
    y2 = float(coords_list[3])
    x3 = float(coords_list[4])
    y3 = float(coords_list[5])
    x4 = float(coords_list[6])
    y4 = float(coords_list[7])

    long = (x1 + x2 + x3 + x4)/4
    lat = (y1 + y2 + y3 + y4)/4
    return (lat, long)

def clean_text(tweet_text):
  '''
  Deal with non-ascii characters in tweet text
  '''
  cleaned = re.sub(r'[^\x00-\x7f]',r'', tweet_text)
  return cleaned.encode('utf-8')

def tweet_sentiment(text):
  polarity = round(float(TextBlob(text).sentiment.polarity),2) # tweet text polarity score between -1, negative, and 1 positive
  if polarity > 0.10:
    if polarity > 0.60: # positive score cutoffs
      return (polarity, 'very positive')
    else:
      return (polarity, 'positive')
  elif polarity < -0.10: # negative score cutoffs
    if polarity < -0.60:
      return (polarity, 'very negative')
    else:
      return (polarity, 'negative')
  else:
    return (polarity, 'neutral')
  
def kafka_sender(messages):
    producer = KafkaProducer(bootstrap_servers='localhost:9092')

    for message in messages:
        producer.send('twitter_sentiment_stream', bytes(message))
    producer.flush()

interval = 2 # pick up new tweets from the stream as they occur (every 2 seconds)
topic = 'kafka_twitter_stream_json' # kafka topic to subscribe to, contains stream of tweets in json

conf = SparkConf().setAppName("KafkaTweetStream").setMaster("local[*]")
sc = SparkContext(conf=conf)
sc.setLogLevel("WARN")
ssc = StreamingContext(sc, interval)

kafkaStream = KafkaUtils.createDirectStream(ssc, [topic], {
  'bootstrap.servers': 'localhost:9092',
  'group.id': 'twitter',
  'fetch.message.max.bytes': '15728640',
  'auto.offset.reset': 'largest'}) # subscribe/stream from the kafka topic

'''
        Tweets are coming in from the Kafka topic in large json blocks, extract the username, location
        and contents of the tweets as json objects.

        Basic dataframe for analysis.
'''
tweets = kafkaStream. \
        map(lambda (key, value): json.loads(value)). \
        map(lambda json_object: (json_object["user"]["screen_name"],
                bounding_box(json_object["place"]["bounding_box"]["coordinates"]),
								clean_text(json_object["text"]), tweet_sentiment(clean_text(json_object["text"]))))

tweets.pprint(10)
tweets.persist(StorageLevel.MEMORY_AND_DISK) # retain the tweets dataframe in persistent memory and disk to allow continued analysis of the stream

topic = 'kafka_twitter_stream_coordinates'
kafkaStreamCoords = KafkaUtils.createDirectStream(ssc, [topic], {
  'bootstrap.servers': 'localhost:9092',
  'group.id': 'twitter',
  'fetch.message.max.bytes': '15728640',
  'auto.offset.reset': 'largest'}) # subscribe/stream from the kafka topic

tweets_coordiates = kafkaStreamCoords. \
        map(lambda (key, value): json.loads(value)). \
        map(lambda json_object: (json_object["user"]["screen_name"],
								json_object["coordinates"]["coordinates"],
								clean_text(json_object["text"]), tweet_sentiment(clean_text(json_object["text"]))))
        
tweets_coordiates.pprint(10)
tweets_coordiates.persist(StorageLevel.MEMORY_AND_DISK)

'''
  From the tweets data stream, extract the usernames from the text.

  Maintain a running count over 24 hours of the most tagged users.

  Replicate the 'influencer' function of twitter to show the top 10 talked about
  people in London.
'''

# keep the username and tweet text
# split the text of the tweet into a list of words
# keep the words marked with a twitter username @
# map - assign count of 1 to each hashtag
# maintain a running total and continue for 24 hours, show results at intervals of 2 seconds
                                                              # ensure stream is running without issue
# sort in descing order by running total, the first x rows will now indicate the most mentioned users

influencers = tweets. \
        map(lambda (username, coordinates, tweet_text, sentiment_level): (username, tweet_text)). \
        flatMapValues(lambda tweet_text: tweet_text.split(" ")). \
        filter(lambda (pair, word): len(word) > 1 and word[0] == '@'). \
        map(lambda (username, hashtag): (hashtag, 1)). \
        reduceByKeyAndWindow(lambda a, b: a+b, None, 60*60*24, 2). \
        transform(lambda rdd: rdd.sortBy(lambda a: -a[-1]))
        


def influencers_to_flask(rdd):
    '''
    For each RDD send data to flask api endpoint
    '''
    if not rdd.isEmpty():
        top = rdd.take(10)

        labels = []
        counts = []

        for label, count in top:
            labels.append(label)
            counts.append(count)
            #print(labels)
            #print(counts)
            request = {'label': str(labels), 'count': str(counts)}
            response = requests.post('http://0.0.0.0:5001/update_influencers', data=request)

influencers.pprint(10) # print the current top ten influencers to the console
influencers.foreachRDD(influencers_to_flask) # send the current top 10 influencers rdd to flask for visualisation

'''
  From the tweets data stream, extract the hashtags from the text.

  Maintain a running count over 24 hours of the most used hashtags.

  Replicate the 'trending' function of twitter to show the top 10 talked about
  topics in London.
'''
# keep the username and tweet text
# split the text of the tweet into a list of words
# keep the words marked with the twitter topic hashtag #
# map - assign count of 1 to each hashtag
# maintain a running total and continue for 24 hours, show results at intervals of 2 seconds
                                                              # ensure stream is running without issue
# sort in descing order by running total, the first x rows will now indicate the most popular #
trending = tweets. \
  map(lambda (username, coordinates, tweet_text, sentiment_level): (username, tweet_text)). \
  flatMapValues(lambda tweet_text: tweet_text.split(" ")). \
  filter(lambda (pair, word): len(word) > 1 and word[0] == '#'). \
  map(lambda (username, hashtag): (hashtag, 1)). \
  reduceByKeyAndWindow(lambda a, b: a+b, None, 60*60*24, 2). \
  transform(lambda rdd: rdd.sortBy(lambda a: -a[-1]))
  
  


def trending_to_flask(rdd):
    '''
    For each RDD send top ten data to flask api endpoint
    '''
    if not rdd.isEmpty():
        top = rdd.take(10)

        labels = []
        counts = []

        for label, count in top:
            labels.append(label)
            counts.append(count)
            #print(labels)
            #print(counts)
            request = {'label': str(labels), 'count': str(counts)}
            response = requests.post('http://0.0.0.0:5001/update_trending', data=request)

trending.pprint(10) # print the current top ten hashtags to the console
trending.foreachRDD(trending_to_flask) # send the current top 10 hashtags rdd to flask for visualisation

'''
  From the tweets data stream, extract for each tweet the
  location, by the centre of the bounding box provided, 
  and the sentiment polarity and classification
'''
 # reduce/map the tweet to coordinates and sentiment tuple only
# send minimum information from the tweet to flask app
sentiment = tweets_coordiates. \
  map(lambda (username, coordinates, tweet_text, sentiment_level): (coordinates, sentiment_level))#.window(60*60, 2)

sentiment.pprint() # print tweets sentiment to the console
sentiment.foreachRDD(lambda rdd: rdd.foreachPartition(kafka_sender))

ssc.start() # start the stream and analysis 
ssc.awaitTermination() # terminate when forced