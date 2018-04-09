from flask import Flask, jsonify, request
from werkzeug.contrib.cache import SimpleCache
import requests
import queries

cache = SimpleCache()

url_grapqhql_api = "https://api.github.com/graphql"


def do_post(auth_header="", url=url_grapqhql_api, payload=""):
    headers = {'Authorization': auth_header}
    print(headers)
    print(url)
    print(payload)
    r = requests.post(url=url, json=payload, headers=headers)
    print(r.status_code)
    print(r.text)
    return r


def get_unique_authors(authors_data):
    author_nodes = authors_data["data"]["repository"]["ref"]["target"]["history"]["edges"] # noqa
    return set([author["node"]["author"]["email"] for author in author_nodes])


def get_author_data(auth_header, repo, user, author_email, since, until):
    author = {}
    payload = {
        'query': queries.get_commit_count % (user, repo, since, until, author_email) # noqa
    }
    r = do_post(auth_header=auth_header, payload=payload)
    if r.status_code == 200:
        history = r.json()["data"]["repository"]["ref"]["target"]["history"]
        author["totalCount"] = history["totalCount"]
        author["name"] = history["edges"][0]["node"]["author"]["name"]
        author["commits"] = get_commit_data(history["edges"])
        return author
    raise InvalidUsage(r.text, status_code=r.status_code)


def get_commit_data(commit_edges):
    commits = []
    for edge in commit_edges:
        commit = {}
        commit["message"] = edge["node"]["message"]
        commit["committedDate"] = edge["node"]["committedDate"]
        commits.append(commit)
    return commits


def serve_authors(auth_header, repo, user, since, until):
    query = {'query': queries.get_authors % (user, repo, since, until)}
    r = do_post(auth_header=auth_header, payload=query)
    if r.status_code == 200 and "errors" not in r.json().keys():
        authors = get_unique_authors(r.json())
        print(f"authors\n{authors}")
        commits = []

        for email in authors:
            author = get_author_data(
                auth_header=auth_header,
                author_email=email,
                since=since,
                until=until,
                repo=repo,
                user=user)
            commits.append(author)
        print(f"commits\n{commits}")
        return commits, r.status_code, r.text
    else:
        return None, r.status_code, r.text


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


@app.route('/<user>/<repo>/commits/')
def commits(user, repo):
    auth_header = request.headers.get('Authorization', default="")
    since = request.args.get('since', default='2018-04-06T00:00:00+00:00')
    until = request.args.get('until', default='2018-04-06T23:59:59+00:00')

    cache_hash = f"{user},{repo},{since},{until}"
    commits_data = cache.get(cache_hash)
    if not commits_data:
        commits_data, status_code, text = serve_authors(
            auth_header=auth_header,
            user=user,
            repo=repo,
            since=since,
            until=until)
        if status_code != 200 or not commits_data:
            raise InvalidUsage(text, status_code=status_code)
        cache.set(cache_hash, commits_data, timeout=30 * 60)
    print(f"commits data\n{commits_data}")
    print(f"type(commits_data) {type(commits_data)}")
    return jsonify(commits_data)


if __name__ == '__main__':
    app.run()
