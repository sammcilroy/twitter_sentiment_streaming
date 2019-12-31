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

<img src="images/kafka_console.png?raw=true"/>

At this stage, the two Apache Kafka topics are being produced to successfully, containing stream of JSON
tweet data from the London area. These topics represent the data in real time and are the basis for the
next stage of data processing and analysis.

##### Data Processing and Analysis

For the data processing and analysis stage, the tweets being produced to the two Apache Kafka topics are consumed using the Kafka-Python library and analysed in Apache Spark and TextBlob to create three outputs:

* an Apache Spark DataFrame (RDD), created every 2 seconds, showing the top ten trending
topics in London, indicated by tweet text beginning with a hashtag #. Each RDD is then sent to
Flask.

* an Apache Spark DataFrame (RDD), created every 2 seconds, showing the top ten influential
users in London, indicated by tweet text beginning with a user tag @, indicating that the tweet
is referencing that user. Each RDD is then sent to Flask.

* an Apache Spark DataFrame (RDD), created every 2 seconds, showing tweet coordinates and
analysed polarity and sentiment levels for every tweet processed. This is then ‘produced’, using
Kafka-Python, to a new Apache Kafka topic which will form a real time stream of tweet
locations and corresponding polarity and sentiment levels to be pulled and visualised by the
Flask/Leaflet.js London sentiment map.


##### Consuming Kafka Topics, Data Collection and Preparation

The PySpark library was used to create a direct stream from the Apache Kafka topics collecting and
storing the tweet data:

```python
from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

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
```
The required data fields from the JSON structure were pulled into Spark Resilient Distributed Datasets
(RDDs) for processing. The user, location, and text data were collected:

```python
'''
        Tweets are coming in from the Kafka topic in large json blocks, extract the username, location
        and contents of the tweets as json objects.
        Basic dataframe for analysis.
'''
tweets = kafkaStream. \
        map(lambda (key, value): json.loads(value)). \
        map(lambda json_object: (json_object["user"]["screen_name"],
                bounding_box(json_object["place"]["bounding_box"]["coordinates"]),
					clean_text(json_object["text"]), 
                    tweet_sentiment(clean_text(json_object["text"]))))
```

Actions were performed on the text using python functions, to clean the text formatting, determine
coordinates if no exact were given and to determine the sentiment and polarity. In order to reuse the same data to continually refresh the analysis, the dataframes were retained in persistent memory and disk:


```python
tweets.persist(StorageLevel.MEMORY_AND_DISK)
```
A similar process was used to collect and persistently store the exact coordinate data as a dataframe:


```python
tweets_coordiates = kafkaStreamCoords. \
        map(lambda (key, value): json.loads(value)). \
        map(lambda json_object: (json_object["user"]["screen_name"],
			json_object["coordinates"]["coordinates"],
			clean_text(json_object["text"]),tweet_sentiment(clean_text(json_object["text"]))))
        
tweets_coordiates.pprint(10)
tweets_coordiates.persist(StorageLevel.MEMORY_AND_DISK)
```

##### Data Processing, Apache Spark Analytics

###### Running Totals Data

The tweets dataframe was used to generate a continued ordered count of hashtag
topics and tagged users in the text field of the tweets:

```python
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
```
The tweets dataframe was transformed into continually updating micro RDDs. The text was split into
its constituent words, words indicating @users or hashtags # (as in the above code example) were
retained, and a running total maintained. A window of 24 hours is also given with an interval of two
seconds, refreshing the data continuously for a one day period. I then used PySpark pprint() functions to view the running totals being successfully populated when the code is run through Spark:

```python
trending.pprint(10) # print the current top ten hashtags to the console
```
The top ten from each of the two running totals could then be viewed through the terminal to monitor
the data being produced as expected:

<img src="images/spark_console.png?raw=true"/>

Once the running totals were confirmed to be collating successfully as expected, functionality was
added to push the data to Flask, through API endpoints. For each RDD generated, i.e. the current sorted hashtags/tagged users every 2 seconds, the RDD was passed into the below function, taking the top 10 entries, splitting the data into 2 arrays representing the labels and counts and posted using the Python requests library to the Flask API:

```python
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
```
As the script, and the Flask application, are running, the data can be viewed as the expected two arrays
into the Flask API endpoint using a browser window:

<img src="images/flask_endpoint.png?raw=true"/>


##### Sentiment Analysis

The sentiment analysis map will plot
points based on the known coordinates of the user/tweet and to color code the markers based on how
positive or negative the sentiment of the text is.
The TextBlob Python library sentiment method returns a polarity score as a continuous value
between -1 (very negative) and 1 (very positive). The values are derived from a NaiveBayes text
classification algorithm trained on labeled movie reviews texts. 

