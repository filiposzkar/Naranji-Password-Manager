let notes_list = [];
const offlineData = JSON.parse(localStorage.getItem('offline_notes') || "[]");
notes_list = [...offlineData, ...notes_list];

const socket = new WebSocket('ws://127.0.0.1:8000/ws/notes/');
socket.onopen = function(e) {   // this runs if the connection is successful
    console.log("WebSocket connection established!");
};
socket.onmessage = function(event) {
    const new_fake_item = JSON.parse(event.data);
    console.log("Received fake entity: ", new_fake_item);
    notes_list.unshift(new_fake_item); 
    renderList();
};
socket.onerror = function(error) {
    console.error("WebSocket Error: ", error);
};

async function fetchNotes() {
    try {
        const response = await fetch('/api/notes/');
        if (response.ok) {
            const data = await response.json();
            console.log(data);
            notes_list = data.results; 
            
            renderList(); 
        }
    } catch (error) {
        console.error("Error fetching notes:", error);
    }
}

fetchNotes();


let currentPage = 1;
const itemsPerPage = 3;


function renderList() {
    const container = document.getElementById('notes_list');
    container.innerHTML = '';

    console.log("this is the notes_list: ", notes_list);
    const dataArray = Array.isArray(notes_list) ? notes_list : (notes_list.results || []);

    // calculating which items to show
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = dataArray.slice(startIndex, endIndex);

    paginatedItems.forEach(item => {
        const itemHTML = `
            <div class="list-item" onclick="displayDetails(${item.id})">
                <img src="${item.logo}" class="notes-icon">
                <div class="item-info">
                    <p class="item-header">${item.headline}</p>
                    <p class="item-bodytext">${item.bodytext}</p>
                </div>
            </div>
        `;
        container.innerHTML += itemHTML;
    });

    updatePaginationControls();
}



function updatePaginationControls() {
    const totalPages = Math.ceil(notes_list.length / itemsPerPage) || 1;
    const info = document.getElementById('pagination-info');
    if (info) {
        info.innerText = `${currentPage} / ${totalPages}`;
    }
}


function nextPage() {
    const totalPages = Math.ceil(notes_list.length / itemsPerPage);
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
    const entry = notes_list.find(item => item.id === id);
   

    if(entry){
        setCookie("last-viewed-notes", entry.headline, 7);  // setting the name, value, and the expiration date of the cookie
        console.log("Cookie updated: User is interested in " + entry.headline);
        
        document.getElementById('name-container').innerHTML = `<h2 id="display-notes-name">${entry.headline}</h2>`;
        document.getElementById('display-notes-logo').src = entry.logo;
        document.getElementById('display-notes-bodytext').value = entry.bodytext;
        
        document.getElementById('edit-button').onclick = () => startEditing(id);
        document.getElementById('delete-button').onclick = () => deleteItem(id);
        
        document.getElementById('save-button').style.display = "none";
        document.getElementById('edit-button').innerText = "Edit";
    }

    
}


// prepare form for new item
function showAddForm() {
    // swapping H2 for an input field
    const container = document.getElementById('name-container');
    container.innerHTML = '<input type="text" id="input-notes-name" placeholder="Notes Name" class="main-title-input">';

    // clearing everything
    document.getElementById('display-notes-logo').src = "{% static 'manager/assets/NotesIcon.png' %}";
    document.getElementById('display-notes-bodytext').value = "";

    // toggling buttons
    document.getElementById('save-button').style.display = "block";
}



