document.addEventListener('DOMContentLoaded', async () => {
    const paperList = document.getElementById('paperList');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');

    try {
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        paperList.style.display = 'none';

        const response = await fetch('http://localhost:5000/api/papers');
        if (!response.ok) {
            throw new Error('Failed to fetch papers');
        }

        const papers = await response.json();
        paperList.innerHTML = '';

        if (papers.length === 0) {
            errorElement.textContent = 'No papers available for today';
            errorElement.style.display = 'block';
            return;
        }

        papers.forEach(paper => {
            const paperElement = document.createElement('div');
            paperElement.className = 'paper-item';
            
            paperElement.innerHTML = `
                <h3 class="paper-title">${paper.title}</h3>
                <p class="paper-authors">By: ${paper.by.join(', ')}</p>
                <p class="paper-topics">Topics: ${paper.key_topics}</p>
                <button class="details-btn" data-day="${paper.day}" data-id="${paper.id}">View Details</button>
            `;
            
            paperList.appendChild(paperElement);
        });

        // Add click handlers for detail buttons
        document.querySelectorAll('.details-btn').forEach(button => {
            button.addEventListener('click', async (e) => {
                const day = e.target.dataset.day;
                const id = e.target.dataset.id;
                chrome.tabs.create({
                    url: `details.html?day=${day}&id=${id}`
                });
            });
        });

        loadingElement.style.display = 'none';
        paperList.style.display = 'block';

    } catch (error) {
        console.error('Error:', error);
        errorElement.textContent = 'Failed to load papers. Please try again later.';
        loadingElement.style.display = 'none';
        errorElement.style.display = 'block';
    }
});