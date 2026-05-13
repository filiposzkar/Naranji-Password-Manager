function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function handleSignUp() {
    const username = document.getElementById('given-username').value;
    const email = document.getElementById('given-email').value;
    const password = document.getElementById('given-password').value;

    const response = await fetch('/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            username: username,
            email: email,
            password: password
        })
    });

    if (response.ok) {
        alert("Account created! Now login and set your Master Key.");
        window.location.href = "/login/";
    } else {
        const error = await response.json();
        alert("Signup failed: " + error.error);
    }
}