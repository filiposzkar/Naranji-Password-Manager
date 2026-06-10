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

    try {
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

        const data = await response.json();

        if (response.ok) {
            document.getElementById('mfaSecretString').innerText = data.mfa_secret_key; // injecting the secret key into the text holder inside the modal            
            document.getElementById('mfaModal').style.display = 'flex';
            fetchMFAQRCode();
        } else {
            alert("Signup failed: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Network error during signup:", error);
        alert("An error occurred. Please try again later.");
    }
}


async function fetchMFAQRCode() {
    try {
        const response = await fetch('/mfa/enable/', {
            method: 'GET',
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const qrImg = document.getElementById('mfaQrImage');
            const qrLoading = document.getElementById('qrLoading');

            qrImg.src = `data:image/png;base64,${data.qr_code}`;

            qrLoading.style.display = 'none';
            qrImg.style.display = 'block';
        }
        else {
            document.getElementById('qrLoading').innerText = "Failed to load QR. Please copy key manually.";
        }
    }
    catch (err) {
        console.error("Error fetching MFA QR code:", err);
        document.getElementById('qrLoading').innerText = "Connection error. Please copy key manually.";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copySecretBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const secretText = document.getElementById('mfaSecretString').innerText;
            
            navigator.clipboard.writeText(secretText)
                .then(() => {
                    // Provide temporary dynamic state context change
                    this.innerText = "Copied!";
                    this.style.backgroundColor = "#a4c639";
                    this.style.color = "white";
                    
                    setTimeout(() => {
                        this.innerText = "Copy Key";
                        this.style.backgroundColor = "";
                        this.style.color = "";
                    }, 2000);
                })
                .catch(err => {
                    console.error("Clipboard copy failure:", err);
                    alert("Could not copy automatically. Please copy text highlight manually.");
                });
        });
    }
});

function redirectToLogin() {
    window.location.href = "/login/";
}