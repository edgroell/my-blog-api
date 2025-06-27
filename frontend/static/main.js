// Function to show messages (success or error) to the user
function showMessage(message, type = 'info') {
    const messageBox = document.getElementById('message-box');
    messageBox.textContent = message;
    // Remove all type classes first, then add the new one
    messageBox.className = 'message-box'; // Reset to base class
    messageBox.classList.add(type);
    messageBox.style.display = 'block';
    // Automatically hide after a few seconds
    setTimeout(() => {
        messageBox.style.display = 'none';
    }, 5000);
}

// Function that runs once the window is fully loaded
window.onload = function() {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts(); // Load posts with default (no sorting/searching)
    } else {
        // If no base URL saved, show a prompt to the user
        showMessage("Please enter your API Base URL (e.g., http://localhost:5002/api) and click 'Load Posts'.", 'info');
    }
};

// Function to fetch all the posts from the API and display them on the page
// Now accepts optional sort_by and direction parameters
function loadPosts(sortBy = '', direction = '') {
    const baseUrl = document.getElementById('api-base-url').value;
    if (!baseUrl) {
        showMessage('API Base URL is required to load posts.', 'error');
        return;
    }
    localStorage.setItem('apiBaseUrl', baseUrl);

    let url = `${baseUrl}/posts`;
    const params = new URLSearchParams();
    if (sortBy) {
        params.append('sort', sortBy);
    }
    if (direction) {
        params.append('direction', direction);
    }
    if (params.toString()) {
        url += `?${params.toString()}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) { // Check for HTTP errors (e.g., 400, 404, 500)
                return response.json().then(errorData => {
                    throw new Error(errorData.error || (errorData['error(s)'] ? errorData['error(s)'].join(', ') : 'Unknown error'));
                });
            }
            return response.json();
        })
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = ''; // Clear out the post container first

            if (data.length === 0) {
                postContainer.innerHTML = '<p class="text-gray-500 text-center">No posts found.</p>';
                return;
            }

            // For each post in the response, create a new post element and add it to the page
            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';

                // Format the date for display (e.g., "YYYY-MM-DD HH:MM")
                let formattedDate = 'N/A';
                if (post.date) {
                    try {
                        const dateObj = new Date(post.date);
                        formattedDate = dateObj.toLocaleString(); // Uses local date and time format
                    } catch (e) {
                        console.warn('Invalid date format for display:', post.date, e);
                        formattedDate = post.date; // Fallback to raw date if parsing fails
                    }
                }

                postDiv.innerHTML = `
                    <h2 class="text-xl font-semibold">${post.title}</h2>
                    <p class="text-gray-700 mb-2">${post.content}</p>
                    <div class="meta text-gray-500 text-sm">
                        <span class="font-medium">Author:</span> ${post.author || 'Anonymous'} |
                        <span class="font-medium">Date:</span> ${formattedDate}
                    </div>
                    <div class="post-actions">
                        <button onclick="deletePost(${post.id})" class="btn-danger">Delete</button>
                    </div>
                `;
                postContainer.appendChild(postDiv);
            });
            showMessage('Posts loaded successfully!', 'success');
        })
        .catch(error => {
            console.error('Error loading posts:', error);
            showMessage(`Failed to load posts: ${error.message || error}`, 'error');
        });
}

// Function to send a POST request to the API to add a new post
function addPost() {
    const baseUrl = document.getElementById('api-base-url').value;
    const postTitle = document.getElementById('post-title').value;
    const postContent = document.getElementById('post-content').value;
    const postAuthor = document.getElementById('post-author').value; // Get author

    if (!baseUrl) { showMessage('API Base URL is required to add a post.', 'error'); return; }
    if (!postTitle || !postContent || !postAuthor) {
        showMessage('Title, Content, and Author are required to add a new post.', 'error');
        return;
    }

    fetch(`${baseUrl}/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: postTitle, content: postContent, author: postAuthor }) // Include author
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || (errorData['error(s)'] ? errorData['error(s)'].join(', ') : 'Unknown error'));
            });
        }
        return response.json();
    })
    .then(post => {
        console.log('Post added:', post);
        showMessage('Post added successfully!', 'success');
        document.getElementById('post-title').value = ''; // Clear fields
        document.getElementById('post-content').value = '';
        document.getElementById('post-author').value = '';
        loadPosts(); // Reload all posts (default unsorted)
    })
    .catch(error => {
        console.error('Error adding post:', error);
        showMessage(`Failed to add post: ${error.message || error}`, 'error');
    });
}