The TextBlob sentiment method was used create my own custom method to sort tweet text into five
distinct categories: very positive, positive, neutral, negative and very negative. These values will
correspond to the colouring chosen for the sentiment map. These colours will show at a glance the
general sentiment across different areas of the city as the tweets analysed builds up over time during the
course of 24 hours.

```python
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
```
As tweets are consumed from the Apache Kafka topic this method is immediately applied to the text as
the Spark RDDs are created:

```python
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
	clean_text(json_object["text"]),
	tweet_sentiment(clean_text(json_object["text"]))))
        
tweets_coordiates.pprint(10)
tweets_coordiates.persist(StorageLevel.MEMORY_AND_DISK)
```
The coordinates and sentiment are then fed into a new Apache Kafka topic which forms the real-
time feed on the sentiment analysis London map:

<img src="images/sentiment_console.png?raw=true"/>

As previously, the Kafka-Python library is used to create the Kafka producer. A custom function was
created to create the producer and send messages to the topic:

```python
'''
  From the tweets data stream, extract for each tweet the
  location, by the centre of the bounding box provided, 
  and the sentiment polarity and classification
'''
 # reduce/map the tweet to coordinates and sentiment tuple only
# send minimum information from the tweet to flask app
sentiment = tweets_coordiates. \
map(lambda (username,coordinates,
	    tweet_text,sentiment_level):(coordinates,
	                                 sentiment_level)).window(60*60,2)

sentiment.pprint() # print tweets sentiment to the console
sentiment.foreachRDD(lambda rdd: rdd.foreachPartition(kafka_sender))
```
At this stage in the implementation process the data has been shown to be successfully produced and
consumed. The running top ten trending hashtags and tagged influential users are being produced every
2 seconds and being successfully passed as arrays to the relevant Flask API endpoints. The sentiment
analysis classifications and locations of each tweet are being successfully produced to an Apache Kafka
topic.

##### Front-end Visualisations

For the front-end visualisation production stage, data is pushed from the the Apache Spark processes
both directly to Flask, for the running total dataframes, and into an
Apache Kafka topic for the real-time sentiment analysis mapping.

Flask forms the basis of the web front end and data collection routes and the visualisations are
produced using JavaScript libraries, Chart.js and Leaflet.js.
This stage has the following general outputs:

* A web based front end, built on Python’s Flask, capable of collecting and storing data and
hosting visualisations
* Navigation and user interface features, CSS and Bootstrap theming
* A bar-chart visualisation, updating every 2 seconds, showing the current top ten trending topics
from London based tweets, based on hashtags in tweet text
* A bar-chart visualisation, updating every 2 seconds, showing the current top ten influential
twitter users in London, based on users being tagged in London based tweet text
* An interactive map of London, showing in real time (as tweets are produced) the location of the
tweet marked on the map, with markers colour coded to sentiment classification. This is
designed to build up over time and show the general sentiment levels across London areas.

##### Flask Implementation

The Flask web application framework was implemented to handle the server side processing of data, to
map the request routes and to define the HTTP routes of the web front end interface and visualisations.
The Flask app was initialised and global variables were created to hold the data pushed from Spark to
populate the running total bar charts:

```python
from flask import Flask, jsonify, request, Response, render_template
from pykafka import KafkaClient
import ast

def get_kafka_client():
    return KafkaClient(hosts='localhost:9092')

app = Flask(__name__)

trending = {'labels': [], 'counts': []}
influencers = {'labels': [], 'counts': []}
```
Flask API endpoints were defined to update data pushed from Spark in the data analytics phase. The
global variables are populated with this data as it is pushed using the Python ast library to interact with
the request data:

```python
@app.route('/update_trending', methods=['POST'])
def update_trending():
	global trending
	if not request.form not in request.form:
		return "error", 400

	trending['labels'] = ast.literal_eval(request.form['label'])
	trending['counts'] = ast.literal_eval(request.form['count'])

	return "success", 201
```
The data could then be viewed populating in the browser against that route:

<img src="images/flask_route.png?raw=true"/>

Routes were then set up to give access to the data for the charts by providing routes to the global
variables which can be then used in the JavaScript chart definitions:

```python
@app.route('/refresh_trending')
def refresh_trending():
	global trending

	return jsonify(
		Label=trending['labels'],
		Count=trending['counts'])
```

as well as routes for the HTML pages/site navigation:

```python
@app.route("/hashtags.html")
def get_hashtags_page():
    global trending
    
    return render_template('hashtags.html',
    trending=trending)
```

