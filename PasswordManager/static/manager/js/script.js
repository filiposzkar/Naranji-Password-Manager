let credentials_list = []; 
const offlineData = JSON.parse(localStorage.getItem('offline_credentials') || "[]");
credentials_list = [...offlineData, ...credentials_list];


const socket = new WebSocket('ws://127.0.0.1:8000/ws/credentials/');
socket.onopen = function(e) {   // this runs if the connection is successful
    console.log("WebSocket connection established!");
};
socket.onmessage = function(event) {
    const new_fake_item = JSON.parse(event.data);
    console.log("Received fake entity: ", new_fake_item);
    credentials_list.unshift(new_fake_item); 
    renderList();
};
socket.onerror = function(error) {
    console.error("WebSocket Error: ", error);
};

async function loadCredentialsFromServer() {
    try {
        const response = await fetch('/api/credentials/'); 
        if (response.ok) {
            const data = await response.json();
            
            if (data.results) {
                credentials_list = data.results; 
            } else if (data.credentials) {
                credentials_list = data.credentials;
            } else {
                credentials_list = data;
            }

            renderList(); 
            console.log("Loaded data from server RAM:", credentials_list);
        }
    } catch (error) {
        console.error("Failed to load credentials:", error);
    }
}

loadCredentialsFromServer();


let currentPage = 1;
const itemsPerPage = 3;


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
                <img src="${item.website_logo}" class="website-icon"> 
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
    const entry = credentials_list.find(item => String(item.id) === String(id));

    if(entry){
        setCookie("last-viewed-login-credential", entry.website_name, 7);  
        
        console.log("Cookie updated: User is interested in " + entry.website_name);
        
        document.getElementById('name-container').innerHTML = `<h2 id="display-website-name">${entry.website_name}</h2>`;
        
        document.getElementById('display-website-logo').src = entry.logo; 
        document.getElementById('display-email').value = entry.email;      
        document.getElementById('display-username').value = entry.username; 
        document.getElementById('display-password').value = entry.password;
        document.getElementById('display-URL').value = entry.url;          

        document.getElementById('edit-button').onclick = () => startEditing(id);
        document.getElementById('delete-button').onclick = () => deleteItem(id);
        
        document.getElementById('save-button').style.display = "none";
        document.getElementById('edit-button').innerText = "Edit";
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
    document.getElementById('display-website-logo').src = "manager/assets/NaranjiLogo.png";
    document.getElementById('display-email').value = "";
    document.getElementById('display-username').value = "";
    document.getElementById('display-password').value = "";
    document.getElementById('display-URL').value = "";

    // toggling buttons
    document.getElementById('save-button').style.display = "block";
}


async function saveNewItem() {
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

    const newEntry = {
        website_name: name,
        url: url,     
        username: username, 
        email: email,       
        password: password, 
        logo: currentLogo,
        synced: true 
    };

    if (!navigator.onLine) {
        handleOfflineSave(newEntry);
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/credentials/add/', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newEntry)
        });

        if (response.ok) {
            const savedItem = await response.json(); 
            
            credentials_list.unshift(savedItem); 
            
            renderList(); 
            displayDetails(savedItem.id); 
            
            console.log("Successfully saved to server RAM:", savedItem);

        } else {
            const errorData = await response.json();
            alert("Server Error: " + (errorData.error || "Failed to save"));
        }
    } catch (error) {
        handleOfflineSave(newEntry);
    }
}


function handleOfflineSave(item) {
    console.warn("Server unreachable! Switching to offline mode.");
    item.synced = false;
    item.id = Date.now();
    credentials_list.unshift(item);
    renderList();

    const offline = JSON.parse(localStorage.getItem('offline_credentials') || "[]");
    offline.push(item);
    localStorage.setItem('offline_credentials', JSON.stringify(offline));
    alert("Saved offline. Will sync later.");
}


function handleOfflineDelete(id) {
    console.warn("Server unreachable! Deleting locally, will sync with server later.");

    credentials_list = credentials_list.filter(item => item.id !== id);
    renderList();
    document.getElementById('detail-view-container').innerHTML = '<p>Select an item to view details</p>';

    const pendingDeletes = JSON.parse(localStorage.getItem('pending_deletes') || "[]");
    pendingDeletes.push(id);
    localStorage.setItem('pending_deletes', JSON.stringify(pendingDeletes));

    alert("Deleted locally. Server will be updated when back online.");
}


function handleOfflineUpdate(id, updatedData) {
    console.warn("Server unreachable! Updating locally.");

    const index = credentials_list.findIndex(item => item.id === id);
    if (index !== -1) {
        credentials_list[index] = { ...updatedData, id: id, synced: false };
    }

    renderList();
    displayDetails(id);

    const pendingUpdates = JSON.parse(localStorage.getItem('pending_updates') || "[]");
    
    const existingIndex = pendingUpdates.findIndex(u => u.id === id);
    if (existingIndex !== -1) {
        pendingUpdates[existingIndex] = { id, data: updatedData };
    } else {
        pendingUpdates.push({ id, data: updatedData });
    }
    
    localStorage.setItem('pending_updates', JSON.stringify(pendingUpdates));
    alert("Updated locally. Changes will sync when the server is back.");
}


