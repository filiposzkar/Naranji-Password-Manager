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

document.getElementById('recover-btn').addEventListener('click', function() {
    const username = document.getElementById('recovery-username').value;
    const phrase = document.getElementById('recovery-phrase').value;
    const errorMsg = document.getElementById('error-message');

    fetch('/api/recover-master-key/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
          username: username,
          recovery_phrase: phrase
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Incorrect phrase or username');
        return response.json();
    })
    .then(data => {
        document.getElementById('key-text').innerText = data.master_key;
        document.getElementById('master-key-display').style.display = 'block';
        errorMsg.innerText = '';
    })
    .catch(error => {
        errorMsg.innerText = error.message;
    });
});