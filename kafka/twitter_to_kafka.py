from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from kafka import SimpleProducer, KafkaClient
import json
import time

access_token = "1330365234-xDjSixFZfSeboDSkHS0WgNvOu5zZw4HeUL8ijVq"
access_token_secret =  "QuhhHxIMSxVC2QhVqaxtdgZtc4pyJBWVg2C6D5IHCH9ph"
consumer_key =  "JES0pDVJW2WCscy1LhFFMxz4A"
consumer_secret =  "uOoW3PCx8nI0kIfsifXfCibYwaeMrHh73TrV2TyuILL9vR9Bdx"

# Central London Boundary Box, covers main areas of the city
london = [-0.2287, 51.4110, -0.0294, 51.5755]

class StdOutListener(StreamListener):
    def on_data(self, data):
        producer.send_messages("kafka_twitter_stream_json", data.encode('utf-8'))
        #print (data)
        return True
    def on_error(self, status):
        print (status)
    def on_limit(self,status):
        print ("Twitter API Rate Limit")
        print("Waiting...")
        time.sleep(15 * 60) # wait 15 minutes and try again
        print("Resuming")
        return True

kafka = KafkaClient("localhost:9092")
producer = SimpleProducer(kafka)
l = StdOutListener()
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
stream = Stream(auth, l, tweet_mode='extended')
stream.filter(locations=london, languages=["en"])
