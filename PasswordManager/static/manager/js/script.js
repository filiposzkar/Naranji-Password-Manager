let credentials_list = []; 
let userMasterKey = "";
let currentPage = 1;
const itemsPerPage = 5;


function askForMasterKey() {
    let input = prompt("Welcome back! Please enter your Master Key to unlock your vault:");
    
    if (input === null || input.trim() === "") {
        userMasterKey = ""; 
        sessionStorage.removeItem('master_key'); 
        window.location.href = "/login/";
        return;
    } 
    else {
        userMasterKey = input; 
        sessionStorage.setItem('master_key', input); 
        console.log("Vault Unlocked! Fetching backend records...");
        loadCredentialsFromServer(); 
    }
}


async function loadCredentialsFromServer() {
    if (!userMasterKey) {
        userMasterKey = sessionStorage.getItem('master_key') || "";
    }

    if (!userMasterKey) {
        askForMasterKey();
        return;
    }

    try {
        const response = await fetch('/api/credentials/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Master-Key': userMasterKey,
                'X-Scoped-Token': sessionStorage.getItem('scoped_api_token')
            },
            credentials: 'include' 
        });
        
        if (response.ok) {
            const data = await response.json();
            credentials_list = Array.isArray(data) ? data : (data.results || []);
            renderList();
        } 
        else if (response.status === 401 || response.status === 400) {
            alert("Invalid or missing Master Key! Access denied.");
            
            sessionStorage.removeItem('master_key');
            sessionStorage.removeItem('scoped_api_token');
            sessionStorage.removeItem('vault_canary');
            window.location.href = '/login/';
        } 
        else if (response.status === 403) {
            alert("Session unauthorized or expired. Please re-authenticate.");
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error("Failed to load credentials:", error);
    }
}


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


document.getElementById('generate-codes-btn').addEventListener('click', function() {
    const csrftoken = getCookie('csrftoken');
    fetch('/generate-codes/', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), 
            'Content-Type': 'application/json',
            'X-Scoped-Token': sessionStorage.getItem('scoped_api_token'),
            'X-CSRFToken': csrftoken
        },
    })
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById('codes-list');
        list.innerHTML = '';
        data.codes.forEach(code => {
            const li = document.createElement('li');
            li.style.fontFamily = 'monospace';
            li.innerText = code;
            list.appendChild(li);
        });
        document.getElementById('codes-display').style.display = 'block';
    })
    .catch(error => console.error('Error:', error));
});


document.getElementById('save-backup-btn').addEventListener('click', function() {
    const phrase = document.getElementById('setup-phrase').value;
    const masterKey = prompt("Please confirm your current Master Key to encrypt the backup:");

    if (!phrase || !masterKey) return alert("Both fields are required!");

    fetch('/api/setup-recovery/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            phrase: phrase,
            master_key: masterKey
        }),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('setup-message').innerText = "Backup secured! You can now use the recovery page.";
        document.getElementById('setup-message').style.color = "green";
    })
    .catch(err => console.error(err));
});




function renderList() {
    const container = document.getElementById('credentials_list');
    container.innerHTML = '';

    // calculating which items to show
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const items = Array.isArray(credentials_list) ? credentials_list : (credentials_list.results || []);
    const paginatedItems = items.slice(startIndex, endIndex);

    paginatedItems.forEach(item => {
        const itemHTML = `
            <div class="list-item" onclick="displayDetails(${item.id})">
                <img src="static/manager/assets/Login.png" class="website-icon"> 
                <div class="item-info">
                    <p class="item-website">${item.website_name}</p>
                    <p class="item-email">${item.email}</p> 
                </div>
            </div>
        `;
        container.innerHTML += itemHTML;
    });

    updatePaginationControls();
}


function updatePaginationControls() {
    const totalPages = Math.ceil(credentials_list.length / itemsPerPage) || 1;
    const info = document.getElementById('pagination-info');
    if (info) {
        info.innerText = `${currentPage} / ${totalPages}`;
    }
}


function nextPage() {
    const totalPages = Math.ceil(credentials_list.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderList();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        renderList();
    }
}

