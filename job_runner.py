from bottle import route, run, static_file, response, template
import bottle
import boto
import boto.sqs
import json
import string
from boto.sqs.message import RawMessage
import signal
import os, subprocess

# Connect to SQS and get the message queue
conn = boto.connect_s3()
sqs = boto.connect_sqs()
queue = sqs.get_queue('lyc-job-requests')

# Poll the message queue in a loop 
while queue:
    global msg
    # Set wait_time_seconds = 20 for your read; this matches the queue limit
    wait_time_seconds = 20
    # Attempt to read a message from the queue
    try:
        msg = queue.read(20)

        msg_body = json.loads(msg.get_body())

        # If a message was read, extract job parameters from the message body
        bucket_name = msg_body['s3_inputs_bucket']
        job_id = msg_body['job_id']
        key = msg_body['s3_key_input_file']
        filename = key.split('/')[1]

        # download the file from S3 storage
        file_key = conn.get_bucket(bucket_name,validate=False).get_key(key)
        if not os.path.exists('jobs/'+job_id):
            os.makedirs('jobs/'+job_id)
        file_key.get_contents_to_filename('jobs/'+job_id+'/'+filename)

        # Launch annotation job as a background process
        job = subprocess.Popen(['python', '/home/ubuntu/anntools/run.py', 'jobs/'+job_id+'/'+filename, "&"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print 'job '+job_id+' is running...'

        # Delete the message from the queue
        queue.delete_message(msg)
        print 'message deleted from queue'

    # If no message was read, continue polling loop
    except:
        continue

