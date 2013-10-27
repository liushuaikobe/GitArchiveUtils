'''
make the raw json file without indent more human-friendly.
'''
import argparse
import simplejson
import sys

# json = '{"created_at":"2013-08-05T20:03:01-07:00","payload":{"shas":[["b0e4c8e153a9cfce9581198cafa54e2f95ff0062","timothy_lachlan_elson@hotmail.com","removing mouse scrolling for mac","tim.elson",true]],"size":1,"ref":"refs/heads/master","head":"b0e4c8e153a9cfce9581198cafa54e2f95ff0062"},"public":true,"type":"PushEvent","url":"https://github.com/telson/dotfiles/compare/718c6c735e...b0e4c8e153","actor":"telson","actor_attributes":{"login":"telson","type":"User","gravatar_id":"9e0958a20a74e717d17ca7aa904a2f22","name":"Tim","email":"timothy_lachlan_elson@hotmail.com"},"repository":{"id":9878983,"name":"dotfiles","url":"https://github.com/telson/dotfiles","description":"repo of home dir configs","watchers":0,"stargazers":0,"forks":0,"fork":false,"size":188,"owner":"telson","private":false,"open_issues":0,"has_issues":true,"has_downloads":true,"has_wiki":true,"language":"Shell","created_at":"2013-05-05T20:54:23-07:00","pushed_at":"2013-08-05T20:03:00-07:00","master_branch":"master"}}'
def parse_json_str(json_str, indent_num=4, indent_str=' '):
	return simplejson.dumps(simplejson.loads(json_str), indent=indent_num * indent_str)

def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('file', help='sorce file including json string for each line.')

	parser.add_argument('-l', '--line', help='which line to parse.', type=int)
	parser.add_argument('-n', '--num', help='how much line that be parsed.', type=int)
	parser.add_argument('-o', '--output', help='where the result be output(default the std out).')
	args = parser.parse_args()
	
	try:
		json_file = open(args.file)
	except Exception, e:
		print 'no such file!'
		return
	result_file = None
	try:
		if args.output:
			result_file = open(args.output + 'result_json.json', 'w+')
			sys.stdout = result_file
	except Exception, e:
		print 'cant create file in', args.output
	
	if args.line:
		# the line is given
		for i in xrange(args.line - 1):
			json_file.readline()
		print parse_json_str(json_file.readline())
	elif args.num:
		# the first num lines
		for i in xrange(args.num):
			print parse_json_str(json_file.readline())
	else:
		# all lines
		for line in json_file.readlines():
			line = parse_json_str(line)
			print line

	if result_file:
		result_file.close()
	if json_file:
		json_file.close()

if __name__ == '__main__':
	main()

