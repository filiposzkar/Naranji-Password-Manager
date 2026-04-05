let notes_list = [
    {id: 1, logo: "NotesIcon.png", headline: "Project Ideas", bodytext: "Lorem ipsum"},
    {id: 2, logo: "NotesIcon.png", headline: "Lecture notes", bodytext: "Lorem ipsum 2"},
];


let currentPage = 1;
const itemsPerPage = 3;


function renderList() {
    const container = document.getElementById('notes_list');
    container.innerHTML = '';

    // calculating which items to show
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = notes_list.slice(startIndex, endIndex);

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
    document.getElementById('display-notes-logo').src = "NotesIcon.png";
    document.getElementById('display-notes-bodytext').value = "";

    // toggling buttons
    document.getElementById('save-button').style.display = "block";
}


// saving to RAM and update sidebar
function saveNewItem() {
    
    const headline = document.getElementById('input-notes-name').value;
    const bodytext = document.getElementById('display-notes-bodytext').value;
    const currentLogo = document.getElementById('display-notes-logo').src;
    

    if (!headline || !bodytext || !currentLogo) {
        alert("Please fill in all parameters!");
        return;
    }

    const newEntry = {
        id: Date.now(), 
        logo: currentLogo,
        headline: headline,
        bodytext: bodytext        
    };

    notes_list.unshift(newEntry); // adding to start of array
    renderList(); // refreshing sidebar
    displayDetails(newEntry.id); // showing the new item details and hide save button
}


// Attach the save function to the button click properly
document.addEventListener('DOMContentLoaded', () => {
    renderList();
    document.getElementById('save-button').onclick = saveNewItem;
});



function deleteItem(id) {
    if (!confirm("Are you sure you want to delete this credential?")) return;

    notes_list = notes_list.filter(item => item.id !== id);  // finding the credential to delete in the list of credentials
    renderList();  // update the sidebar

    document.getElementById('name-container').innerHTML = `<h2 id="display-notes-name">Select an item</h2>`;
    document.getElementById('display-notes-logo').src = "NotesIcon.png";
    document.getElementById('display-notes-bodytext').value = "";
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



function saveUpdate(id) {
    // finding the index of the item to be updated in the list of items
    const index = notes_list.findIndex(item => item.id === id);

    if (index !== -1) {
        // grabbing the new values from the UI
        notes_list[index].headline = document.getElementById('input-notes-name').value;
        notes_list[index].bodytext = document.getElementById('display-notes-bodytext').value;
        notes_list[index].logo = document.getElementById('display-notes-logo').src;

        // refreshing the sidebar and the detailed view
        renderList();
        displayDetails(id);
        
        alert("Changes saved to RAM!");
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
