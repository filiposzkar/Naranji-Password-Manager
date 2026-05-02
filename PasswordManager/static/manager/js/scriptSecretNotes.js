let notes_list = [];

async function fetchNotes() {
    try {
        const response = await fetch('/api/notes/', {
            method: 'GET',
            credentials: 'include' // important to show only this user's data
        });
        if (response.ok) {
            const data = await response.json();
            notes_list = data.results || data
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
                <img src="/static/manager/assets/Note.png" class="notes-icon">
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


function displayDetails(id) {
    const entry = notes_list.find(item => item.id === id);
    if(entry){
        setCookie("last-viewed-notes", entry.headline, 7);  // setting the name, value, and the expiration date of the cookie
        console.log("Cookie updated: User is interested in " + entry.headline);
        
        document.getElementById('name-container').innerHTML = `<h2 id="display-notes-name">${entry.headline}</h2>`;
        document.getElementById('display-notes-logo').src = "/static/manager/assets/Note.png";
        document.getElementById('display-notes-bodytext').value = entry.bodytext;
        
        // document.getElementById('edit-button').onclick = () => startEditing(id);
        // document.getElementById('delete-button').onclick = () => deleteItem(id);
        
        // document.getElementById('save-button').style.display = "none";
        // document.getElementById('edit-button').innerText = "Edit";

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
}


// prepare form for new item
function showAddForm() {
    // swapping H2 for an input field
    const container = document.getElementById('name-container');
    container.innerHTML = '<input type="text" id="input-notes-name" placeholder="Notes Name" class="main-title-input">';

    // clearing everything
    document.getElementById('display-notes-logo').src = "/static/manager/assets/Note.png";
    document.getElementById('display-notes-bodytext').value = "";

    // toggling buttons
    document.getElementById('save-button').style.display = "block";
}



async function saveNewItem() {
    try {
        const headlineElement = document.getElementById('input-notes-name');
        const bodytextElement = document.getElementById('display-notes-bodytext');
        const logoElement = document.getElementById('display-notes-logo');
        const token = getCookie('csrftoken');
        console.log("My CSRF Token is:", token);
        
        const headline = headlineElement.value;
        const bodytext = bodytextElement.value;
        const currentLogo = logoElement ? logoElement.src : "NaranjiLogo.png";
        console.log("Data collected:", { headline, bodytext, currentLogo });

        // client-side validation
        if (!headline.trim() || !bodytext.trim()) {
            alert("Please fill in the title and content!");
            return; 
        }

        // preparing the data for the backend
        const noteData = {
            headline: headline,
            bodytext: bodytext,
            logo: currentLogo
        };

        const response = await fetch('/api/notes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(noteData),
            credentials: 'include'
        })

        // handling the Server Response
        if (response.ok) {
            const savedItem = await response.json(); 
            notes_list.unshift(savedItem); 
            renderList(); 
            displayDetails(savedItem.id); 
            alert("Saved to database!");
        } else {
            const errorData = await response.json();
            console.error("Server rejected the request:", errorData);
            alert("Server Error: " + (errorData.error || "Unknown error"));
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
        const response = await fetch(`/api/notes/${id}/`, {
            method: 'DELETE',
        });

        if (response.ok) {
            notes_list = notes_list.filter(item => item.id !== id);
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

    try {
        // sending the update to the Django Backend
        const response = await fetch(`/api/notes/${id}/`, { 
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
            alert("Changes saved to the database!");
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

// function getCookie(name) {
//     let nameEQ = name + "=";
//     let ca = document.cookie.split(';');  // this split the long string, to get each component separately (name, value, days)
//     for(let i=0; i < ca.length; i++) {
//         let c = ca[i];
//         while (c.charAt(0) == ' ') c = c.substring(1, c.length);  // trim any white space put by the browser at the beginning of a cookie
//         if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);   // indexOf() looks for a substring in a string, and because we want the name of the cookie to match the "name" parameter
//         // we need to make sure that the substring "name" is starting on the first position of the cookies name, meaning that they are equal
//         // we then extract the value of the cookie and return it
//     }
//     return null;
// }


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