// runs when a login credential from the list of credentials gets clicked
function displayDetails(id) {
    // Look for the entry in your local list
    console.log("Current list type:", typeof credentials_list, credentials_list);
    const entry = credentials_list.find(item => String(item.id) === String(id));

    if(entry){
        setCookie("last-viewed-login-credential", entry.website_name, 7);  
        
        console.log("Cookie updated: User is interested in " + entry.website_name);
        
        document.getElementById('name-container').innerHTML = `<h2 id="display-website-name">${entry.website_name}</h2>`;
        
        document.getElementById('display-website-logo').src = "static/manager/assets/Login.png"; 
        document.getElementById('display-email').value = entry.email;      
        document.getElementById('display-username').value = entry.username; 
        document.getElementById('display-password').value = entry.password;
        document.getElementById('display-URL').value = entry.url;        
        
        setFormFieldsDisabled(true);  // locking the fields

        const editBtn = document.getElementById('edit-button');
        const deleteBtn = document.getElementById('delete-button');
        const saveBtn = document.getElementById('save-button');

        if (editBtn) {
            editBtn.style.display = "block"; 
            editBtn.onclick = () => startEditing(id);
            editBtn.innerText = "Edit";
        }
        if (deleteBtn) {
            deleteBtn.style.display = "block"; 
            deleteBtn.onclick = () => deleteItem(id);
        }
        if (saveBtn) {
            saveBtn.style.display = "none";
        }
    }
    else {
        console.error("Could not find credential with ID:", id);
        console.log("Available IDs in list:", credentials_list.map(i => i.id));
    }
}


// prepare form for new item
function showAddForm() {
    // swapping H2 for an input field
    const container = document.getElementById('name-container');
    container.innerHTML = '<input type="text" id="input-website-name" placeholder="Website Name" class="main-title-input">';

    // clearing everything
    document.getElementById('display-website-logo').src = "static/manager/assets/Login.png";
    document.getElementById('display-email').value = "";
    document.getElementById('display-username').value = "";
    document.getElementById('display-password').value = "";
    document.getElementById('display-URL').value = "";

    // toggling buttons
    document.getElementById('save-button').style.display = "block";
    document.getElementById('edit-button').style.display = "none";
    document.getElementById('delete-button').style.display = "none";
}


function setFormFieldsDisabled(status) {
    document.getElementById('display-email').disabled = status;
    document.getElementById('display-username').disabled = status;
    document.getElementById('display-password').disabled = status;
    document.getElementById('display-URL').disabled = status;
}


document.getElementById('add-item-button').addEventListener('click', () => {
    document.getElementById('display-email').value = "";
    document.getElementById('display-username').value = "";
    document.getElementById('display-password').value = "";
    document.getElementById('display-URL').value = "";

    setFormFieldsDisabled(false);   // unlock the fields 

    document.getElementById('save-button').style.display = "block";
    document.getElementById('edit-button').style.display = "none";
})



function generateStrongPassword() {
    const lowercase = "abcdefghijklmnopqrstuvwxyz";
    const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const numbers = "0123456789";
    const symbols = "!@#$%^&*";

    let password = "";
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += symbols[Math.floor(Math.random() * symbols.length)];

    const allChars = lowercase + uppercase + numbers + symbols;
    for (let i = 0; i < 8; i++) {
        password += allChars[Math.floor(Math.random() * allChars.length)];
    }

    return password.split('').sort(() => 0.5 - Math.random()).join('');
}


function autoFillGeneratedPassword() {
    const passwordInput = document.getElementById('display-password');
    const newPassword = generateStrongPassword();
    passwordInput.value = newPassword;
    passwordInput.dispatchEvent(new Event('input'));
}



document.getElementById('display-password').addEventListener('input', function() {
    const passwordInput = this;
    const strengthText = document.getElementById('password-strength-text');
    const passwordValue = passwordInput.value;

    if (passwordValue.length === 0) {
        passwordInput.classList.remove('border-weak', 'border-strong');
        strengthText.innerText = '';
        return;
    }

    // at least 12 characters, at least 1 number, at leat 1 special character
    const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{12,}$/;  

    if (strongPasswordRegex.test(passwordValue)) {
        passwordInput.classList.remove('border-weak');
        passwordInput.classList.add('border-strong');
        strengthText.innerText = "Strong";
        strengthText.style.color = "#a4c639";
    }

    else {
        passwordInput.classList.remove('border-strong');
        passwordInput.classList.add('border-weak');
        if (strengthText) {
            strengthText.innerHTML = `
                Weak (12+ characters, 1 uppercase, 1 lowercase, 1 number, 1 symbol). 
                <a href="javascript:void(0)" onclick="autoFillGeneratedPassword()" style="color: #337ab7; text-decoration: underline; margin-left: 5px;">
                    Generate strong password
                </a>
            `;
            strengthText.style.color = "#d9534f";
        }
    }
});



