# Copyright (C) 2011-2015 Vas Vasiliadis
# University of Chicago
##
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import sys
import time
import driver

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

		# Save results file and log file to S3 results bucket

	else:
		print 'A valid .vcf file must be provided as input to this program.'