async function syncOfflineData() {
    // 1) Sync new items (POST)
    const offlineAdds = JSON.parse(localStorage.getItem('offline_credentials') || "[]");
    for (const item of offlineAdds) {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/credentials/add/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item)
            });
            if (res.ok) {
                const savedItem = await res.json(); // Get the "Official" item from server
                removeItemsFromOfflineStorage(item.id);
                
                // Update the item in your local JS list so it stays visible
                const idx = credentials_list.findIndex(i => i.id === item.id);
                if (idx !== -1) {
                    credentials_list[idx] = savedItem; // Replace temp ID with server ID
                }
            }
        } catch (e) { break; }
    }

    // 2) Sync updates (PUT)
    const offlineUpdates = JSON.parse(localStorage.getItem('pending_updates') || "[]");
    for (const updateObj of offlineUpdates) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/credentials/update/${updateObj.id}/`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateObj.data)
            });
            if (res.ok) {
                const updatedItem = await res.json();
                // Clear from local storage
                let updates = JSON.parse(localStorage.getItem('pending_updates'));
                updates = updates.filter(u => u.id !== updateObj.id);
                localStorage.setItem('pending_updates', JSON.stringify(updates));

                // Update local JS memory
                const idx = credentials_list.findIndex(i => i.id === updateObj.id);
                if (idx !== -1) credentials_list[idx] = updatedItem;
            }
            if (res.status === 404) {
                console.warn("Item not found on server (likely restart). Re-adding...");
                // Try to POST it as a new item instead
                await fetch('http://127.0.0.1:8000/api/credentials/add/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateObj.data)
                });
            }
        } catch (e) { break; }
    }

    // 3) Sync deletes (DELETE)
    const offlineDeletes = JSON.parse(localStorage.getItem('pending_deletes') || "[]");
    for (const id of offlineDeletes) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/credentials/delete/${id}/`, { method: 'DELETE' });
            if (res.ok) {
                let deletes = JSON.parse(localStorage.getItem('pending_deletes'));
                deletes = deletes.filter(d => d !== id);
                localStorage.setItem('pending_deletes', JSON.stringify(deletes));
            }
        } catch (e) { break; }
    }

    renderList();
}

function removeItemsFromOfflineStorage(id) {
    let offline = JSON.parse(localStorage.getItem('offline_credentials') || "[]");
    offline = offline.filter(i => i.id !== id);
    localStorage.setItem('offline_credentials', JSON.stringify(offline));
}

// checking when the page is first opened/refreshed
window.addEventListener('load', async () => {
    // 1. Fetch what the server currently has
    const response = await fetch('http://127.0.0.1:8000/api/credentials/');
    const serverData = await response.json();
    
    // 2. If server is empty but we have local data, move local data to "offline" to trigger a sync
    if (serverData.results.length === 0 && credentials_list.length > 0) {
        localStorage.setItem('offline_credentials', JSON.stringify(credentials_list));
    }
    await syncOfflineData();
});

// checking whenever the browser detects the internet is back
window.addEventListener('online', syncOfflineData);


document.addEventListener('DOMContentLoaded', () => {
    renderList();
    document.getElementById('save-button').onclick = saveNewItem;
});


async function deleteItem(id) {
    if (!id) return;
    if (!confirm("Are you sure?")) return;

    if (!navigator.onLine) {
        handleOfflineDelete(id);
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/credentials/delete/${id}/`, {
            method: 'DELETE'
        });

        if (response.ok) {
            credentials_list = credentials_list.filter(item => item.id !== id);
            renderList();
            document.getElementById('detail-view-container').innerHTML = '<p>Select an item to view details</p>';
        } else {
            alert("Server couldn't delete this item.");
        }
    } catch (error) {
        handleOfflineDelete(id);
    }
}




function startEditing(id) {
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

    if (!navigator.onLine) {
        handleOfflineUpdate(id, updatedData);
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/credentials/update/${id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
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
            
            alert("Changes saved to Server RAM!");
        } else {
            const errorData = await response.json();
            alert("Error saving: " + (errorData.error || "Unknown error"));
        }
    } catch (error) {
        handleOfflineUpdate(id, updatedData);
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


// function to get a cookie from the browser's storage

function getCookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(';');  // this split the long string, to get each component separately (name, value, days)
    for(let i=0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);  // trim any white space put by the browser at the beginning of a cookie
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);   // indexOf() looks for a substring in a string, and because we want the name of the cookie to match the "name" parameter
        // we need to make sure that the substring "name" is starting on the first position of the cookies name, meaning that they are equal
        // we then extract the value of the cookie and return it
    }
    return null;
}


window.onload = function() {
    renderList(); 
    const lastVisitedName = getCookie("last-viewed-login-credential");

    if (lastVisitedName) {
        // finding the ID of the credential that matches the name in the cookie
        const lastEntry = credentials_list.find(item => item.website_name === lastVisitedName);

        if (lastEntry) {
            displayDetails(lastEntry.id);
        
            // const msgElement = document.getElementById('cookie-msg');
            // if (msgElement) {
            //     msgElement.innerText = "Resuming where you left off: " + lastVisitedName;
            // }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            // Check if it's an internal link (doesn't open in new tab and has an href)
            if (this.hostname === window.location.hostname && this.href) {
                e.preventDefault();
                const target = this.href;

                document.body.style.opacity = '0';
                document.body.style.transition = 'opacity 0.5s ease';

                setTimeout(() => {
                    window.location.href = target;
                }, 500);
            }
        });
    });
});
