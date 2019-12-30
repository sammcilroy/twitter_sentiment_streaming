from flask import Flask, jsonify, request, Response, render_template
from pykafka import KafkaClient
import ast

def get_kafka_client():
    return KafkaClient(hosts='localhost:9092')

app = Flask(__name__)

trending = {'labels': [], 'counts': []}
influencers = {'labels': [], 'counts': []}

@app.route("/")
def get_dashboard_page():
	global influencers

	return render_template(
		'influencers.html',
		influencers=influencers)
 
@app.route('/topic/<topicname>')
def get_messages(topicname):
    client = get_kafka_client()
    def events():
        for i in client.topics[topicname].get_simple_consumer():
            yield 'data:{0}\n\n'.format(i.value.decode())
    return (Response(events(), mimetype="text/event-stream"))  

@app.route("/map.html")
def get_map():
    return(render_template('map.html'))

@app.route("/about.html")
def get_about_page():
    	
	return render_template('about.html')

@app.route("/hashtags.html")
def get_hashtags_page():
    global trending
    
    return render_template('hashtags.html',
    trending=trending)

@app.route('/refresh_trending')
def refresh_trending():
	global trending

	return jsonify(
		Label=trending['labels'],
		Count=trending['counts'])

@app.route('/refresh_influencers')
def refresh_influencers():
	global influencers

	return jsonify(
		Label=influencers['labels'],
		Count=influencers['counts'])

@app.route('/update_trending', methods=['POST'])
def update_trending():
	global trending
	if not request.form not in request.form:
		return "error", 400

	trending['labels'] = ast.literal_eval(request.form['label'])
	trending['counts'] = ast.literal_eval(request.form['count'])

	return "success", 201


@app.route('/update_influencers', methods=['POST'])
def update_influencers():
	global influencers
	if not request.form not in request.form:
		return "error", 400

	influencers['labels'] = ast.literal_eval(request.form['label'])
	influencers['counts'] = ast.literal_eval(request.form['count'])

	return "success", 201


if __name__ == "__main__":
	app.run(debug=True,host='0.0.0.0', port=5001)
