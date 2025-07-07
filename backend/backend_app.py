"""
My Blogs app
by Ed Groell
Latest: 07-JUL-2025
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from data_access import PostRepository, PostNotFound, ValidationError

app = Flask(__name__)
CORS(app)

# --- Swagger UI Setup ---
SWAGGER_URL = "/api/docs"
API_URL = "/static/my_blogs.json"
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'My Blogs'}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# --- Initialize the Data Access Layer ---
post_repository = PostRepository(posts_file='posts.json')


@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts() -> Response:
    """
    Handles fetching all posts and creating a new post.
    GET /api/posts?sort=<field>&direction=<asc|desc>
    POST /api/posts
    """
    if request.method == 'POST':
        try:
            new_post_data = request.get_json()
            created_post = post_repository.add(new_post_data)

            return jsonify(created_post), 201

        except ValidationError as e:

            return jsonify({"error": str(e)}), 400

        except Exception as e:

            return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    else:  # GET
        try:
            sort_by = request.args.get('sort')
            direction = request.args.get('direction', 'asc')
            posts = post_repository.get_all(sort_by=sort_by, direction=direction)

            return jsonify(posts), 200

        except ValueError as e:

            return jsonify({"error": str(e)}), 400


@app.route('/api/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_post(post_id: int) -> Response:
    """ Handles operations on a single post: fetch, update, or delete. """
    if request.method == 'GET':
        try:
            post = post_repository.get_by_id(post_id)

            return jsonify(post), 200

        except PostNotFound as e:

            return jsonify({"error": str(e)}), 404

    if request.method == 'PUT':
        try:
            update_data = request.get_json()
            if not update_data:

                return jsonify({"error": "Request body cannot be empty."}), 400

            updated_post = post_repository.update(post_id, update_data)

            return jsonify(updated_post), 200

        except (PostNotFound, ValidationError) as e:
            status = 404 if isinstance(e, PostNotFound) else 400

            return jsonify({"error": str(e)}), status

    if request.method == 'DELETE':
        try:
            post_repository.delete(post_id)

            return jsonify({"message": f"Post with id {post_id} deleted."}), 200

        except PostNotFound as e:

            return jsonify({"error": str(e)}), 404


@app.route('/api/posts/search', methods=['GET'])
def search_posts() -> Response:
    """
    Searches for posts based on query parameters.
    e.g., /api/posts/search?title=...&author=...&date=YYYY-MM-DD
    """
    params = {
        'title': request.args.get('title'),
        'content': request.args.get('content'),
        'author': request.args.get('author'),
        'date': request.args.get('date')
    }
    search_criteria = {k: v for k, v in params.items() if v is not None}

    if not search_criteria:
        return jsonify({"error": "At least one search parameter is required."}), 400

    results = post_repository.search(**search_criteria)
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)