let currentLoggingInUser = "";

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


// document.getElementById('auth-form').addEventListener('submit', async (e) => {
//     e.preventDefault();
//     const username = document.getElementById('given-username').value;
//     const password = document.getElementById('given-password').value;

//     const response = await fetch('/login/', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
//         body: JSON.stringify({ username, password })
//     });

//     const data = await response.json();

//     if (response.status === 200 && data.mfa_required) {
//         window.currentLoggingInUser = data.username; 
//         document.getElementById('login-step-1').style.display = 'none';
//         document.getElementById('login-step-2').style.display = 'block';
//     } else if (response.ok) {
//         window.location.href = '/'; 
//     } else {
//         alert(data.error || "Login failed");
//     }
// });


// document.getElementById('verify-mfa-button').addEventListener('click', async () => {
//     const code = document.getElementById('mfa-code').value;
    
//     const response = await fetch('/login/verify-mfa/', { 
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
//         body: JSON.stringify({ 
//             username: window.currentLoggingInUser, 
//             code: code 
//         })
//     });

//     if (response.ok) {
//         const data = await response.json();
//         if (data.token) {
//             sessionStorage.setItem('scoped_api_token', data.token);
//         }
//         window.location.href = '/'; 
//     } else {
//         alert("Invalid MFA code. Please try again.");
//     }
// });


document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('given-username').value;
    const password = document.getElementById('given-password').value;

    const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.status === 200 && data.mfa_required) {
        // PATH A (e.g. Oszkar): MFA is needed
        window.currentLoggingInUser = data.username; 
        document.getElementById('login-step-1').style.display = 'none';
        document.getElementById('login-step-2').style.display = 'block';
    } else if (response.ok) {
        // PATH B (e.g. John): No MFA needed, successful straight login path!
        // Capture the scoped API token payload returned by your new login_view code
        if (data.token) {
            sessionStorage.setItem('scoped_api_token', data.token);
        }
        window.location.href = '/'; 
    } else {
        alert(data.error || "Login failed");
    }
});


document.getElementById('verify-mfa-button').addEventListener('click', async () => {
    const code = document.getElementById('mfa-code').value;
    
    const response = await fetch('/login/verify-mfa/', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ 
            username: window.currentLoggingInUser, 
            code: code 
        })
    });

    if (response.ok) {
        const data = await response.json();
        if (data.token) {
            sessionStorage.setItem('scoped_api_token', data.token);
        }
        window.location.href = '/'; 
    } else {
        alert("Invalid MFA code. Please try again.");
    }
});