from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
SWAGGER_URL="/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL="/static/my_blog_api.json" # (2) ensure you create this dir and file

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'My Blog API' # (3) You can change this if you like
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
    {"id": 3, "title": "Testing search", "content": "I love python"},
]


def validate_new_post_data(new_post: dict):
    errors = []

    if not new_post:
        errors.append("Request body cannot be empty.")
        return False, errors

    if "title" not in new_post or not new_post["title"]:
        errors.append("Field 'title' is missing or empty.")
    if "content" not in new_post or not new_post["content"]:
        errors.append("Field 'content' is missing or empty.")

    if errors:

        return False, errors

    return True, []


def validate_update_post_data(new_data: dict):
    errors = []

    if "title" in new_data and not new_data["title"]:
        errors.append("Field 'title' is empty.")
    if "content" in new_data and not new_data["content"]:
        errors.append("Field 'content' is empty.")

    if errors:

        return False, errors

    return True, []


def find_post_by_id(id: int):
    for post in POSTS:
        if post["id"] == id:

            return post


def search_posts_data(title: str = None, content: str = None):
    search_results = set()

    lower_title = title.lower() if title else None
    lower_content = content.lower() if content else None

    for post in POSTS:
        match = False
        post_title_lower = post.get("title").lower()
        post_content_lower = post.get("content").lower()

        if lower_title and lower_title in post_title_lower:
            match = True
        if lower_content and lower_content in post_content_lower:
            match = True

        if match:
            search_results.add(tuple(post.items()))

    return [dict(item) for item in search_results]


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    if request.method == 'POST':
        # Get new post from the user
        new_post = request.get_json()

        # Validate new post content
        is_valid, errors = validate_new_post_data(new_post)

        if not is_valid:

            return jsonify({"error(s)": errors}), 400

        # Generate new ID for the new post
        new_id = max(post['id'] for post in POSTS) + 1
        new_post['id'] = new_id

        # Add new post
        POSTS.append(new_post)

        return jsonify(new_post), 201

    else:
        # Handle the GET request
        sort_by = request.args.get('sort')
        direction = request.args.get('direction')

        valid_sort_fields = {"title", "content"}
        valid_direction_fields = {"asc", "desc"}

        if sort_by is not None or direction is not None:
            if sort_by not in valid_sort_fields or direction not in valid_direction_fields:
                return jsonify({"error": "Invalid sorting parameters. "
                                     "Use 'sort' (title, content) and 'direction (asc, desc)"}), 400

            sorting = (direction == "desc")
            sorted_posts = sorted(POSTS, key=lambda post: post.get(sort_by, ''), reverse=sorting)

            return jsonify(sorted_posts), 200

        else:

            return jsonify(POSTS), 200


@app.route('/api/posts/<int:id>', methods=['DELETE', 'PUT'])
def handle_endpoint(id):
    # Find the post based on given ID
    post = find_post_by_id(id)

    # If not found, return 404 error
    if not post:

        return jsonify({"error": f"Post with id {id} not found."}), 404

    if request.method == 'DELETE':

        return delete_post(id, post)

    if request.method == 'PUT':

        return update_post(post)


def delete_post(id, post):
    # Delete post
    POSTS.remove(post)

    # Return the deleted post
    return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200


def update_post(post):
    # Update post
    new_data = request.get_json()

    # Validate update post content
    is_valid, errors = validate_update_post_data(new_data)
    if not is_valid:

        return jsonify({"error(s)": errors}), 400

    # Update post
    post.update(new_data)

    # Return the updated post
    return jsonify(post)


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    title = request.args.get('title')
    content = request.args.get('content')

    search_results = search_posts_data(title, content)

    return jsonify(search_results), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
