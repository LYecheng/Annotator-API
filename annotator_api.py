import bottle
from bottle import route, run, static_file, response, template
import boto
import json
import string
import subprocess
import uuid
import os, os.path

conn = boto.connect_s3()

# for debugging
@route('/')
def index():
    return "Welcome to anntools!"

@route('/annotator/analysis', method='POST')
def request_analysis():
    # extract the various parameters from request body
    bucket_name = bottle.request.json['s3_inputs_bucket']
    job_id = bottle.request.json['job_id']
    key = bottle.request.json['s3_key_input_file']
    filename = key.split('/')[1]

    # download the file from S3 storage
    file_key = conn.get_bucket(bucket_name,validate=False).get_key(key)
    if not os.path.exists('jobs/'+job_id):
        os.makedirs('jobs/'+job_id)
    file_key.get_contents_to_filename('jobs/'+job_id+'/'+filename)

    # Launch annotation job as a background process
    job = subprocess.Popen(['python', '/home/ubuntu/anntools/run.py', 'jobs/'+job_id+'/'+filename, "&"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print 'current file is '+filename

    # Return response to notify user of successful submission
    response.status = 200
    data = {'id': job_id, 'input_file': filename}

    return json.dumps({'code': response.status, 'data': data})


##### redirected from web server, run annotation service #####
@route('/annotator/run', method='POST')
def run():
    print bottle.request
    # parse the query string to get key and bucket name
    bucket_name = bottle.request.query.bucket
    key = bottle.request.query.key.split('/')[1] # job_id~test1.txt
    job_id = key.split('~')[0]
    print 'bucket name is '+bucket_name+', key is '+key+', job id is '+job_id

    # download the file from S3 storage
    file_key = conn.get_bucket(bucket_name,validate=False).get_key('lyc/'+key)
    if not os.path.exists('jobs/'+job_id):
        os.makedirs('jobs/'+job_id)
    file_key.get_contents_to_filename('jobs/'+job_id+'/'+key)

    # use subprocess to invoke anntools run.py on filename
    child_process = subprocess.Popen(['python', '/home/ubuntu/anntools/run.py', 'jobs/'+job_id+'/'+key.split('~')[1]])
    if child_process.poll() == None:
            HTTP_code = 200 # OK
    else:
            HTTP_code = 400 # Bad Request

    # construct the response message
    response_message = '{"status": %d, "job_id": "%s"}' % (HTTP_code, job_id)

    # convert the response type to json and return 
    return json.dumps(response_message)



##### display a list of running annotation jobs using their job ids #####
@route('/annotator/list')
def list_running_jobs():
    job_directory = 'jobs/'
    immediate_subdir = filter(os.path.isdir, [os.path.join(job_directory,f) for f in os.listdir(job_directory)])
    dirs = '; '.join(immediate_subdir)

    return json.dumps('There are '+str(len(immediate_subdir))+' running jobs (job_id): '+dirs)



bottle.run(host='0.0.0.0',port=8888,debug=True)