import sys
import time
import driver
import boto
from boto.s3.key import Key
import shutil
import boto.dynamodb2 as ddb
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.table import Table

# A rudimentary times for coarse-grained profiling
class Timer(object):
        def __init__(self, verbose=False):
                self.verbose = verbose

        def __enter__(self):
                self.start = time.time()
                return self

        def __exit__(self, *args):
                self.end = time.time()
                self.secs = self.end - self.start
                self.msecs = self.secs * 1000  # millisecs
                if self.verbose:
                        print 'elapsed time: %f ms' % self.msecs

if __name__ == '__main__':
        # Call the AnnTools pipeline
        if len(sys.argv) > 1:
                input_file_name = sys.argv[1]
                with Timer() as t:
                        driver.run(input_file_name, 'vcf')
                print "input file is " + input_file_name
                print "Total runtime: %s seconds" % t.secs

                # Save results file and log file to S3 results bucket
                conn = boto.connect_s3()
                k = Key(conn.get_bucket('gas-results', validate=False))

                # copy all three files to the bucket
                k.key = 'lyc/'+input_file_name
                k.set_contents_from_filename(input_file_name)
                k.key = 'lyc/'+input_file_name.split('.')[0]+'.annot.vcf'
                k.set_contents_from_filename(input_file_name.split('.')[0]+'.annot.vcf')
                k.key = 'lyc/'+input_file_name+'.count.log'
                k.set_contents_from_filename(input_file_name+'.count.log')
                print 'result files copied to gas-results'

                # delete the directory in the instance
                job_id = input_file_name.split('/')[1]
                shutil.rmtree('jobs/'+job_id+'/')
                print 'job file deleted from instance'

                # update the item in DynamoDB
                ann_table = Table('lyc-annotations', schema=[HashKey('job_id')], connection = ddb.connect_to_region('us-east-1'))
                item = ann_table.get_item(job_id=job_id)
                item['s3_results_bucket'] = 'gas-results'
                item['s3_key_result_file'] = 'lyc/'+input_file_name.split('.')[0]+'.annot.vcf'
                item['s3_key_log_file'] = 'lyc/'+input_file_name+'.count.log'
                item['complete_time'] = int(time.time())
                item['status'] = 'completed'
                item.partial_save()
                print 'job information updated in DB'

        else:
                print 'A valid .vcf file must be provided as input to this program.'