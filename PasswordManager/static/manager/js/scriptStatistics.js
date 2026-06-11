async function renderAllCharts() {
    const apiToken = sessionStorage.getItem('scoped_api_token');
    const masterKey = sessionStorage.getItem('master_key');

    try {
        const response = await fetch('/api/statistics/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Scoped-Token': apiToken,
                'X-Master-Key': masterKey
            }
        });
        const stats = await response.json();

        const vaultCanvas = document.getElementById('vaultChart');
        if (vaultCanvas) {
            const ctx1 = vaultCanvas.getContext('2d');
            new Chart(ctx1, {
                type: 'pie', 
                data: {
                    labels: stats.vault_stats.labels,
                    datasets: [{
                        label: 'Vault Distribution',
                        data: stats.vault_stats.values,
                        backgroundColor: ['#4CAF50', '#FFC107'],
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: { display: true, text: 'Credentials and Notes counter' }
                    }
                }
            });
        }

        const securityCanvas = document.getElementById('securityChart');
        if (securityCanvas) {
            const ctx2 = securityCanvas.getContext('2d');
            new Chart(ctx2, {
                type: 'pie', 
                data: {
                    labels: stats.security_stats.labels,
                    datasets: [{
                        label: 'Password Health',
                        data: stats.security_stats.values,
                        backgroundColor: ['#4CAF50', '#FFC107'], 
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: { display: true, text: 'Password Reuse Check' }
                    }
                }
            });
        }

        const strengthCanvas = document.getElementById('strengthChart');
        if(strengthCanvas) {
            const ctx3 = strengthCanvas.getContext('2d');
            new Chart(ctx3, {
                type: 'pie',
                data: {
                    labels: stats.strength_stats.labels, 
                    datasets: [{
                        label: 'Password Strength',
                        data: stats.strength_stats.values,  
                        backgroundColor: ['#4CAF50', '#FFC107'], 
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: { display: true, text: 'Password Strength Evaluation' }
                    }
                }
            });
        }


    } catch (err) {
        console.error("Failed loading statistical reporting dashboards:", err);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    renderAllCharts();
});


document.addEventListener('DOMContentLoaded', () => {
    document.body.style.opacity = '1';
    document.body.style.transition = 'opacity 0.5s ease';

    const links = document.querySelectorAll('a');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.hostname === window.location.hostname && this.getAttribute('href').includes('/')) {
                e.preventDefault();
                const target = this.href;
                document.body.style.opacity = '0';
                setTimeout(() => {
                    window.location.href = target;
                }, 500);
            }
        });
    });
});





// async function renderSecurityChart() {
//     const apiToken = sessionStorage.getItem('scoped_api_token');

//     const response = await fetch('/api/security-stats/', {
//         method: 'GET',
//         headers: {
//             'Content-Type': 'application/json',
//             'X-Scoped-Token': apiToken // Prove admin_access scheme authorization!
//         }
//     });
//     const stats = await response.json();

//     const ctx = document.getElementById('securityChart').getContext('2d');
//     new Chart(ctx, {
//         type: 'pie',
//         data: {
//             labels: stats.labels,
//             datasets: [{
//                 label: 'System Health',
//                 data: stats.values,
//                 // Using the specific colors we defined in the Django view
//                 backgroundColor: stats.colors || ['#a4c639', '#d9534f'], 
//                 borderWidth: 1
//             }]
//         },
//         options: {
//             responsive: true,
//             plugins: {
//                 legend: { position: 'bottom' },
//                 title: {
//                     display: true,
//                     text: 'Security Observation Overview'
//                 }
//             }
//         }
//     });
// }

