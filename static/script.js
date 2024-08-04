document.addEventListener('DOMContentLoaded', function() {
    function updateAlbumInfo(id, type) {
        fetch(`/get_album_info?playlist_id=${id}&type=${type}`)
            .then(response => response.json())
            .then(data => {
                const albumInfoDiv = document.getElementById('info-display');
                
                if (data.error) {
                    albumInfoDiv.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }
                
                const iframe = document.createElement('iframe');
                iframe.src = `https://open.spotify.com/embed/${type}/${id}`;
                iframe.width = '300';
                iframe.height = '1000';
                iframe.frameBorder = '0';
                iframe.allowTransparency = 'true';
                iframe.allow = 'encrypted-media';

                albumInfoDiv.innerHTML = '';
                albumInfoDiv.appendChild(iframe);
            })
            .catch(error => {
                console.error('Error fetching album info:', error);
                const albumInfoDiv = document.getElementById('info-display');
                albumInfoDiv.innerHTML = '<p>Failed to load album information.</p>';
            });
    }

    document.querySelectorAll('.iframe-container button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const container = this.closest('.iframe-container');
            const id = container.getAttribute('data-id');
            const type = container.getAttribute('data-type');
            updateAlbumInfo(id, type);
        });
    });
});