async function saveNewItem() {

    let noteData = null;
    try {
        const headlineElement = document.getElementById('input-notes-name');
        const bodytextElement = document.getElementById('display-notes-bodytext');
        const logoElement = document.getElementById('display-notes-logo');

        
        const headline = headlineElement.value;
        const bodytext = bodytextElement.value;
        
        const currentLogo = logoElement ? logoElement.src : "NaranjiLogo.png";

        console.log("Data collected:", { headline, bodytext, currentLogo });

        // client-side validation
        if (!headline.trim() || !bodytext.trim()) {
            alert("Please fill in the title and content!");
            return; 
        }

        noteData = {
            headline: headline,
            bodytext: bodytext,
            logo: currentLogo
        };

        if (!navigator.onLine) {
            handleOfflineSave(noteData);
            return;
        }

        console.log("Sending POST request to /api/notes/add/...");

        const response = await fetch('http://127.0.0.1:8000/api/notes/add/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(noteData)
        });


        // handling the Server Response
        if (response.ok) {
            const savedItem = await response.json(); 
            
            notes_list.unshift(savedItem); 
            
            renderList(); 
            displayDetails(savedItem.id); 
            
            console.log("Successfully saved to server RAM:", savedItem);

            alert("Note saved to Server RAM!");
        } else {
            const errorData = await response.json();
            console.error("Server rejected the request:", errorData);
            alert("Server Error: " + (errorData.error || "Unknown error"));
        }

    } catch (error) {
        handleOfflineSave(noteData);
    }
}


function handleOfflineSave(item) {
    console.warn("Server unreachable! Switching to offline mode.");
    item.synced = false;
    item.id = Date.now();
    notes_list.unshift(item);
    renderList();

    const offline = JSON.parse(localStorage.getItem('offline_notes') || "[]");
    offline.push(item);
    localStorage.setItem('offline_notes', JSON.stringify(offline));
    alert("Saved offline. Will sync later.");
}


function handleOfflineDelete(id) {
    console.warn("Server unreachable! Deleting locally, will sync with server later.");

    notes_list = notes_list.filter(item => item.id !== id);
    renderList();
    document.getElementById('detail-view-container').innerHTML = '<p>Select an item to view details</p>';

    const pendingDeletes = JSON.parse(localStorage.getItem('pending_notes_deletes') || "[]");
    pendingDeletes.push(id);
    localStorage.setItem('pending_notes_deletes', JSON.stringify(pendingDeletes));

    alert("Deleted locally. Server will be updated when back online.");
}


function handleOfflineUpdate(id, updatedData) {
    console.warn("Server unreachable! Updating locally.");

    const index = notes_list.findIndex(item => item.id === id);
    if (index !== -1) {
        notes_list[index] = { ...updatedData, id: id, synced: false };
    }

    renderList();
    displayDetails(id);

    const pendingUpdates = JSON.parse(localStorage.getItem('pending_notes_updates') || "[]");
    
    const existingIndex = pendingUpdates.findIndex(u => u.id === id);
    if (existingIndex !== -1) {
        pendingUpdates[existingIndex] = { id, data: updatedData };
    } else {
        pendingUpdates.push({ id, data: updatedData });
    }
    
    localStorage.setItem('pending_notes_updates', JSON.stringify(pendingUpdates));
    alert("Updated locally. Changes will sync when the server is back.");
}


async function syncOfflineNotes() { 
    // add
    const offlineAdds = JSON.parse(localStorage.getItem('offline_notes') || "[]");
    for (const item of offlineAdds) {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/notes/add/', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item)
            });
            if (res.ok) {
                const savedItem = await res.json();
                removeNotesFromOfflineStorage(item.id);
                
                const idx = notes_list.findIndex(i => i.id === item.id); 
                if (idx !== -1) {
                    notes_list[idx] = savedItem; 
                }
            }
        } catch (e) { break; }
    }
    // update
    const offlineUpdates = JSON.parse(localStorage.getItem('pending_notes_updates') || "[]");
    for (const updateObj of offlineUpdates) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/notes/update/${updateObj.id}/`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateObj.data)
            });
            if (res.ok) {
                const updatedItem = await res.json();
                // Clear from local storage
                let updates = JSON.parse(localStorage.getItem('pending_notes_updates'));
                updates = updates.filter(u => u.id !== updateObj.id);
                localStorage.setItem('pending_notes_updates', JSON.stringify(updates));

                // Update local JS memory
                const idx = notes_list.findIndex(i => i.id === updateObj.id);
                if (idx !== -1) notes_list[idx] = updatedItem;
            }
            if (res.status === 404) {
                console.warn("Item not found on server (likely restart). Re-adding...");
                // Try to POST it as a new item instead
                await fetch('http://127.0.0.1:8000/api/notes/add/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateObj.data)
                });
            }
        } catch (e) { break; }
    }

    // delete
    const offlineDeletes = JSON.parse(localStorage.getItem('pending_notes_deletes') || "[]");
    for (const id of offlineDeletes) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/notes/delete/${id}/`, { method: 'DELETE' });
            if (res.ok) {
                let deletes = JSON.parse(localStorage.getItem('pending_notes_deletes'));
                deletes = deletes.filter(d => d !== id);
                localStorage.setItem('pending_notes_deletes', JSON.stringify(deletes));
            }
        } catch (e) { break; }
    }
    renderList();
}

