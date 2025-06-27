import os
import json
from datetime import datetime

from flask import Flask, jsonify, request, Response
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

POSTS_FILE = 'posts.json'

POSTS = []


def load_data() -> None:
    """
    Loads posts from the posts.json file.
    Converts date strings to datetime objects.
    Initializes the file with empty list if it doesn't exist.
    """
    global POSTS
    if not os.path.exists(POSTS_FILE):
        # If file doesn't exist, create with an empty JSON list
        print(f"'{POSTS_FILE}' not found. Creating an empty file.")
        with open(POSTS_FILE, "w", encoding="utf-8") as handle:
            json.dump([], handle)

        POSTS = []

        return

    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as handle:
            posts_data = json.load(handle)

            loaded_posts = []
            for post in posts_data:
                if "date" in post and isinstance(post['date'], str):
                    try:
                        post["date"] = datetime.fromisoformat(post["date"])
                    except ValueError as e:
                        print(
                            f"Warning: Could not get date '{post['date']}' for post ID {post.get('id')}: {e}. Keeping as string.")

                loaded_posts.append(post)

            POSTS.clear()
            POSTS.extend(loaded_posts)

        print(f"Successfully loaded {len(POSTS)} posts from '{POSTS_FILE}'.")

    except Exception as e:
        print(f"An unexpected error occurred while loading posts: {e}. Initializing with empty posts.")
        POSTS.clear()


def save_posts():
    """
    Saves the current in-memory POSTS list to the posts.json file.
    Converts datetime objects to strings.
    """
    posts_to_save = []

    for post in POSTS:
        post_copy = post.copy()
        if 'date' in post_copy and isinstance(post_copy['date'], datetime):
            post_copy['date'] = post_copy['date'].isoformat()
        posts_to_save.append(post_copy)

    try:
        with open(POSTS_FILE, "w", encoding="utf-8") as handle:
            json.dump(posts_to_save, handle, indent=4)

        print(f"Successfully saved {len(POSTS)} posts to '{POSTS_FILE}'.")

    except Exception as e:
        print(f"Error saving posts to '{POSTS_FILE}': {e}")


def validate_new_post_data(new_post: dict) -> tuple[bool, list]:
    """
    Validates data for a new post.
    Ensures 'title', 'content', and 'author' fields are present and not empty.
    :param new_post: dict with new post data
    :return:
        True if new_post is valid, False otherwise
        List of errors if new_post is invalid
    """
    errors = []

    if not new_post:
        errors.append("Request body cannot be empty.")

        return False, errors

    # Check for presence and non-emptiness of required fields
    for field in ["title", "content", "author"]:
        if field not in new_post or not new_post[field]:
            errors.append(f"Field '{field}' is missing or empty.")

    if errors:

        return False, errors

    return True, []


def validate_update_post_data(new_data: dict) -> tuple[bool, list]:
    """
    Validates data for updating an existing post.
    Ensures that if 'title', 'content', or 'author' fields are present, they are not empty.
    :param new_data: dict with update post data
    :return:
        True if update is valid, False otherwise
        List of errors if update is invalid
    """
    errors = []
    # Only validate if the field is present and then check for emptiness
    if "title" in new_data and not new_data["title"]:
        errors.append("Field 'title' is empty.")
    if "content" in new_data and not new_data["content"]:
        errors.append("Field 'content' is empty.")
    if "author" in new_data and not new_data["author"]:
        errors.append("Field 'author' is missing or empty.")

    if errors:

        return False, errors

    return True, []


def find_post_by_id(post_id: int) -> dict | None:
    """
    Finds a post in the POSTS list by its ID.
    Returns the post dictionary if found, otherwise None.
    :param post_id: int: id of post
    :return: dict or None: post if found
    """
    for post in POSTS:
        if post["id"] == post_id:

            return post


