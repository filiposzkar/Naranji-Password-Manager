async function renderVaultChart() {
    const response = await fetch('/api/statistics/');
    const stats = await response.json();

    const ctx = document.getElementById('vaultChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie', 
        data: {
            labels: stats.labels,
            datasets: [{
                label: 'Vault Distribution',
                data: stats.values,
                backgroundColor: ['#4CAF50', '#FFC107'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}


renderVaultChart();


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