function removeNotesFromOfflineStorage(id) {
    let offline = JSON.parse(localStorage.getItem('offline_notes') || "[]");
    offline = offline.filter(i => i.id !== id);
    localStorage.setItem('offline_notes', JSON.stringify(offline));
}

window.addEventListener('load', async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/notes/');
        const serverData = await response.json();
        
        const results = serverData.results || serverData;

        if (results.length === 0 && notes_list.length > 0) {
            localStorage.setItem('offline_notes', JSON.stringify(notes_list));
        }
        await syncOfflineNotes(); // Fix: name must match your function
    } catch (e) {
        await syncOfflineNotes();
    }
});

window.addEventListener('online', syncOfflineNotes);


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
        const response = await fetch(`http://127.0.0.1:8000/api/notes/delete/${id}/`, {
            method: 'DELETE'
        });

        if (response.ok) {
            notes_list = notes_list.filter(item => item.id !== id);
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
    const entry = notes_list.find(item => item.id === id);
    
    // swapping the H2 for an input so the user can change the name
    const container = document.getElementById('name-container');
    container.innerHTML = `<input type="text" id="input-notes-name" value="${entry.headline}" class="main-title-input">`;

    const editBtn = document.getElementById('edit-button');
    editBtn.innerText = "Save Changes";   // changing the Edit button into a "Confirm" button
    editBtn.onclick = () => saveUpdate(id); // updating the click event to trigger the save
}


async function saveUpdate(id) {
    const headline = document.getElementById('input-notes-name').value;
    const bodytext = document.getElementById('display-notes-bodytext').value;
    const logo = document.getElementById('display-notes-logo').src;

    if(!headline) {
        alert("Headline is required!");
        return;
    }

    if(!bodytext) {
        alert("Bodytext is required!");
        return;
    }

    const updatedData = {
        headline: document.getElementById('input-notes-name').value,
        bodytext: document.getElementById('display-notes-bodytext').value,
        logo: document.getElementById('display-notes-logo').src
    };

    if (!navigator.onLine) {
        handleOfflineUpdate(id, updatedData);
        return;
    }

    try {
        // sending the update to the Django Backend
        const response = await fetch(`http://127.0.0.1:8000/api/notes/update/${id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedData)
        });

        if (response.ok) {
            const result = await response.json();
            
            const index = notes_list.findIndex(item => item.id === id);
            if (index !== -1) {
                notes_list[index] = result;
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
        notes_list.push({
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
    const found = notes_list.find(c => c.website_name === "Test Site 1");
    console.log(found ? "Test: Search logic working." : "Test: Search logic failed.");



    // test 3: deleting an item
    const initialCount = notes_list.length;
    const idToDelete = notes_list[0].id; // grabbing the first one
    deleteItem(idToDelete); 

    if (notes_list.length === initialCount - 1) {
        console.log("Test: Delete logic passed. Item removed from RAM.");
    } 
    else {
        console.log("Test: Delete logic failed.");
    }



    // test 4: updating an item
    const testId = notes_list[0].id;
    notes_list[0].website_name = "UPDATED_NAME";
    renderList();

    const check = notes_list.find(c => c.id === testId);
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
    const lastVisitedNote = getCookie("last-viewed-notes");

    if (lastVisitedNote) {
        // finding the ID of the credential that matches the name in the cookie
        const lastEntry = notes_list.find(item => item.headline === lastVisitedNote);

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