// Function to send a DELETE request to the API to delete a post
function deletePost(postId) {
    const baseUrl = document.getElementById('api-base-url').value;
    if (!baseUrl) { showMessage('API Base URL is required to delete a post.', 'error'); return; }
    showMessage(`Attempting to delete post ID: ${postId}...`, 'info');


    fetch(`${baseUrl}/posts/${postId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'Unknown error during deletion');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Post deleted:', data);
        showMessage(data.message || `Post ID ${postId} deleted successfully!`, 'success');
        loadPosts(); // Reload the posts after deleting one
    })
    .catch(error => {
        console.error('Error deleting post:', error);
        showMessage(`Failed to delete post: ${error.message || error}`, 'error');
    });
}

// New function to apply sorting
function applySort() {
    const sortBy = document.getElementById('sort-by').value;
    const direction = document.getElementById('sort-direction').value;

    if (!sortBy && !direction) {
        showMessage('Please select a field to sort by or a direction to apply sorting.', 'info');
        loadPosts(); // Reload unsorted if nothing selected
        return;
    }

    // The API requires both or neither for sorting. If one is selected,
    // the other must also be valid.
    if ((sortBy && !direction) || (!sortBy && direction)) {
        showMessage('Both "Sort By" and "Direction" must be selected to apply sorting.', 'error');
        return;
    }

    loadPosts(sortBy, direction);
}

// New function to perform a search
function performSearch() {
    const baseUrl = document.getElementById('api-base-url').value;
    if (!baseUrl) {
        showMessage('API Base URL is required to perform a search.', 'error');
        return;
    }

    const searchTitle = document.getElementById('search-title').value;
    const searchContent = document.getElementById('search-content').value;
    const searchAuthor = document.getElementById('search-author').value;
    const searchDate = document.getElementById('search-date').value;

    const params = new URLSearchParams();
    if (searchTitle) { params.append('title', searchTitle); }
    if (searchContent) { params.append('content', searchContent); }
    if (searchAuthor) { params.append('author', searchAuthor); }
    if (searchDate) { params.append('date', searchDate); }

    if (params.toString() === '') {
        showMessage('Please enter at least one search criterion.', 'info');
        return;
    }

    const url = `${baseUrl}/posts/search?${params.toString()}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || (errorData['error(s)'] ? errorData['error(s)'].join(', ') : 'Unknown error'));
                });
            }
            return response.json();
        })
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = ''; // Clear existing posts

            if (data.length === 0) {
                postContainer.innerHTML = '<p class="text-gray-500 text-center">No matching posts found.</p>';
                showMessage('No matching posts found.', 'info');
                return;
            }

            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';

                let formattedDate = 'N/A';
                if (post.date) {
                    try {
                        const dateObj = new Date(post.date);
                        formattedDate = dateObj.toLocaleString();
                    } catch (e) {
                        console.warn('Invalid date format for display:', post.date, e);
                        formattedDate = post.date;
                    }
                }

                postDiv.innerHTML = `
                    <h2 class="text-xl font-semibold">${post.title}</h2>
                    <p class="text-gray-700 mb-2">${post.content}</p>
                    <div class="meta text-gray-500 text-sm">
                        <span class="font-medium">Author:</span> ${post.author || 'Anonymous'} |
                        <span class="font-medium">Date:</span> ${formattedDate}
                    </div>
                    <div class="post-actions">
                        <button onclick="deletePost(${post.id})" class="btn-danger">Delete</button>
                    </div>
                `;
                postContainer.appendChild(postDiv);
            });
            showMessage(`Found ${data.length} matching posts.`, 'success');
        })
        .catch(error => {
            console.error('Error during search:', error);
            showMessage(`Failed to perform search: ${error.message || error}`, 'error');
        });
}

// Function to clear all search/sort inputs and reload all posts
function clearSearchAndReload() {
    document.getElementById('sort-by').value = '';
    document.getElementById('sort-direction').value = '';
    document.getElementById('search-title').value = '';
    document.getElementById('search-content').value = '';
    document.getElementById('search-author').value = '';
    document.getElementById('search-date').value = '';
    loadPosts(); // Reload all posts unsorted
    showMessage('Search and sort cleared. All posts reloaded.', 'info');
}

