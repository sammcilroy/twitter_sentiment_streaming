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



### 2. Assess assumptions on which statistical inference will be based

```javascript
if (isAwesome){
  return true
}
```

### 3. Support the selection of appropriate statistical tools and techniques

<img src="images/dummy_thumbnail.jpg?raw=true"/>

### 4. Provide a basis for further data collection through surveys or experiments

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. 

For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).