To produce the real-time sentiment map I also required a route set up to collect data from Apache
Kafka topics. The below custom route uses server-sent events to collect data from any running Kafka
topic into the specified route:

```python
@app.route('/topic/<topicname>')
def get_messages(topicname):
    client = get_kafka_client()
    def events():
        for i in client.topics[topicname].get_simple_consumer():
            yield 'data:{0}\n\n'.format(i.value.decode())
    return (Response(events(), mimetype="text/event-stream"))  
```
Data from running Kafka topics can then be seen populating in the browser. Below is the Kafka stream
used to populate the sentiment map:

<img src="images/sentiment_browser.png?raw=true"/>

##### Chart.js Visualisations

Chart.js was implemented to use JavaScript to create the running total bar charts connected to the data
coming into the API endpoints set up in the previous section:

```javascript
var ctx = document.getElementById('trending_chart').getContext('2d');
var trending_chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Hashtags',
            data: [],
            backgroundColor:' #af90ca',
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                    callback: function(value) {if (value % 1 === 0) {return value;}}
                }
            }]
        }
    }
});
```
JavaScript was used to populate arrays with the array data stored in the API endpoints and to use these
to populate the labels and data arrays attached to the chart. This was set to repeat every 2 seconds. In
this way the chart’s data arrays would be populated with new top 10 data each time:

```javascript
var src_data_trending= {
    labels: [],
    counts: []
}

setInterval(function(){
    $.getJSON('/refresh_trending', {
    }, function(data) {
        src_data_trending.labels = data.Label;
        src_data_trending.counts = data.Count;
    });
    trending_chart.data.labels = src_data_trending.labels;
    trending_chart.data.datasets[0].data = src_data_trending.counts;
    trending_chart.update();
},2000);
```
Links to the chart JavaScript files were embedded into the relevant HTML pages for display in the
browser:

<img src="images/influencers_chart.png?raw=true"/>

<img src="images/webpage.png?raw=true"/>


##### London Sentiment Map, Leaflet.js

JavaScript employing the Leaflet.js library was applied to the production of the London Sentiment
Map. Leaflet.js works in conjunction with the mapbox API to display and append to open source maps
in the browser. I set up a JavaScript/Leaflet.js script to connect to the mapbox API and display a map of
London:


```javascript
var mymap = L.map('mapid').setView([51.505, -0.09], 11);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
	attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, 
	<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, 
	Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
	maxZoom: 18,
	id: 'mapbox.streets',
	accessToken: 'pk.eyJ1Ijoic2FtbWNpbHJveSIsImEiOiJjazA5aTdkaTMwOGZ3M3BtcTIzbWVvd2VmIn0.eOXHT1jSc7Ut92BvnhJGJQ'
}).addTo(mymap);
```
<img src="images/london_map.png?raw=true"/>

Leaflet.js allows for custom markers to be added to coordinates on the map with user defined colours
and messages:

<img src="images/leaflet_popup.png?raw=true"/>

I added to the map’s script a connection to the Kafka topic API endpoint data source, as detailed
previously, and to extract latitude, longitude, polarity and sentiment as separate variables by cleaning
and splitting the data into arrays and indexing:

```javascript
var source = new EventSource('/topic/twitter_sentiment_stream');
source.onmessage = function(event) {
  obj = String(event.data);
  var strnew = obj.replace(/[{()}]/g, '').replace(/[\[\]']+/g,'');
  var elems = strnew.split(',');
  var lat = elems[1];
  var long = elems[0];
  var pol = elems[2];
  var sent = elems[3].trim();
  console.log(lat + ' ' + long + ' ' + pol+ ' ' + sent);
```
I then added an if then else statement to populate the map with a marker at each coordinate with the
colour and pop up text changing based on sentiment:

```javascript
if (sent.valueOf() == "very positive") {
    var circle = L.circle([lat, long], {
      color: '#50cc1b',
      fillColor: '#8bde68',
      fillOpacity: 0.5,
      radius: 200,
      title: "very positive"
    }).addTo(mymap);
```
A link to the sentiment map JavaScript file was then embedded into the an HTML page for display in
the browser:

<img src="images/sentiment_map.png?raw=true"/>

Viewing the map in the browser we can see the tweets being populated as markers based on their
position. Their colour is set based on their sentiment, ranging from dark green, light green, yellow,
blue, to red representing very positive, positive, neutral, negative and very negative. Clicking on a
marker displays a popup showing the sentiment and associated polarity.

As points begin to build and cluster on the map it begins to create a visualisation indicating general
positive or negative sentiment levels across London. The screenshot above shows data collecting for
about an hour.
