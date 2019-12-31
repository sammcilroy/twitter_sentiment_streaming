## Twitter Sentiment Analysis: Big Data Streaming Processing

**Project description:** This project aims to design and implement a data intensive software application to acquire, store,
process and visualise analytics from real-time tweets generated across London. The application makes use of common
distributed computing technologies for working with large volumes of data at scale (Apache Kafka, Apache Spark), and web frameworks (Flask, JavaScript) for the visualisation of the data. The project also makes use of Containerisation/Docker to aid development and deployment.

### 1. Project Outline

The development of an end to end soultion comprised of:

1. Scalable data pipelines to collect and store real time tweets across London, utilising Apache Kafka streams
2. Scalable processing of the data collected in real time including key metrics and a sentiment analysis of each tweet collected, utilising Apache Spark Pyspark data processing
3. A web front end to display the results, running totals of top ten topics and influencers, map of london showing sentiment of tweets by location in real-time, utilising Flask and JavaScript libraries

### 2. Project Design

<img src="images/twitter_project.png?raw=true"/>

#### Stage 1: Data Ingestion

Tweepy and Kafka Python libraries are used to pull tweets as JSON objects and to create 
‘streams’ of tweets into two separate Kafka topics. The first topic will take all available tweet objects
created across London and will be used to analyse the running trending topic and tagged users. The
second topic will take all tweet object created across London where an exact coordinate is given (the
user has both opted into location sharing and is using a GPS enabled device). By definition this stream
will be slower/contain less tweets than the full stream but it will be necessary to use this stream with
known coordinates to create the sentiment map.

#### Stage 2: Data Processing and Analysis

The two Kafka topics ‘produced’ in the previous stage are ‘consumed’ by the data processing stage.
This stage utilises Apache Spark to create the running total dataframes and, in combination with the
TextBlob library will ‘produce’ a new Kafka topic stream of tweet coordinates and sentiment levels.
The two dataframes will be pushed to the front-end at regular 2 second intervals. The separate tweet
sentiment stream will be ‘consumed’ during the visualisation stage.

#### Stage 3: Front-End Visualisation

The final stage is the creation of the web front end and visualisations. A python Flask app is created to
route and collect data directly from Spark and the produced Kafka sentiment stream. Bootstrap and
CSS will be implemented to create a consistent interface to ‘store’ the three visualisations. The two
running total charts is produced with Chart.js with the sentiment map created with Leaflet.js.


### 3. Project Implementation

#### Initial Setup, Development Environment and Docker

In order to develop the applications using a consistent environment, and to be able to save and deploy
the application and its dependencies as a single unit the implementation of the project was set up and
completed in a docker image/container and hosted in a private DockerHub repository. The docker image was started from a copy of the official Ubuntu 18.04 LTS image.

Python3, Java 8 and Scala 2.11 programming environments are requirements for the project and
Apache Kafka/Spark. These were installed on the container and added to the relevant path variables.
The python environment was updated to include the required python libraries.

Apache Kafka version 2.11-2.3.0 was installed in the root directory. The command to start the
Kafka service was added to the Linux OS’ .bashrc file so that a new Kafka service is started on port
9092 at startup. The command to start the required Zoopkeeper instance on port 2181 at startup was
also added. Every time the project docker container is started the Kafka and Zookeeper services will
start automatically on these ports. Apache Spark version 2.4.3 was installed in the root
directory. Flask was installed as a standard python library. The Chart.js and Leaflet.js libraries were included
as JavaScript files so as to be referenced from code developed through Flask.

#### Data Ingestion

##### Twitter Streaming API and Kafka Topics Creation

Two Kafka topics were created which will are used to collect and store streams from the Twitter API.
The first topic, kafka_twitter_stream_json, collects all available tweets from the London Area as they
occur in real time. This gives the maximum amount of data possible for analysis. The second topic,
kafka_twitter_stream_coordinates, collects all tweets from the London Area where the exact location
coordinates of the user are known (given as a single latitude and longitude), rather than just a general
area (given as a four coordinate bounding box) which can be quite large and imprecise, often covering
large areas. This information is essential for the the sentiment map to be developed for the front-end.
However, as this information is only provided if the user has opted in to sharing their location and is
also using a GPS connected device the number of tweets with this information is far less. 

The topics were created using the Kafka script/command for topic creation:

