GitArchiveUtils
===============

Utils for handling and parsing the data from http://www.githubarchive.org/

## Sample Data

``` javascript
{
	"_id" : ObjectId("5246dfa52c771f0063065453"),
	"created_at" : "2013-09-27T23:02:32-07:00",
	"payload" : {
		"issue_id" : 20207269,
		"comment_id" : 25291706
	},
	"public" : true,
	"type" : "IssueCommentEvent",
	"url" : "https://github.com/slide/ip-test/issues/1259#issuecomment-25291706",
	"actor" : "ironpythonbot",
	"actor_attributes" : {
		"login" : "ironpythonbot",
		"type" : "User",
		"gravatar_id" : "a327bc2b03439ce3d66b251f3af2be64"
	},
	"repository" : {
		"id" : 13164458,
		"name" : "ip-test",
		"url" : "https://github.com/slide/ip-test",
		"description" : "Testing importing IronPython issues from CodePlex",
		"watchers" : 0,
		"stargazers" : 0,
		"forks" : 0,
		"fork" : false,
		"size" : 0,
		"owner" : "slide",
		"private" : false,
		"open_issues" : 468,
		"has_issues" : true,
		"has_downloads" : true,
		"has_wiki" : true,
		"created_at" : "2013-09-27T17:45:32-07:00",
		"pushed_at" : "2013-09-27T17:45:32-07:00",
		"master_branch" : "master"
	}
}
```

## Sample Queries

``` javascript
/* distribution of different events on GitHub */
db.test.aggregate({
		$group : {
			_id : "$type", 
			sum : { $sum : 1 } 
		}}, {
		$sort : { 
			sum : -1 
		}
	}
)
```