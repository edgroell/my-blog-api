from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


def validate_post_data(new_post: dict):
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


def find_post_by_id(id: int):
    for post in POSTS:
        if post["id"] == id:
            return post


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    if request.method == 'POST':
        # Get new post from the user
        new_post = request.get_json()

        # Validate new post content
        is_valid, errors = validate_post_data(new_post)

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
        return jsonify(POSTS)


@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    # Find the post based on given ID
    post = find_post_by_id(id)

    # If not found, return 404 error
    if not post:
        return jsonify({"error": f"No post with id {id} found."}), 404

    # Delete post
    POSTS.remove(post)

    # Return the deleted post
    return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
