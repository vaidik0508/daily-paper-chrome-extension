document.addEventListener('DOMContentLoaded', function() {
    const params = new URLSearchParams(window.location.search);
    const paperId = params.get('id');
    const day = params.get('day');

    console.log('URL parameters:', {day, paperId}); // Debug log

    function fetchPaperDetails(day, paperId) {
        document.getElementById('explanation').innerHTML = '<p>Loading...</p>';

        console.log('Attempting to fetch details for day:', day, 'and paperId:', paperId); // Debug log

        if (!day || !paperId) {
            const errorMessage = `Missing parameters: day=${day}, id=${paperId}`;
            console.error(errorMessage); // Debug log
            document.getElementById('title').textContent = 'Error';
            document.getElementById('explanation').innerHTML = `<p>${errorMessage}</p>`;
            return;
        }

        fetch(`http://localhost:5000/api/paper/${day}/${paperId}`)
            .then(response => {
                console.log('API response status:', response.status); // Debug log
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(paper => {
                console.log('Fetched paper details:', paper); // Debug log
                document.getElementById('title').textContent = paper.title;

                if (Array.isArray(paper.authors)) {
                    document.getElementById('authors-list').textContent = paper.authors.join(', ');
                } else {
                    document.getElementById('authors-list').textContent = 'Not available';
                }

                const explanationMarkdown = paper.explanation;
                const explanationHtml = marked(explanationMarkdown);
                document.getElementById('explanation').innerHTML = explanationHtml;
            })
            .catch(error => {
                console.error('Error fetching paper details:', error); // Debug log
                document.getElementById('title').textContent = 'Error';
                document.getElementById('explanation').innerHTML = `<p>Failed to fetch paper details: ${error.message}</p>`;
            });
    }

    if (day && paperId) {
        fetchPaperDetails(day, paperId);
    } else {
        const errorMessage = `Missing required parameters: day=${day}, id=${paperId}`;
        console.error(errorMessage); // Debug log
        document.getElementById('title').textContent = 'Error';
        document.getElementById('explanation').innerHTML = `<p>${errorMessage}</p>`;
    }
});