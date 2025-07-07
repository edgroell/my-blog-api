"""
Module serving as Data Access Layer.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


# --- Custom Exceptions for Clearer Error Handling ---

class PostNotFound(Exception):
    """ Custom exception raised when a post is not found. """
    pass


class ValidationError(Exception):
    """ Custom exception raised for data validation errors. """
    pass


class PostRepository:
    """
    Manages all data operations for blog posts, using a JSON file as storage.
    This class is responsible for loading, saving, creating, updating, deleting,
    and searching for posts.
    """

    def __init__(self, posts_file: str):
        """
        Initializes the PostRepository.
        Args: posts_file (str): The path to the JSON file used for storing posts.
        """
        self.posts_file = posts_file
        self.posts: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """
        Loads posts from the JSON file into memory.
        Converts date strings to datetime objects. Initializes the file with an
        empty list if it doesn't exist or is invalid.
        """
        if not os.path.exists(self.posts_file):
            print(f"'{self.posts_file}' not found. Creating a new file.")
            with open(self.posts_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            self.posts = []

            return

        try:
            with open(self.posts_file, "r", encoding="utf-8") as f:
                posts_data = json.load(f)
                loaded_posts = []
                for post in posts_data:
                    if "date" in post and isinstance(post['date'], str):
                        try:
                            post["date"] = datetime.fromisoformat(post["date"])
                        except ValueError as e:
                            print(f"Warning: Could not parse date '{post['date']}': {e}")
                    loaded_posts.append(post)
                self.posts = loaded_posts
            print(f"Successfully loaded {len(self.posts)} posts.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error loading '{self.posts_file}': {e}. Initializing with empty list.")
            self.posts = []

    def _save_data(self) -> None:
        """ Saves the current list of posts to the JSON file. """
        posts_to_save = []
        for post in self.posts:
            post_copy = post.copy()
            if 'date' in post_copy and isinstance(post_copy['date'], datetime):
                post_copy['date'] = post_copy['date'].isoformat()
            posts_to_save.append(post_copy)

        try:
            with open(self.posts_file, "w", encoding="utf-8") as f:
                json.dump(posts_to_save, f, indent=4)
        except IOError as e:
            print(f"Error saving posts to '{self.posts_file}': {e}")

    def get_all(self, sort_by: Optional[str] = None, direction: Optional[str] = "asc") -> List[Dict[str, Any]]:
        """
        Retrieves all posts, with optional sorting.

        Args:
            sort_by (Optional[str]): The field to sort by. Valid fields are
                                     'id', 'title', 'content', 'author', 'date'.
            direction (Optional[str]): The sorting direction, 'asc' or 'desc'.

        Returns:
            List[Dict[str, Any]]: A list of all post dictionaries.

        Raises:
            ValueError: If sorting parameters are invalid.
        """
        if not sort_by:

            return self.posts

        valid_sort_fields = {"id", "title", "content", "author", "date"}
        if sort_by not in valid_sort_fields or direction not in {"asc", "desc"}:

            raise ValueError("Invalid sorting parameters.")

        is_reverse = direction == "desc"

        return sorted(self.posts, key=lambda p: p.get(sort_by, ""), reverse=is_reverse)

    def get_by_id(self, post_id: int) -> Dict[str, Any]:
        """
        Finds a single post by its ID.

        Args:
            post_id (int): The ID of the post to find.

        Returns:
            Dict[str, Any]: The post dictionary if found.

        Raises:
            PostNotFound: If no post with the given ID exists.
        """
        for post in self.posts:
            if post["id"] == post_id:

                return post

        raise PostNotFound(f"Post with id {post_id} not found.")

    def add(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds a new post.

        Args:
            post_data (Dict[str, Any]): The data for the new post.

        Returns:
            Dict[str, Any]: The newly created post, including its ID and date.

        Raises:
            ValidationError: If the post data is invalid.
        """
        errors = []
        if not post_data:

            raise ValidationError("Request body cannot be empty.")

        for field in ["title", "content", "author"]:
            if not post_data.get(field):
                errors.append(f"Field '{field}' is missing or empty.")

        if errors:

            raise ValidationError(", ".join(errors))

        new_id = max(p['id'] for p in self.posts) + 1 if self.posts else 1
        new_post = {
            "id": new_id,
            "date": datetime.now(),
            **post_data
        }
        self.posts.append(new_post)
        self._save_data()

        return new_post

    def update(self, post_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates an existing post.

        Args:
            post_id (int): The ID of the post to update.
            update_data (Dict[str, Any]): The data to update the post with.

        Returns:
            Dict[str, Any]: The updated post dictionary.

        Raises:
            PostNotFound: If the post to update is not found.
            ValidationError: If the update data is invalid.
        """
        post_to_update = self.get_by_id(post_id)

        errors = []
        for field in ["title", "content", "author"]:
            if field in update_data and not update_data[field]:
                errors.append(f"Field '{field}' cannot be empty.")
        if errors:

            raise ValidationError(", ".join(errors))

        post_to_update.update(update_data)
        post_to_update['date'] = datetime.now()
        self._save_data()

        return post_to_update

    def delete(self, post_id: int) -> None:
        """
        Deletes a post by its ID.

        Args:
            post_id (int): The ID of the post to delete.

        Raises:
            PostNotFound: If the post to delete is not found.
        """
        post_to_delete = self.get_by_id(post_id)
        self.posts.remove(post_to_delete)
        self._save_data()

    def search(self, **kwargs: Optional[str]) -> List[Dict[str, Any]]:
        """
        Searches posts based on criteria.

        Args:
            **kwargs: Search criteria (e.g., title="...", author="...").

        Returns:
            List[Dict[str, Any]]: A list of unique matching posts.
        """
        results = []
        query = {k.lower(): v.lower() for k, v in kwargs.items() if v and k != 'date'}
        search_date_str = kwargs.get('date')

        search_date = None
        if search_date_str:
            try:
                search_date = datetime.strptime(search_date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Warning: Invalid search date format '{search_date_str}'.")

        for post in self.posts:
            text_match = False
            for key, value in query.items():
                if value in post.get(key, "").lower():
                    text_match = True
                    break

            date_match = False
            if search_date and isinstance(post.get('date'), datetime):
                if post['date'].date() == search_date:
                    date_match = True

            if (query and text_match) or (search_date and date_match):
                if post['id'] not in [r['id'] for r in results]:
                    results.append(post)

        return results
