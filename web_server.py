from bottle import route, run, static_file, response, template
import bottle
import boto
import json
import boto.sqs
import string
import uuid, time
import boto.dynamodb2 as ddb
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.table import Table
import base64, hmac, hashlib
import urllib2
from boto.sqs.message import RawMessage

conn = boto.connect_s3()
sns = boto.connect_sns()
sqs = boto.connect_sqs()

# this must be changed 
# redirect_url = 'http://ec2-52-2-66-81.compute-1.amazonaws.com:8888/annotator/run'
redirect_url = 'http://lyc.ucmpcs.org:8888/redirect'


# for debugging
@route('/')
def index():
    return "Welcome to Web Server!"


# upload file using form
@route('/upload', method='GET')
def upload_file_to_s3():

    # define S3 policy document 
    policy = """{"expiration":"2016-07-17T12:00:00.000Z", 
            "conditions": 
            [{"bucket":"gas-inputs"},
            ["starts-with", "$key", "lyc/"],
            {"acl": "private"},
            ["starts-with", "$success_action_redirect","http://lyc.ucmpcs.org:8888/redirect"],
            {"x-amz-algorithm": "AWS2-HMAC-SHA1"}
            ]
            }"""

    # encode and sign policy document
    encoded_policy =  base64.b64encode(policy)
    signature = base64.b64encode(hmac.new(conn.aws_secret_access_key, encoded_policy, hashlib.sha1).digest())

    # Generate a unique job ID
    jobID = str(uuid.uuid4())

    # render 'upload.tpl' template and pass in variables
    return template('upload.tpl',bucket_name='gas-inputs', acl='private', algorithm='AWS2-HMAC-SHA1', aws_key=conn.aws_access_key_id, encoded_policy=encoded_policy, signature=signature, job_id = jobID, redirect_url=redirect_url)


@route("/redirect", method="GET")
def send_annotation_request():

    # Get bucket name and key from the S3 redirect URL
    bucket_name = bottle.request.query.bucket
    key = bottle.request.query.key.split('/')[1] # jobID~test.txt
    jobID = key.split('~')[0]
    file_name = key.split('~')[1]

    # Create a job item and persist it to the annotations database
    ann_table = Table('lyc-annotations', schema=[HashKey('job_id')], connection = ddb.connect_to_region('us-east-1'))
    data = {'job_id': jobID, 'username': 'lyc', 's3_inputs_bucket': bucket_name, 's3_key_input_file': 'lyc/'+key, 'input_file_name': file_name, 'submit_time': int(time.time()), 'status':'pending'}
    ann_table.put_item(data=data)


    ###------------------------------------------------------------------###
    ## Create new request that includes the same data in the body
    # url ="http://ec2-52-2-66-81.compute-1.amazonaws.com:8888/annotator/analysis"
    # headers = {'Content-Type': 'application/json'}
    # ann_request = urllib2.Request(url, json.dumps(data), headers)

    ## Send request (as an HTTP POST) to the annotator API    
    # annotator_response = urllib2.urlopen(ann_request)

    ## returns a response to the user containing the job ID and the filename
    # return annotator_response
    ###------------------------------------------------------------------###


    # publish a notification to the SNS topic
    # http://ridingpython.blogspot.com/2011/11/aws-sns-how-to-send-out-messages-to-e.html
    queue = sqs.get_queue('lyc-job-requests')

    # publishes a notification to the SNS topic
    m = RawMessage()
    m.set_body(json.dumps(data))
    queue.write(m)

    # returns a response to the user containing the job ID and the filename
    response = '{"code": "200 OK", "data": {"id": "%s", "input_file": "%s"}}' % (jobID, key)
    return response




# gets a list of objects from your S3 input bucket 
@route('/list_jobs', method='GET')
def display_files_in_s3():

    # use boto to establish connection and get 'gas-inputs' bucket
    bucket = conn.get_bucket('gas-inputs', validate=False)

    # get 'lyc' directory within the bucket, append file names in the list to response message
    response = '{"files": '
    for key in bucket.list('lyc'):
        response += key.name + ' '
    response += '}'

    return json.dumps(response)


bottle.run(host='0.0.0.0',port=8888,debug=True)