# github-repo-commits
Get commit data from a github repo

# What
It's a flask app which exposes an endpoint to query user commit data.
Returns committer logins (or name if login not found) along with commits (message and commmittedDate) per specified date frame 

# Serverless
No server, no database

    https://dzake583i3.execute-api.ap-northeast-1.amazonaws.com/dev/

# In Short
    curl -X GET \
    'https://dzake583i3.execute-api.ap-northeast-1.amazonaws.com/dev/manycoding/file-repo/commits/?since=2018-02-10&until=2018-04-10' \
    -H 'Authorization: token $token' \
    -H 'Cache-Control: no-cache' \
    -H 'Content-Type: application/json'

    If you want to run the server manually:
    * pip install -r requirements.txt
    * python server.py

# How
My goal was to make the simplest yet scalable solution, that's why I chose GraphQL to query the necessary data and service it via one endpoint and AWS to make it scallable. The AWS Lambda setup is made with Zappa.

Limitations:
* Github GraphQL API has limits 5000 points per user per hour. Each request consumes 1 point
* It takes some time to warm up AWS Lambda, the first normal request (quering commits data for a week) could take up to 
* Some repos have a solid number of commits per week, a request timeout could happen if the graphql query will take more than 30 seconds.
* AWS Lambda and the app itself has caching, so the following requests are faster  

# To Do
* Add tests
* Setup proper AWS logging, e.g. CloudWatch
* Talk about the usage and update the app accordingly. For example, I assumed to server data per committer login or name as they seemed like proper fields for the task. Perhaps other fields should be used.
* Improve the response speed if necessary.

# Examples
    curl -X GET \
      'https://dzake583i3.execute-api.ap-northeast-1.amazonaws.com/dev/manycoding/file-repo/commits/?since=2018-02-10&until=2018-04-10' \
      -H 'Authorization: token $token_value' \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' 
  
    {
        "GitHub": {
            "commits": [
                {
                    "committedDate": "2018-02-13T09:42:17Z",
                    "message": "Update README.md"
                }
            ],
            "totalCount": 1
        },
        "manycoding": {
            "commits": [
                {
                    "committedDate": "2018-02-12T11:44:11Z",
                    "message": "Implement download of any file"
                },
                {
                    "committedDate": "2018-02-12T10:04:06Z",
                    "message": "Support any file upload"
                }
            ],
            "totalCount": 2
        }
    }
