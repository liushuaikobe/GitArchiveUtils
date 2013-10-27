from __future__ import division
import os
import simplejson
import argparse

Events = ['CommitCommentEvent', 'CreateEvent', 'DeleteEvent', 'DownloadEvent', 'FollowEvent', \
			'ForkEvent', 'ForkApplyEvent', 'GistEvent', 'GollumEvent', 'IssueCommentEvent', \
			'IssuesEvent', 'MemberEvent', 'PublicEvent', 'PullRequestEvent', 'PullRequestReviewCommentEvent', \
			'PushEvent', 'TeamAddEvent', 'WatchEvent']

class EventFilter(object):
	Event_Name = ''

	def __init__(self, origin_file, origin_file_path, bad_event='GistEvent'):
		# the handle of of the origin file
		self.origin_file = origin_file
		# the full path of the origin file
		self.origin_file_path = origin_file_path
		# the base dir and the file name of the origin file
		self.origin_file_dir, self.origin_file_name = os.path.split(origin_file_path)
		# the total json count in origin file
		self.total_num = 0
		# the json count after filtering
		self.good_num = 0
		# the size of the origin file
		self.origin_size = self.get_file_size(self.origin_file_path)
		# the size of the target file
		self.target_size = 0.0
		# tag
		EventFilter.Event_Name = bad_event

	def filtering(self):
		targt_file_path = ''.join((self.origin_file_dir, '/', 'temp.json'))

		target_file = open(targt_file_path, 'w+')

		for json in self.origin_file:
			self.total_num += 1
			json_dict = simplejson.loads(json)
			if json_dict['type'] != EventFilter.Event_Name:
				self.good_num += 1
				target_file.write(json)

		self.origin_file.close()
		os.remove(self.origin_file_path)
		
		target_file.close()
		os.rename(targt_file_path, self.origin_file_path)
		self.target_size = self.get_file_size(self.origin_file_path)

	def get_file_size(self, file_path):
		return round(os.path.getsize(file_path) / 1024 / 1024, 2)

	def output_filtering_result(self):
		print self.total_num, 'total,', self.total_num - self.good_num, 'cut,', self.good_num, 'remain.'
		print self.origin_size, 'Mb to', self.target_size, 'Mb.'



def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('file', help='origin file to be filted.')
	parser.add_argument('-e', '--event', help='event that you don\'t need.', choices=Events)

	args = parser.parse_args()

	try:
		origin_file = open(args.file)
		if args.event:
			event_filter = EventFilter(origin_file, os.path.abspath(args.file), args.event)
		else:	
			event_filter = EventFilter(origin_file, os.path.abspath(args.file))
	except IOError:
		print 'Json file does not exsit.'
		return

	event_filter.filtering()
	event_filter.output_filtering_result()


if __name__ == '__main__':
	main()




		
