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