```javascript
bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --
replication-factor 1 --partitions 1 --topic kafka_twitter_stream_json
```
Two important arguments in the topic creation process to note are the replication-factor and the number
of partitions. Basically the number of partitions is how many nodes the topic is set to be distributed
across and the replication-factor is the number of times the data is to be replicated during distribution:

<img src="images/kafka_topic.png?raw=true"/>

For development purposes in this project I am using a Docker container image with a single
Kafka/Spark node setup so the partitions and replication factor are set to 1. However, when the image
is deployed to a distributed server or cloud environment these arguments will be changed to suit.

##### Tweepy Connection, Pulling JSON Tweets and Producing as Kafka Messages

The Tweepy python library was used to create a connection to the Twitter Streaming API using the
required OAuth authentication and ‘listen’ to tweets to consume as they come in real time. 

The Tweepy Class <i>StdOutListener()</i> is used as a listener to gather new tweets. It contains three
key methods which can be overridden to customize the data collected: <i>on_data</i>, <i>on_error</i> and
<i>on_limit</i>:

```python
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
```
On each data event ‘on_data’ I am using the Kafka-Python library to create a producer and send the
tweet data as a message to the required Kafka topic:

```python
kafka = KafkaClient("localhost:9092")
producer = SimpleProducer(kafka)

def on_data(self, data):
        producer.send_messages("kafka_twitter_stream_json", data.encode('utf-8'))
```
Data is encoded as UTF-8 to ensure compatibility with non-standard tweet characters such as emojis
and tags.

Errors can be handled using the <i>on_error</i> method, I have chosen to have errors printed to the console
for testing and evaluation purposed but allow the production to continue. Non-critical errors which do
not disrupt the flow of data can be overlooked to some extent during development.

The <i>on_limit</i> method allows for working around limits set by Twitter on their Streaming API,
especially the non-paid for connections. There are arbitrary limits set by Twitter based on current usage
and capacity where a limit message is sent to a listener such as Tweepy to cut off the stream. Using the
on_limit method I have set a waiting time of 15 minutes if this should occur, at which point the stream
can resume. This is a generally accepted wait time among other developers working with Twitter data.
Using this method I have not had any issues with the stream being terminated due to a Twitter limit
message.

The Twitter Streaming API provides a stream of tweets in real time
with each tweet represented as a JSON object. Aspects of the JSON can be used to ‘filter’ the stream
based on selection criteria. Key to this project, a filter on the location information in the JSON can be
provided in the form of a ‘bounding box’ a set of four coordinates, forming a polygon, which define an
area. I have used four coordinates producing a large square over Central London and surrounding areas
of the city. This was fed into the filter argument, thus listening only for tweets from that area:

```python
# Central London Boundary Box, covers main areas of the city
london = [-0.2287, 51.4110, -0.0294, 51.5755]

stream = Stream(auth, l, tweet_mode='extended')
stream.filter(locations=london, languages=["en"])
```
To simplify the sentiment analysis process, I am also using the filter arguments to listen only for tweets
marked as English language. The tweet_mode argument for the string also allows me to pull in tweet
data with the full text of the tweet without truncation which is useful for a more accurate sentiment
analysis.

The code below summarises how the Tweepy and Kafka-Python libraries were used in collaboration
to produce a stream of all English language tweets within a chosen area, London in this case, and
produce those tweets as JSON formatted messages to Apache Kafka topic(s):

```python
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from kafka import SimpleProducer, KafkaClient
import json
import time

# Central London Boundary Box, covers main areas of the city
london = [-0.2287, 51.4110, -0.0294, 51.5755]

class StdOutListener(StreamListener):
    def on_data(self, data):
        decoded = json.loads(data)
        if decoded.get("coordinates") is not None:
            producer.send_messages("kafka_twitter_stream_coordinates", data.encode('utf-8'))
        #print (data)
        return True
    def on_error(self, status):
        print (status)
    def on_limit(self,status):
        print ("Twitter API Rate Limit")
        print("Waiting...")
        time.sleep(15 * 60) # wait 5 minutes and try again
        print("Resuming")
        return True

kafka = KafkaClient("localhost:9092")
producer = SimpleProducer(kafka)
l = StdOutListener()
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
stream = Stream(auth, l, tweet_mode='extended')
stream.filter(locations=london, languages=["en"])
```
Two Apache Kafka topics were created to collect and store the JSON formatted
tweets. The Kafka ‘Console Consumer’ script was be used to consume and display the contents of
topics in the terminal, this was useful to show the data being collected was correct:




















For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).