def search_posts_data(search_title: str = None,
                      search_content: str = None,
                      search_author: str = None,
                      search_date: str = None) -> list:
    """
    Searches posts based on provided title, content, author, and/or date.
    Performs case-insensitive search for text fields and exact date match.
    Returns a list of unique matching posts.
    :param search_title: str: title to search for
    :param search_content: str: content to search for
    :param search_author: str: author to search for
    :param search_date: str: date to search for
    :return: list: list of posts matching the search criteria
    """
    search_results = set()

    # Convert search queries to lowercase for case-insensitive comparison
    lower_title = search_title.lower() if search_title else None
    lower_content = search_content.lower() if search_content else None
    lower_author = search_author.lower() if search_author else None

    # Parse search_date into a date object if provided for accurate comparison
    search_date_obj = None
    if search_date:
        try:
            # Assuming search date comes in YYYY-MM-DD format for consistency
            search_date_obj = datetime.strptime(search_date, "%Y-%m-%d").date()
        except ValueError:
            # Handle invalid date format in search query
            print(f"Warning: Invalid date format for search_date: {search_date}. Skipping date search.")
            search_date_obj = None

    for post in POSTS:
        match = False
        # Get post fields safely, providing empty string as default for lower()
        post_title_lower = post.get("title").lower()
        post_content_lower = post.get("content").lower()
        post_author_lower = post.get("author").lower()

        # Access the datetime object for comparison
        post_date_obj = post.get("date")

        if lower_title and lower_title in post_title_lower:
            match = True
        if lower_content and lower_content in post_content_lower:
            match = True
        if lower_author and lower_author in post_author_lower:
            match = True

        # Compare date objects (only the date part)
        if search_date_obj and isinstance(post_date_obj, datetime) and post_date_obj.date() == search_date_obj:
            match = True

        if match:
            search_results.add(post["id"])

    return [post for post in POSTS if post["id"] in search_results]


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts() -> tuple[Response, int]:
    """
    Handles GET requests to retrieve posts (with optional sorting) and
    POST requests to create a new post.
    Returns:
        Tuple[Response, int]: A tuple containing a Flask Response object
                              (which includes the JSON data) and an HTTP status code.
                              - 200 (OK) for successful GET,
                              - 201 (Created) for successful POST, or
                              - 400 (Bad Request) for validation errors or invalid sorting parameters.
    """
    if request.method == 'POST':
        # Get new post from the user
        new_post = request.get_json()

        # Validate new post content
        is_valid, errors = validate_new_post_data(new_post)

        if not is_valid:

            return jsonify({"error(s)": errors}), 400

        # Generate new ID for the new post
        new_id = max(post['id'] for post in POSTS) + 1 if POSTS else 1
        new_post['id'] = new_id

        # Generate data field date
        new_post['date'] = datetime.now()

        # Add new post
        POSTS.append(new_post)
        save_posts()

        return jsonify(new_post), 201

    else:
        # Handle the GET request
        sort_by = request.args.get('sort')
        direction = request.args.get('direction')

        valid_sort_fields = {"id", "title", "content", "author", "date"}
        valid_direction_fields = {"asc", "desc"}

        # Check if sorting parameters are provided and valid
        if sort_by is not None or direction is not None:
            if sort_by not in valid_sort_fields or direction not in valid_direction_fields:
                return jsonify({"error": "Invalid sorting parameters. "
                                     "Use 'sort' (id, title, content, author, date) and 'direction' (asc, desc)"
                                }), 400

            sorting = (direction == "desc")

            try:
                sorted_posts = sorted(
                    POSTS,
                    key=lambda post: post.get(sort_by, '') if sort_by != 'date' else post.get(sort_by),
                    reverse=sorting
                )
            except TypeError as e:
                print(f"Sorting error: {e}")
                return jsonify(
                    {"error": f"Error during sorting."}), 500

            return jsonify(sorted_posts), 200

        else:
            # If no sorting parameters or incomplete, return the original list
            return jsonify(POSTS), 200


@app.route('/api/posts/<int:id>', methods=['DELETE', 'PUT'])
def handle_single_post(id: int) -> tuple[Response, int] | None:
    """
    Handles operations for a single post identified by its ID (DELETE, PUT).
    params: id (int): The unique identifier of the post.
    Returns:
        Tuple[Response, int]: A tuple containing a Flask Response object
                              (which includes the JSON data) and an HTTP status code.
                              - 200 (OK) for successful DELETE/PUT,
                              - 400 (Bad Request) for invalid update data, or
                              - 404 (Not Found) if the post does not exist.
    """
    # Find the post based on given ID
    post = find_post_by_id(id)

    # If not found, return 404 error
    if not post:

        return jsonify({"error": f"Post with id {id} not found."}), 404

    if request.method == 'DELETE':

        return delete_post(id, post)

    if request.method == 'PUT':

        return update_post(post)


def delete_post(id: int, post: dict) -> tuple[Response, int] | None:
    """ Deletes a post from the POSTS list """
    global POSTS
    # Delete post
    POSTS.remove(post)
    save_posts()
    # Return the deleted post
    return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200


def update_post(post: dict) -> tuple[Response, int] | None:
    """ Updates an existing post with new data """
    # Update post
    new_data = request.get_json()

    # Validate update post content
    is_valid, errors = validate_update_post_data(new_data)
    if not is_valid:

        return jsonify({"error(s)": errors}), 400

    # Generate data field date
    # If new_data contains 'date', it would be overridden
    # In the list, only the update date will remain
    new_data['date'] = datetime.now()

    # Update post
    post.update(new_data)
    save_posts()
    # Return the updated post
    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts() -> tuple[Response, int] | None:
    """ Endpoint for searching posts based on query parameters """
    search_title = request.args.get('title')
    search_content = request.args.get('content')
    search_author = request.args.get('author')
    search_date = request.args.get('date')

    search_results = search_posts_data(search_title, search_content, search_author, search_date)

    return jsonify(search_results), 200


if __name__ == '__main__':
    load_data()
    app.run(host="0.0.0.0", port=5002, debug=True)
