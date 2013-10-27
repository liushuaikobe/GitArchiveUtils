import simplejson
import argparse
import time

class StatisticsTimeline(object):
	'''
	Statistics the key of the json data.
	'''
	def __init__(self, json_file):
		self.json_file = json_file
		self.total_json_nums = 0
		self.top_key = {}
		self.top_key_timecost = 0

	def statistics_top_keys(self):
		'''
		statistics keys in top level.
		'''
		start = time.time()
		for json in self.json_file:
			self.total_json_nums += 1
			json_dict = simplejson.loads(json)
			# if 'repository' not in json_dict:
			# 	print self.total_json_nums
			for key in json_dict:
				if key in self.top_key:
					self.top_key[key] += 1
				else:
					self.top_key[key] = 1
		complete = time.time()
		self.top_key_timecost = complete - start

	def output_top_keys_result(self, indent = 4, seperator=' '):
		'''
		print the result of top key statistics in a human-friendly format
		'''
		max_len_1 = 0
		max_len_2 = 0
		for key in self.top_key:
			max_len_1 = len(key) if len(key) > max_len_1 else max_len_1
		for value in self.top_key.values():
			tmp_s = str(value)
			max_len_2 = len(tmp_s) if len(tmp_s) > max_len_2 else max_len_2 
		print '-' * 80
		for key in self.top_key:
			seperator_num_1 = indent + (max_len_1 - len(key))
			seperator_num_2 = indent + (max_len_2 - len(str(self.top_key[key])))
			rate = float(self.top_key[key]) / float(self.total_json_nums) * 100
			print ''.join((key, seperator * seperator_num_1, str(self.top_key[key]), seperator * seperator_num_2, str(rate), '%'))
		print '-' * 80
		print self.total_json_nums, 'lines,', self.top_key_timecost, 'seconds.' 

	def get_top_keys(self):
		return self.top_key

	def get_total_json_nums(self):
		return self.total_json_nums


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('file', help='sorce file including json string for each line.')

	args = parser.parse_args()

	try:
		json_file = open(args.file, 'r')
		s = StatisticsTimeline(json_file)
	except IOError:
		print 'json file does not exsit.'
		return 

	s.statistics_top_keys()
	s.output_top_keys_result()

	if json_file:
		json_file.close()

if __name__ == '__main__':
	main()