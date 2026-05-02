document.addEventListener('DOMContentLoaded', () => {
    document.body.style.opacity = '1';

    const navLinks = document.querySelectorAll('a');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const destination = this.href;
            if (destination && destination.includes(window.location.origin)) {
                e.preventDefault(); 
                document.body.style.opacity = '0'; 
                setTimeout(() => {
                    window.location.href = destination;
                }, 500);
            }
        });
    });
});




const roomName = "general";  // matches the room_name in routing.py
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
);


chatSocket.onmessage = function(e) {  // handling what happens when a message is received (whenever Redis broadcasts a message, this function wakes up)
    const data = JSON.parse(e.data);  // turning the data that came as string from Python into a JavaScript object, so we can access data.message, data.username
    const chatLog = document.querySelector('#chat-log');  // this is the HTML element where all the messages appear
    const messageElement = document.createElement('div');  // creating a new div for the new messages received from Python

    const currentUser = document.getElementById('user-data').textContent; // this looks for the HTML element user-data, that holds the name of the person currently logged in
    const isMe = data.username.toLowerCase() === currentUser.toLowerCase();  // we compare the username of the logged in person to the username of the one who sent the message
                                                                             // to see if the new message that needs to be displayed is my message, or someone else's

    messageElement.classList.add('message');  // adding the 'message' class to the CSS list of the new message (div)
    messageElement.classList.add(isMe ? 'outgoing' : 'incoming');  // if isMe is true, '.outgoing'is added (so the message has green background), if its not me, the the background of the message is white
    messageElement.innerHTML = `<strong>${data.username}</strong> ${data.message}`;  // adding the username with bold and the message to the new div element
    chatLog.appendChild(messageElement);  // actually displaying the new message
    chatLog.scrollTop = chatLog.scrollHeight;  // adding the newest messages at the bottom of the page
};


document.querySelector('#chat-message-submit').onclick = function(e) {  // handling what happens when the Send button gets clicked (taking the message and sending it)
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;

    if(message.trim() !== "") {
        chatSocket.send(JSON.stringify({  // sending the message from the user in JSON format through the WebSocket to the server
            'message': message
        }));
        messageInputDom.value = ''; // clearing the input
    }
}

document.querySelector('#chat-message-input').onkeyup = function(e) {  // sending the message when pressing Enter (instead of having to Send button)
    if (e.keyCode === 13) {  // 13 is the number for Enter, so when Enter gets pressed the message is sent, not if we click another random element from the keyboard
        document.querySelector('#chat-message-submit').click();
    }
}

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};