from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]

def validate_post_data(new_post):
    if (("title" not in new_post or new_post["title"] == "")
            and ("content" not in new_post or new_post["content"] == "")):
        return False
    return True


def validate_post_title(new_post):
    if "title" not in new_post or new_post["title"] == "":
        return False
    return True


def validate_post_content(new_post):
    if "content" not in new_post or new_post["content"] == "":
        return False
    return True


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    if request.method == 'POST':
        # Get new post from the user
        new_post = request.get_json()

        # Validate new post content
        if not validate_post_data(new_post):
            return jsonify({"error": "Fields 'title' and 'content' can't be empty or missing!"}), 400

        if not validate_post_title(new_post):
            return jsonify({"error": "Field 'title' can't be empty or missing!"}), 400

        if not validate_post_content(new_post):
            return jsonify({"error": "Field 'content' can't be empty or missing!"}), 400

        # Generate new ID for the new post
        new_id = max(post['id'] for post in POSTS) + 1
        new_post['id'] = new_id

        # Add new post
        POSTS.append(new_post)

        return jsonify(new_post), 201

    else:
        # Handle the GET request
        return jsonify(POSTS)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
