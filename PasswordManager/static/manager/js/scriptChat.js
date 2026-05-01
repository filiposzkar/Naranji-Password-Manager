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

chatSocket.onmessage = function(e) {  // handling what happens when a message is received
    const data = JSON.parse(e.data);
    const chatLog = document.querySelector('#chat-log');
    const messageElement = document.createElement('div');  // creating a new message div

    const currentUser = document.getElementById('user-data').textContent;
    const isMe = data.username === currentUser;

    messageElement.classList.add('message');
    messageElement.classList.add(isMe ? 'outgoing' : 'incoming');
    messageElement.innerHTML = `<strong>${data.username}</strong> ${data.message}`;

    chatLog.appendChild(messageElement);

    chatLog.scrollTop = chatLog.scrollHeight;
};


document.querySelector('#chat-message-submit').onclick = function(e) {  // handling what happens when the Send button gets clicked
    const messageInputDom = document.querySelector('#chat-message-submit');
    const message = messageInputDom.value;

    if(message.trim() !== "") {
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.value = ''; // clearing the input
    }
}


document.querySelector('#chat-message-input').onkeyup = function(e) {  // sending the message when pressing Enter
    if (e.keyCode === 13) {
        document.querySelector('#chat-message-submit').click();
    }
}