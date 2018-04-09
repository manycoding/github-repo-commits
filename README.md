# github-repo-commits
Get commit data from a github repo

# What

    It's a flask app which exposes an endpoint to query user commit data. I used caching, so the first query could take up to 30 seconds.

# Serverless

No server, no database

    https://dzake583i3.execute-api.ap-northeast-1.amazonaws.com/dev/

# In Short

    curl -X GET \
    'https://dzake583i3.execute-api.ap-northeast-1.amazonaws.com/dev/torvalds/linux/commits/?since=2018-04-07T00:00:00%2B00:00&until=2018-04-07T23:59:59%2B00:00' \
    -H 'Authorization: token $token' \
    -H 'Cache-Control: no-cache' \
    -H 'Content-Type: application/json'

    If you want to run manually, which is not recommended:
    * Install requirements.txt
    * python server.py

# Explanation of architecture and API design
    My goal was to make the simplest yet scalable solution, that's why I chose GraphQL to query the necessary data and service it via one endpoint and AWS to make it scallable.

    Making a query 

# If you had more time, what would you like to improve?