async function saveNewItem() {
    const name = document.getElementById('input-website-name').value;
    const email = document.getElementById('display-email').value;
    const currentLogo = document.getElementById('display-website-logo').src;
    const username = document.getElementById('display-username').value;
    const password = document.getElementById('display-password').value;
    const url = document.getElementById('display-URL').value;

    const token = getCookie('csrftoken');
    console.log("My CSRF Token is:", token);

    // client-side validation
    if (!name) {
        alert("Website name is required!");
        return;
    }

    if (!email) {
        alert("Email is required!");
        return;
    }

    if (!username) {
        alert("Username is required!");
        return;
    }

    if (!password) {
        alert("Password is required!");
        return;
    }

    if (!url) {
        alert("URL is required!");
        return;
    }

    if(userMasterKey === null || userMasterKey === "") {
        userMasterKey = prompt("Please enter your Master Key to encrypt this password!");
        if (!userMasterKey) return;
    }

    const newEntry = {
        website_name: name,
        url: url,     
        username: username, 
        email: email,       
        password: password, 
        logo: currentLogo   
    };

    try {
        const response = await fetch('/api/credentials/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'X-Scoped-Token': sessionStorage.getItem('scoped_api_token'),
                'X-Master-Key': userMasterKey
            },
            body: JSON.stringify(newEntry),
            credentials: 'include'
        })

        if (response.ok) {
            const savedItem = await response.json(); 
            alert("Saved and encrypted!");

            if (Array.isArray(credentials_list)) {
                credentials_list.unshift(savedItem);
            } else {
                if (credentials_list.results) {
                    credentials_list.results.unshift(savedItem);
                } else {
                    credentials_list = [savedItem];
                }
            }
            renderList();
            displayDetails(savedItem.id);
        }
        else {
            const errorData = await response.json();
            alert("Server Error: " + (errorData.error || "Failed to save"));
        }
    } catch (error) {
        console.error("Connection failed:", error);
        alert("Could not connect to the Python server.");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    renderList();
    document.getElementById('save-button').onclick = saveNewItem;
});


async function deleteItem(id) {
    if (!id) {
        console.error("Delete failed: No ID provided.");
        return;
    }
    if (!confirm("Are you sure you want to delete this credential?")) {
        return;
    }
    try {
        const response = await fetch(`/api/credentials/${id}/`, { 
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'), 
                'Content-Type': 'application/json',
                'X-Scoped-Token': sessionStorage.getItem('scoped_api_token'),
            }
        });

        if (response.ok) {
            credentials_list = credentials_list.filter(item => item.id !== id);
            renderList();
            alert("Deleted successfully from the database");
        } else {
            const errorData = await response.json();
            alert("Error: " + errorData.error);
        }
    } catch (error) {
        console.error("Network error:", error);
        alert("OK!");
    }
}



function startEditing(id) {
    setFormFieldsDisabled(false);  
    const entry = credentials_list.find(item => item.id === id);
    
    // swapping the H2 for an input so the user can change the name
    const container = document.getElementById('name-container');
    container.innerHTML = `<input type="text" id="input-website-name" value="${entry.website_name}" class="main-title-input">`;

    const editBtn = document.getElementById('edit-button');
    editBtn.innerText = "Save Changes";   // changing the Edit button into a "Confirm" button
    editBtn.onclick = () => saveUpdate(id); // updating the click event to trigger the save
}


