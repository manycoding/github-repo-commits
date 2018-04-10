from flask import Flask, jsonify, request
from werkzeug.contrib.cache import SimpleCache
import requests
import queries
import datetime

cache = SimpleCache()

url_grapqhql_api = "https://api.github.com/graphql"


def do_post(auth_header="", url=url_grapqhql_api, payload=""):
    headers = {'Authorization': auth_header}
    # print(headers)
    # print(url)
    # print(payload)
    r = requests.post(url=url, json=payload, headers=headers)
    # print(r.status_code)
    # print(r.text)
    return r


app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


app.register_error_handler(403, lambda e: 'Wrong authorization header')
app.register_error_handler(500, lambda e: 'General error')


def update_user_data(commit_edges, filtered_users=None):
    """
    Updates or creates user commits data in JSON format
    """
    users = filtered_users if filtered_users else {}
    for commit in commit_edges:
        # print(f"EDGE {commit}")
        # print(f"EDGE type {type(commit)}")
        node = commit["node"]
        # print(f"NODE {node}")
        if node["committer"]["user"]:
            login = node["committer"]["user"]["login"]
        else:
            login = node["committer"]["name"]
        # print(f"LOGIN {login}")

        c = {}
        c["message"] = node["message"]
        c["committedDate"] = node["committedDate"]
        if login in users.keys():
            users[login]["totalCount"] += 1
            commits = users[login]["commits"]
            commits.append(c)
            users[login]["commits"] = commits
        else:
            committer = {}
            committer["totalCount"] = 1
            commits = []
            commits.append(c)
            committer["commits"] = commits
            users[login] = committer
    return users


def get_user_commits(auth_header, user, repo, since, until):
    """
    Makes a query to github GraphQL API and returns combined user
    commit data.
    Supports pagination. 
    """
    query = {'query': queries.get_commits % (user, repo, since, until, "")}
    r = do_post(auth_header=auth_header, payload=query)
    if r.status_code == 200 and "errors" not in r.json().keys():
        body = r.json()
        history = body["data"]["repository"]["ref"]["target"]["history"]

        users = update_user_data(history["edges"])
        cursor = history["pageInfo"]["endCursor"]
        has_next_page = history["pageInfo"]["hasNextPage"]
        while has_next_page:
            cursor_filter = f', after: "{cursor}"'
            query = {'query': queries.get_commits % (
                user, repo, since, until, cursor_filter)}
            r = do_post(auth_header=auth_header, payload=query)
            if r.status_code != 200 or "errors" in r.json().keys():
                return None, r.status_code, r.text

            body = r.json()
            history = body["data"]["repository"]["ref"]["target"]["history"]
            users = update_user_data(history["edges"], users)
            has_next_page = history["pageInfo"]["hasNextPage"]
            cursor = history["pageInfo"]["endCursor"]

        return users, r.status_code, r.text
    else:
        return None, r.status_code, r.text


@app.route('/<user>/<repo>/commits/')
def commits(user, repo):
    """
    Serve commits data

    parameters
    since - date filter from which the results should be fetched in
    2018-01-01 format. Default is today
    until - the date until the results should be fetched, default is today

    headers
    {'Authorization': 'token token_value'}
    token_value - a github token to access its API. The endpoint does not
    require additional permitions except basic ones
    """
    auth_header = request.headers.get('Authorization', default="")
    since = request.args.get('since', default=str(datetime.date.today()), type=str)  # noqa
    until = request.args.get('until', default=str(datetime.date.today()), type=str)  # noqa
    if not since or not until:
        raise InvalidUsage(
            "Empty sine or until parameters are not supported", status_code=422)
    since = f"{since}T00:00:00+00:00"
    until = f"{until}T23:59:59+00:00"

    cache_hash = f"{user},{repo},{since},{until}"
    commits_data = cache.get(cache_hash)
    if not commits_data:
        commits_data, status_code, text = get_user_commits(
            auth_header=auth_header,
            user=user,
            repo=repo,
            since=since,
            until=until)
        if status_code != 200:
            raise InvalidUsage(text, status_code=status_code)
        cache.set(cache_hash, commits_data, timeout=30 * 60)
    # print(f"commits data\n{commits_data}")
    return jsonify(commits_data)


if __name__ == '__main__':
    app.run()