async function saveUpdate(id) {
    const name = document.getElementById('input-website-name').value;
    const email = document.getElementById('display-email').value;
    const currentLogo = document.getElementById('display-website-logo').src;
    const username = document.getElementById('display-username').value;
    const password = document.getElementById('display-password').value;
    const url = document.getElementById('display-URL').value;

    // client-side validation
    if (!name) {
        alert("Website name is required!");
        return;
    }

    if (!email) {
        alert("Email is required!");
        return;
    }

    if (!username) {
        alert("Username is required!");
        return;
    }

    if (!password) {
        alert("Password is required!");
        return;
    }

    if (!url) {
        alert("URL is required!");
        return;
    }


    const updatedData = {
        website_name: document.getElementById('input-website-name').value,
        email: document.getElementById('display-email').value,
        username: document.getElementById('display-username').value,
        password: document.getElementById('display-password').value,
        url: document.getElementById('display-URL').value,
        logo: document.getElementById('display-website-logo').src
    };

    try {
        const response = await fetch(`/api/credentials/${id}/`, { 
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Scoped-Token': sessionStorage.getItem('scoped_api_token'),
                'X-Master-Key': userMasterKey
            },
            body: JSON.stringify(updatedData)
        });

        if (response.ok) {
            const result = await response.json();
            const index = credentials_list.findIndex(item => item.id === id);
            if (index !== -1) {
                credentials_list[index] = result;
            }
            renderList();
            displayDetails(id);
            alert("Changes saved to database");
        } else {
            const errorData = await response.json();
            alert("Error saving: " + (errorData.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Network error:", error);
        alert("Could not connect to the server.");
    }
}



function runTests() {
    console.log("Starting Tests...");

    // test 1: adding multiple items 
    for (let i = 1; i <= 10; i++) {
        credentials_list.push({
            id: Date.now() + i,
            website_name: `Test Site ${i}`,
            email: `test${i}@example.com`,
            username: `user${i}`,
            password: `pass${i}`,
            url: `www.test${i}.com`,
            logo: "default-icon.png"
        });
    }
    
    renderList();
    console.log("Test: 10 items added to RAM. Check pagination.");




    // test 2: verifying searching/filtering
    const found = credentials_list.find(c => c.website_name === "Test Site 1");
    console.log(found ? "Test: Search logic working." : "Test: Search logic failed.");




    // test 3: deleting an item
    const initialCount = credentials_list.length;
    const idToDelete = credentials_list[0].id; // grabbing the first one
    deleteItem(idToDelete); 

    if (credentials_list.length === initialCount - 1) {
        console.log("Test: Delete logic passed. Item removed from RAM.");
    } 
    else {
        console.log("Test: Delete logic failed.");
    }



    // test 4: updating an item
    const testId = credentials_list[0].id;
    credentials_list[0].website_name = "UPDATED_NAME";
    renderList();

    const check = credentials_list.find(c => c.id === testId);
    if (check.website_name === "UPDATED_NAME") {
        console.log("Test: Update logic passed.");
    } 
    else {
        console.log("Test: Update logic failed.");
    }
}


// function to save cookie to the browser's storage
// name -> name of the cookie
// value -> the data the cookie stores
// days -> how many days until the browser deletes the cookie

function setCookie (name, value, days) {
    const date = new Date();  // grabbing the current time
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));  // date.setTime() transforms days into milliseconds, and adds it to the current time to find the expiration date
    let expires = "expires=" + date.toUTCString();  // toUTCString() converts the expiration date (in milliseconds) to a real date time that browsers understand
    document.cookie = name + "=" + value + ";" + expires + ";path=";  // this line sends the data of the cookie to the browser's storage (name, value and days become one long string)
}


window.onload = function() {
    renderList(); 
    const lastVisitedName = getCookie("last-viewed-login-credential");

    if (lastVisitedName) {
        // finding the ID of the credential that matches the name in the cookie
        const lastEntry = credentials_list.find(item => item.website_name === lastVisitedName);

        if (lastEntry) {
            displayDetails(lastEntry.id);
        }
    }
};


document.addEventListener('DOMContentLoaded', () => {
    const saveBtn = document.getElementById('save-button');
    if (saveBtn) saveBtn.onclick = saveNewItem;

    const links = document.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', function(e) {   // when the user clicks on a specific link 

            // checking if the link is internal, not an external one outside the website and if it is valid
            if (this.hostname === window.location.hostname && this.href && this.getAttribute('href') !== 'javascript:void(0)') {
                e.preventDefault();  // stop the browser from instantly jumping to the new page
                const target = this.href;  // remembers the URL the user wants to go to
                document.body.style.opacity = '0';
                document.body.style.transition = 'opacity 0.5s ease';
                setTimeout(() => { window.location.href = target; }, 500);
            }
        });
    });


    if (window.location.pathname.includes('credentials') || document.getElementById('add-item-button')) {
        if (sessionStorage.getItem('master_key')) {   // did the user already wrote their master key?
            loadCredentialsFromServer();
        } else {
            askForMasterKey();
        }
    } else {
        renderList();
    }
});